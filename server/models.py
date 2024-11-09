from pydantic import BaseModel
from typing import List


class Chat(BaseModel):
    sender: str
    message: str


class ChatAnalysisRequest(BaseModel):
    username: str
    chats: List[Chat]


class SentimentResponse(BaseModel):
    sentiment: str
    alert_needed: bool
    explanation: str
