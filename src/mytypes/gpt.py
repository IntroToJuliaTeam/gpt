from dataclasses import dataclass


@dataclass
class YandexGPTConfig:
    """Configuration for Yandex GPT authentication"""

    service_account_id: str
    key_id: str
    private_key: str
    folder_id: str


@dataclass
class Message:
    """Сообщение в истории диалога"""

    role: str  # "user" или "assistant"
    text: str

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)
