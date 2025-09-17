# app.py — FastAPI that wraps the shared core logic
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from core import answer_question, load_notes_and_build_index

app = FastAPI(title="One Piece Bot API")

class ChatRequest(BaseModel):
    message: str
    k: int = 3

class ChatResponse(BaseModel):
    reply: str
    passages: List[Dict]

@app.on_event("startup")
def _startup():
    load_notes_and_build_index()

@app.get("/")
def read_root():
    return {"message": "API is running. Use POST /chat."}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    res = answer_question(req.message, k=req.k)
    return ChatResponse(**res)


