from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class TBaseVectorStore(ABC):
    @abstractmethod
    def persist(self):
        pass

    @abstractmethod
    def build(self, docs: List[Tuple[str, Dict]]):
        pass

    @abstractmethod
    def query(self, q: str, top_k=5) -> List[Dict]:
        pass


class TBaseYandexGPTBot(ABC):
    @abstractmethod
    def get_user_history(self, user_id: int) -> List:
        pass

    @abstractmethod
    def add_to_history(self, user_id: int, role: str, text: str) -> None:
        pass

    @abstractmethod
    def clear_history(self, user_id: int) -> None:
        pass

    @abstractmethod
    def get_iam_token(self) -> str:
        pass

    @abstractmethod
    def unsafe_ask_gpt(self, question: str, user_id: int = None) -> str:
        pass


class TYandexGPTBot(TBaseYandexGPTBot):
    @abstractmethod
    def ask_gpt(self, question: str, user_id: int) -> str:
        pass


class TPromptValidatorBot(TBaseYandexGPTBot):
    @abstractmethod
    def check_prompt(self, prompt: str) -> bool:
        pass


class TAnswerValidatorBot(TBaseYandexGPTBot):
    @abstractmethod
    def check_answer(self, answer: str) -> bool:
        pass


class TBaseRagClient(ABC):
    @staticmethod
    @abstractmethod
    def rag_answer(
        vector_store: TBaseVectorStore,
        yandex_bot: TYandexGPTBot,
        query: str,
        user_id: int,
    ):
        pass
