# core.py — strict grounded answering (no generation)

from typing import List, Dict
import time, threading, sqlite3
import numpy as np
import httpx
import re

# ---- retrieval: embeddings ----
from fastembed import TextEmbedding
from sklearn.metrics.pairwise import cosine_similarity

# ---- extractive QA (on GPU if available) ----
import torch
from transformers import pipeline

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.1:8b"  # or "qwen2.5:7b-instruct"
# --- helper ---
def llm_chat(messages, temperature: float = 0.6, max_tokens: int = 300) -> str:
    """
    messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
    returns assistant text
    """
    try:
        with httpx.stream(
            "POST",
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": True, "options": {"temperature": temperature}},
            timeout=60,
        ) as r:
            r.raise_for_status()
            chunks = []
            for line in r.iter_lines():
                if not line:
                    continue
                data = httpx.Response.json(httpx.Response(200, content=line))
                # each event has data like {"message":{"role":"assistant","content":"..."},"done":false}
                msg = data.get("message", {}).get("content", "")
                chunks.append(msg)
                if data.get("done"):
                    break
            return "".join(chunks).strip() or "(no reply)"
    except Exception as e:
        return f"(LLM error: {e})"
# --- small talk detection ---
GREET_RE = re.compile(r"^\s*(hi|hello|hey|yo|good\s*(morning|evening|afternoon)|sup)\b", re.I)
THANKS_RE = re.compile(r"\b(thanks|thank you|ty)\b", re.I)

def is_small_talk(q: str) -> bool:
    return bool(GREET_RE.search(q) or THANKS_RE.search(q) or q.strip().lower() in {"how are you?", "who are you?", "what can you do?"})
# --- chat router ---
def chat_router(user_text: str, k: int = 3) -> Dict:
    """
    Route:
      - small talk -> local LLM
      - One Piece Q&A -> strict RAG
      - if retrieval looks weak -> fall back to LLM
    """
    # 1) Small talk
    if is_small_talk(user_text):
        system = {"role":"system","content":"You are a friendly assistant for a One Piece app. Keep replies short and warm."}
        user = {"role":"user","content":user_text}
        reply = llm_chat([system, user])
        return {"reply": reply, "passages": []}

    # 2) Try strict RAG
    hits = search_topk(user_text, k=k)
    if hits:
        # Use your existing strict function to get a grounded answer
        res = answer_question(user_text, k=k)
        # Heuristic: if similarity too low, answer may be off-topic; use LLM instead.
        top_score = hits[0].get("score", 0.0)
        if top_score < 0.25:  # tune threshold as your data grows
            system = {"role":"system","content":"You are a friendly assistant. If the user asks general things, reply helpfully. If they ask about One Piece, answer briefly and clearly."}
            user = {"role":"user","content": user_text}
            reply = llm_chat([system, user])
            return {"reply": reply, "passages": []}
        return res

    # 3) Fallback -> LLM
    system = {"role":"system","content":"You are a friendly assistant. Keep replies concise."}
    user = {"role":"user","content": user_text}
    reply = llm_chat([system, user])
    return {"reply": reply, "passages": []}

DEVICE = 0 if torch.cuda.is_available() else -1
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("CUDA device:", torch.cuda.get_device_name(0))
    torch.set_float32_matmul_precision("high")

qa_pipeline = pipeline(
    "question-answering",
    model="deepset/roberta-base-squad2",
    device=DEVICE,
    torch_dtype=torch.float16 if DEVICE == 0 else None,
)

# ---------- globals ----------
_notes: List[Dict] = []
_emb_model: TextEmbedding | None = None
_emb_matrix: np.ndarray | None = None
_lock = threading.Lock()
_last_reload = 0.0
_reload_interval = 10  # seconds

# ---------- data / index ----------
def load_notes_and_build_index():
    global _notes, _emb_model, _emb_matrix
    conn = sqlite3.connect("onepiece.db")
    c = conn.cursor()
    c.execute("""
      CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        title TEXT,
        arc TEXT,
        text TEXT
      )
    """)
    rows = c.execute("SELECT id, title, arc, text FROM notes").fetchall()
    conn.close()

    notes = [{"id": r[0], "title": r[1], "arc": r[2], "text": r[3]} for r in rows]
    docs = [f"{n['title']} — {n['text']}" for n in notes]

    if _emb_model is None:
        _emb_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    vecs = list(_emb_model.embed(docs))
    emb_matrix = np.array(vecs, dtype="float32")

    with _lock:
        _notes = notes
        _emb_matrix = emb_matrix

def _maybe_reload():
    global _last_reload
    now = time.time()
    if (_emb_matrix is None) or (now - _last_reload > _reload_interval):
        load_notes_and_build_index()
        _last_reload = now

def search_topk(query: str, k: int = 3) -> List[Dict]:
    _maybe_reload()
    if not _notes or _emb_matrix is None:
        return []
    q_vec = np.array(list(_emb_model.embed([query]))[0], dtype="float32").reshape(1, -1)
    sims = cosine_similarity(q_vec, _emb_matrix).ravel()
    top_idx = sims.argsort()[::-1][:k]
    results = []
    for idx in top_idx:
        item = dict(_notes[idx])
        item["score"] = float(sims[idx])
        results.append(item)
    return results

def filter_hits_by_relevance(question: str, hits: List[Dict]) -> List[Dict]:
    """Keep passages with similarity > tiny floor; arc keyword in question boosts keep."""
    q = question.lower()
    allowed_arcs = { (h.get("arc") or "").lower() for h in hits if (h.get("arc") or "").lower() in q }
    filtered = []
    for h in hits:
        score_ok = h.get("score", 0.0) > 0.05   # slightly higher floor for cleaner sets
        arc_ok = ((h.get("arc") or "").lower() in allowed_arcs) if allowed_arcs else False
        if score_ok or arc_ok:
            filtered.append(h)
    if not filtered and hits:
        filtered = [hits[0]]
    return filtered

# ---------- strict, grounded answerer ----------
def answer_question(question: str, k: int = 3) -> Dict:
    """
    Retrieval -> filter -> extractive QA per passage.
    Accept an answer only if:
      - confidence >= CONF_THRESH, and
      - the answer is found verbatim in the passage text.
    Else, fall back to the top passage text (still grounded).
    """
    raw_hits = search_topk(question, k=k)
    hits = filter_hits_by_relevance(question, raw_hits)

    if not hits:
        return {"reply": "Sorry, I don't know yet.", "passages": []}

    best = None  # (answer, score, idx)
    for i, h in enumerate(hits):
        ctx = h.get("text", "")
        if not ctx:
            continue
        try:
            res = qa_pipeline(question=question, context=ctx)
            ans = (res.get("answer") or "").strip()
            sc  = float(res.get("score") or 0.0)
            # guardrails: non-trivial, not yes/no, and must appear in ctx
            if ans and len(ans) > 3 and ans.lower() not in {"yes","no","unknown"} and ans in ctx:
                if (best is None) or (sc > best[1]):
                    best = (ans, sc, i)
        except Exception:
            continue

    CONF_THRESH = 0.55  # tune 0.45–0.65
    if best and best[1] >= CONF_THRESH:
        i = best[2]
        src = f"{hits[i]['title']} ({hits[i]['arc']})"
        reply = f"Q: {question}\n\nA: {best[0]}\n\nSources: {src}"
        return {"reply": reply, "passages": [hits[i]]}

    # Fallback: grounded, verbatim top passage
    top = hits[0]
    reply = f"Q: {question}\n\nA: {top['text']}\n\nSources: {top['title']} ({top['arc']})"
    return {"reply": reply, "passages": [top]}
