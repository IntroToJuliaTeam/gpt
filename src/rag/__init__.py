from src.types.abc import TBaseRagClient, TBaseVectorStore
from .rag import rag_answer as rag_answer_base, VectorStore


class RagClient(TBaseRagClient):
    @staticmethod
    def rag_answer(vector_store: TBaseVectorStore, yandex_bot, query: str, user_id: int) -> str:
        return rag_answer_base(vector_store, yandex_bot, query, user_id)