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
