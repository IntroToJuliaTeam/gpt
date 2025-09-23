from typing import Optional

try:
    from src.mytypes.abc import TBaseRagClient, TBaseVectorStore, TYandexGPTBot
except ImportError:
    from src.gpt.src.mytypes.abc import TBaseRagClient, TBaseVectorStore, TYandexGPTBot

from .rag import VectorStore
from .rag import rag_answer as rag_answer_base


class RagClient(TBaseRagClient):
    @staticmethod
    def rag_answer(
        vector_store: TBaseVectorStore,
        yandex_bot: TYandexGPTBot,
        query: str,
        user_id: Optional[int] = None,
    ) -> str:
        return rag_answer_base(vector_store, yandex_bot, query, user_id)
