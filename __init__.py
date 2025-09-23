try:
    # Абсолютные импорты
    from src.gpt.yandex_gpt import YandexGPTBot
    from src.mytypes.gpt import YandexGPTConfig
    from src.rag import RagClient
    from src.rag.rag import prepare_index
except ImportError:
    # Относительные импорты (если запускаем из пакета)
    from src.gpt.src.gpt.yandex_gpt import YandexGPTBot
    from src.gpt.src.mytypes.gpt import YandexGPTConfig
    from src.gpt.src.rag import RagClient
    from src.gpt.src.rag.rag import prepare_index
