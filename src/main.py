import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends

from src.gpt.yandex_gpt import YandexGPTBot
from src.models import HistoryItem, QuestionRequest
from src.rag import RagClient
from src.types.gpt import YandexGPTConfig

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Mediator API", version="1.0.0")

SERVICE_ACCOUNT_ID = os.environ["ACCOUNT_ID"]
KEY_ID = os.environ["KEY_ID"]
PRIVATE_KEY = os.environ["PRIVATE_KEY"].replace("\\n", "\n")
FOLDER_ID = os.environ["FOLDER_ID"]
TELEGRAM_TOKEN = os.environ["BOT_TOKEN"]

gpt_bot = YandexGPTBot(
            YandexGPTConfig(SERVICE_ACCOUNT_ID, KEY_ID, PRIVATE_KEY, FOLDER_ID)
        )
rag_client = RagClient()

# Endpoints для работы с историей
@app.get("/history/{user_id}", response_model=List)
async def get_user_history(
        user_id: int,
):
    """Получить историю пользователя"""
    try:
        history = gpt_bot.get_user_history(user_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/history/{user_id}")
async def add_to_history(
        user_id: int,
        item: HistoryItem,
):
    """Добавить сообщение в историю пользователя"""
    try:
        gpt_bot.add_to_history(user_id, item.role, item.text)
        return {"status": "success", "message": "Added to history"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/{user_id}")
async def clear_history(
        user_id: int,
):
    """Очистить историю пользователя"""
    try:
        gpt_bot.clear_history(user_id)
        return {"status": "success", "message": "History cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gpt/{user_id}")
async def ask_gpt(
        user_id: int,
        request: QuestionRequest,
):
    """Задать вопрос GPT с учетом истории"""
    try:
        answer = gpt_bot.ask_gpt(request.question, user_id)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/{user_id}")
async def rag_answer(
        user_id: int,
        request: QuestionRequest,
):
    """Получить ответ через RAG"""
    try:
        answer = rag_client.rag_answer(gpt_bot, request.question, user_id)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
