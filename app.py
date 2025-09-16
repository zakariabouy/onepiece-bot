from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import json, os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel   # fast cosine
import threading

app = FastAPI(title="One Piece Bot (Step 4: tiny retrieval)")

# ====== Data models ======
class ChatRequest(BaseModel):
    message: str
    k: int = 3  # how many passages to return (default 3)

class ChatResponse(BaseModel):
    reply: str
    passages: List[Dict]

# ====== Global (simple) state ======
DATA_PATH = os.path.join("data", "notes.jsonl")
_notes: List[Dict] = []
_vectorizer: TfidfVectorizer = None
_matrix = None
_lock = threading.Lock()  # avoid race conditions on first load

def load_notes_and_build_index():
    global _notes, _vectorizer, _matrix
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Missing data file: {DATA_PATH}")

    notes = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            notes.append(json.loads(line))

    # Build TF-IDF on title+text for better recall
    docs = [(n.get("title","") + " — " + n.get("text","")).strip() for n in notes]
    vectorizer = TfidfVectorizer(min_df=1, ngram_range=(1,2), stop_words="english")
    matrix = vectorizer.fit_transform(docs)

    with _lock:
        _notes = notes
        _vectorizer = vectorizer
        _matrix = matrix

def search_topk(query: str, k: int = 3) -> List[Dict]:
    with _lock:
        if _matrix is None:
            load_notes_and_build_index()
        vec = _vectorizer.transform([query])
        sims = linear_kernel(vec, _matrix).ravel()  # cosine similarity
    # get top-k indices
    top_idx = sims.argsort()[::-1][:k]
    results = []
    for idx in top_idx:
        item = dict(_notes[idx])
        item["score"] = float(sims[idx])
        results.append(item)
    return results

# ====== Routes ======
@app.get("/")
def read_root():
    return {"message": "Tiny retrieval is ready. Use POST /chat."}

@app.on_event("startup")
def _startup():
    load_notes_and_build_index()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    hits = search_topk(req.message, k=req.k)

    # Build a simple grounded reply: stitch top passages as a paragraph + mini citations
    bullet_lines = []
    for h in hits:
        bullet_lines.append(f"- {h.get('title','(untitled)')} [{h.get('arc','?')}]: {h.get('text','')}")
    reply = (
        "Here’s what I found based on your question:\n\n" +
        "\n".join(bullet_lines) +
        "\n\n(Answer is grounded in the notes above. We’ll add a real LLM later.)"
    )

    return ChatResponse(reply=reply, passages=hits)
