import logging
import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from src.gpt.yandex_gpt import YandexGPTBot
from src.models import HistoryItem, QuestionRequest
from src.rag import RagClient
from src.rag.rag import prepare_index
from src.mytypes.gpt import YandexGPTConfig

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

URL = os.environ["URL"]
PORT = os.environ["PORT"]

s3_cfg = {
    "endpoint": os.environ["S3_ENDPOINT"],
    "access_key": os.environ["S3_ACCESS_KEY"],
    "secret_key": os.environ["S3_SECRET_KEY"],
    "bucket": os.environ["S3_BUCKET"],
    "prefix": os.environ.get("S3_PREFIX", ""),
}

gpt_bot = YandexGPTBot(
    YandexGPTConfig(SERVICE_ACCOUNT_ID, KEY_ID, PRIVATE_KEY, FOLDER_ID)
)
global_vector_store = prepare_index(s3_cfg)
rag_client = RagClient()


@app.get("/history/{user_id}", response_model=List)
async def get_user_history(
    user_id: int,
):
    """Получить историю пользователя"""
    try:
        history = gpt_bot.get_user_history(user_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/history/{user_id}")
async def clear_history(
    user_id: int,
):
    """Очистить историю пользователя"""
    try:
        gpt_bot.clear_history(user_id)
        return {"status": "success", "message": "History cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/rag")
async def rag_answer(
    request: QuestionRequest,
):
    """Получить ответ через RAG"""
    try:
        answer = rag_client.rag_answer(
            vector_store=global_vector_store,
            yandex_bot=gpt_bot,
            query=request.question,
            user_id=None,
        )
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=URL, port=int(PORT))
