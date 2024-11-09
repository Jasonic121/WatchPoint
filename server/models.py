from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class UserAccount(BaseModel):
    id: int
    name: str
    email: EmailStr
    password: str
    account_type: str = Field(..., pattern="^(parent|child)$")


class ParentAccount(UserAccount):
    account_type: str = "parent"
    children: List[int] = []


class ChildAccount(UserAccount):
    account_type: str = "child"
    parent_id: Optional[int] = None


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
