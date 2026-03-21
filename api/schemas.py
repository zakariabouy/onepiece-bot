from pydantic import BaseModel
from typing import List, Dict, Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    k: int = 5
    temperature: float = 0.5
    history: List[ChatMessage] = []


class TheoryRequest(BaseModel):
    theory: str
    evidence: str = ""
