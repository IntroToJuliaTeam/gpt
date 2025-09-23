try:
    # Абсолютные импорты
    from src.gpt.yandex_gpt import YandexGPTBot
    from src.rag import RagClient
    from src.rag.rag import prepare_index
    from src.types.gpt import YandexGPTConfig
except ImportError:
    # Относительные импорты (если запускаем из пакета)
    from src.gpt.src.gpt.yandex_gpt import YandexGPTBot
    from src.gpt.src.rag import RagClient
    from src.gpt.src.rag.rag import prepare_index
    from src.gpt.src.types.gpt import YandexGPTConfig
