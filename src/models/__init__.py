from typing import List, Dict

from pydantic import BaseModel


class HistoryItem(BaseModel):
    role: str
    text: str

class QuestionRequest(BaseModel):
    question: str

class HistoryResponse(BaseModel):
    history: List[Dict[str, str]]