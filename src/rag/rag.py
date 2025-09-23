import logging
import os
import pickle
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

import boto3
import faiss
import fitz
from sentence_transformers import SentenceTransformer

from src.types.abc import TBaseVectorStore

logger = logging.getLogger(__name__)


# файл делался Женей, ему не нравится использовать линтер,
# так что он выключен для этого файла в [конфиге](.pylintrc)
# все вопросы к Жене, все равно я этот файл трогать не буду)))


# -----------------------------
# 1. Скачать документы из S3
# -----------------------------
def download_from_s3(endpoint, access_key, secret_key, bucket, prefix="") -> List[str]:
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="ru-central1",
    )
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    except Exception as e:
        logger.error("Ошибка подключения к S3: %s", e)
        return []

    if "Contents" not in resp:
        return []

    local_files = []
    tmpdir = tempfile.mkdtemp(prefix="rag_s3_")
    for obj in resp["Contents"]:
        key = obj.get("Key")
        if not key or key.endswith("/"):
            continue
        size = obj.get("Size", 0)
        if size == 0:
            continue

        local_path = os.path.join(tmpdir, os.path.basename(key))
        try:
            s3.download_file(bucket, key, local_path)
            if os.path.getsize(local_path) > 0:
                local_files.append(local_path)
        except Exception as e:
            logger.error("Ошибка скачивания %s: %s", key, e)
            continue

    return local_files


# -----------------------------
# 2. Извлечь текст (PDF с сохранением структуры)
# -----------------------------
def extract_text(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    if p.suffix.lower() == ".pdf":
        text = []
        try:
            doc = fitz.open(path)
            for i, page in enumerate(doc, start=1):
                # blocks сохраняют более связный текст
                page_text = page.get_text("blocks")
                if not page_text:
                    page_text = page.get_text("text")
                # каждый блок — tuple (x0, y0, x1, y1, text, block_no, ...)
                if isinstance(page_text, list):
                    blocks_text = "\n".join(b[4] for b in page_text if len(b) > 4)
                else:
                    blocks_text = page_text
                text.append(f"[PAGE {i}]\n{blocks_text}")
        except Exception as e:
            logger.error("Ошибка PDF %s: %s", path, e)
        return "\n".join(text)
    return ""


# -----------------------------
# 3. Чанкование
# -----------------------------
def chunk_text(text: str, max_chars=1800, overlap=250) -> List[str]:
    chunks, i, n = [], 0, len(text)
    while i < n:
        j = min(i + max_chars, n)
        chunk = text[i:j]
        chunks.append(chunk)
        i = j - overlap if j < n else n
    return chunks


# -----------------------------
# 4. Vector Store (FAISS)
# -----------------------------
class VectorStore(TBaseVectorStore):
    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        index_path="faiss_index.bin",
        meta_path="faiss_meta.pkl",
    ):
        self.model = SentenceTransformer(model_name)
        self.index_path = index_path
        self.meta_path = meta_path
        self.index = None
        self.metadatas = []
        self._load()

    def _load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, "rb") as f:
                    self.metadatas = pickle.load(f)
            except Exception:
                self.index = None

    def persist(self):
        if self.index is None:
            return
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadatas, f)

    def build(self, docs: List[Tuple[str, Dict]]):
        texts = [t for t, _ in docs]
        vecs = self.model.encode(texts, convert_to_numpy=True)
        if self.index is None:
            self.index = faiss.IndexFlatL2(vecs.shape[1])
        self.index.add(vecs)
        self.metadatas.extend([m for _, m in docs])
        self.persist()

    def query(self, q: str, top_k=5) -> List[Dict]:
        if not self.index:
            return []
        qv = self.model.encode([q], convert_to_numpy=True)
        # ищем больше кандидатов, чтобы потом фильтровать
        D, I = self.index.search(  # pylint: disable=invalid-name,unused-variable
            qv, top_k * 3
        )
        results = []
        for i in I[0]:
            if i < len(self.metadatas):
                m = self.metadatas[i]
                if re.search(r"operator|infix", m["content"], re.IGNORECASE):
                    # приоритет для операторов
                    results.insert(0, m)
                else:
                    results.append(m)
        return results[:top_k]


# -----------------------------
# 5. Подготовить индекс
# -----------------------------
def prepare_index(s3_cfg: Dict) -> VectorStore:
    files = download_from_s3(**s3_cfg)
    docs = []
    for f in files:
        txt = extract_text(f)
        for c in chunk_text(txt):
            docs.append((c, {"source": os.path.basename(f), "content": c}))
    if not docs:
        docs = [
            (
                "Нет доступных документов.",
                {"source": "placeholder", "content": "Нет доступных документов."},
            )
        ]
    vs = VectorStore()
    vs.build(docs)
    return vs


# -----------------------------
# 6. Сборка контекста
# -----------------------------
def build_context(results: List[Dict]) -> str:
    parts = []
    for r in results:
        parts.append(f"Источник: {r.get('source')}\n{r.get('content')}\n---")
    return "\n".join(parts)


# -----------------------------
# 7. Основная функция RAG
# -----------------------------
def rag_answer(
    vector_store: TBaseVectorStore, yandex_bot, query: str, user_id: int
) -> str:
    results = vector_store.query(query, 5)
    context = build_context(results)
    # Тут с промптом можно поэкспериментировать
    final_prompt = (
        "[CONTEXT]\n"
        f"{context}\n"
        "[SYSTEM]\n"
        "Ты — ассистент. Используй контекст выше для ответа.\n"
        "[USER]\n"
        f"{query}\n"
    )
    return yandex_bot.ask_gpt(final_prompt, user_id)
