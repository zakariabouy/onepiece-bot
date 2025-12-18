# core.py — unified conversational RAG (semantic retrieval + local LLM via Ollama)
# - Retrieval: FastEmbed (BAAI/bge-small-en-v1.5)
# - Synthesis: local LLM (Ollama). Instructed to use ONLY provided sources and cite them.
# - Fallbacks for small talk / weak retrieval
# - Optional strict extractive QA helper (answer_question)

from typing import List, Dict
import os, re, time, threading, sqlite3, json
import numpy as np

# ---------- Retrieval: semantic embeddings ----------
from fastembed import TextEmbedding
from sklearn.metrics.pairwise import cosine_similarity

# ---------- Optional extractive QA (GPU if available) ----------
import torch
from transformers import pipeline

# ---------- Local LLM (Ollama) ----------
import httpx

# ====== Config ======
DB_PATH = os.getenv("ONEPIECE_DB", "onepiece.db")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
RELOAD_INTERVAL_SEC = 10

# Detect device for HF pipelines
DEVICE = 0 if torch.cuda.is_available() else -1
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    try:
        print("CUDA device:", torch.cuda.get_device_name(0))
    except Exception:
        pass
    torch.set_float32_matmul_precision("high")

# (Optional) Extractive QA head for strict answers
qa_pipeline = pipeline(
    "question-answering",
    model="deepset/roberta-base-squad2",
    device=DEVICE,
    torch_dtype=torch.float16 if DEVICE == 0 else None,
)

# ====== Globals for notes + index ======
_notes: List[Dict] = []
_emb_model: TextEmbedding | None = None
_emb_matrix: np.ndarray | None = None
_lock = threading.Lock()
_last_reload = 0.0

# ====== Data / Index ======
def load_notes_and_build_index():
    """Load notes from SQLite and build an embedding matrix."""
    global _notes, _emb_model, _emb_matrix

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id   TEXT PRIMARY KEY,
                title TEXT,
                arc   TEXT,
                text  TEXT
            )
        """)
        rows = c.execute("SELECT id, title, arc, text FROM notes").fetchall()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        rows = []

    notes = [{"id": r[0], "title": r[1], "arc": r[2], "text": r[3]} for r in rows]
    docs = [f"{n['title']} — {n['text']}" for n in notes]

    if _emb_model is None:
        _emb_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    vecs = list(_emb_model.embed(docs)) if docs else []
    emb_matrix = np.array(vecs, dtype="float32") if vecs else None

    with _lock:
        _notes = notes
        _emb_matrix = emb_matrix

def _maybe_reload():
    global _last_reload
    now = time.time()
    if (_emb_matrix is None) or (now - _last_reload > RELOAD_INTERVAL_SEC):
        load_notes_and_build_index()
        _last_reload = now

def _is_latest_query(query: str) -> bool:
    """Detect if user is asking about recent/latest events."""
    patterns = ['latest', 'recent', 'newest', 'last chapter', 'last event', 
                'current', 'now', 'happening now', 'most recent', 'currently']
    q_lower = query.lower()
    return any(p in q_lower for p in patterns)

def _get_latest_chapters(k: int = 5) -> List[Dict]:
    """Get the most recent chapters by chapter number."""
    _maybe_reload()
    chapter_notes = [n for n in _notes if n.get('id', '').startswith('chapter_')]
    # Sort by chapter number descending
    chapter_notes.sort(key=lambda x: int(x['id'].replace('chapter_', '') or 0), reverse=True)
    # Add score field to match semantic search results format
    results = []
    for note in chapter_notes[:k]:
        item = dict(note)
        item["score"] = 1.0  # High score for chronological matches
        results.append(item)
    return results

def search_topk(query: str, k: int = 5) -> List[Dict]:
    _maybe_reload()
    if not _notes or _emb_matrix is None:
        return []
    
    # Special handling for "latest/recent" queries
    if _is_latest_query(query):
        return _get_latest_chapters(k)
    
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
    """Keep passages with non-trivial similarity; boost if arc token appears in the question."""
    q = question.lower()
    allowed_arcs = {(h.get("arc") or "").lower() for h in hits if (h.get("arc") or "").lower() in q}
    filtered = []
    for h in hits:
        score_ok = h.get("score", 0.0) > 0.05
        arc_ok = ((h.get("arc") or "").lower() in allowed_arcs) if allowed_arcs else False
        if score_ok or arc_ok:
            filtered.append(h)
    if not filtered and hits:
        filtered = [hits[0]]
    return filtered

# ====== Local LLM (Ollama) ======
def llm_chat(messages, temperature: float = 0.5, timeout: float = 60.0) -> str:
    """
    messages: [{"role":"system"|"user"|"assistant","content":"..."}]
    Streams from Ollama /api/chat and returns assistant text.
    """
    try:
        with httpx.stream(
            "POST",
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL, 
                "messages": messages, 
                "stream": True, 
                "options": {
                    "temperature": temperature,
                    "num_ctx": 4096,  # Limit context window for faster responses
                }
            },
            timeout=timeout,
        ) as r:
            r.raise_for_status()
            chunks = []
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = data.get("message", {}).get("content", "")
                if msg:
                    chunks.append(msg)
                if data.get("done"):
                    break
            return "".join(chunks).strip() or "(no reply)"
    except Exception as e:
        return f"(LLM error: {e})"

# ====== Small talk heuristic ======
GREET_RE = re.compile(r"^\s*(hi|hello|hey|yo|good\s*(morning|evening|afternoon)|sup)\b", re.I)
THANKS_RE = re.compile(r"\b(thanks|thank you|ty)\b", re.I)

def is_small_talk(q: str) -> bool:
    ql = q.strip().lower()
    return bool(GREET_RE.search(ql) or THANKS_RE.search(ql) or ql in {"how are you?", "who are you?", "what can you do?"})

# ====== Strict extractive QA (helper) ======
def answer_question(question: str, k: int = 3) -> Dict:
    """
    Retrieval -> filter -> extractive QA per passage.
    Accept an answer only if:
      - confidence >= threshold, and
      - exact span appears in the passage (prevents hallucination)
    Else, fall back to top passage text (still grounded).
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
            sc = float(res.get("score") or 0.0)
            if ans and len(ans) > 3 and ans.lower() not in {"yes", "no", "unknown"} and ans in ctx:
                if (best is None) or (sc > best[1]):
                    best = (ans, sc, i)
        except Exception:
            continue

    CONF_THRESH = 0.55
    if best and best[1] >= CONF_THRESH:
        i = best[2]
        src = f"{hits[i]['title']} ({hits[i]['arc']})"
        reply = f"Q: {question}\n\nA: {best[0]}\n\nSources: {src}"
        return {"reply": reply, "passages": [hits[i]]}

    # Fallback: grounded verbatim (top passage)
    top = hits[0]
    reply = f"Q: {question}\n\nA: {top['text']}\n\nSources: {top['title']} ({top['arc']})"
    return {"reply": reply, "passages": [top]}

# ====== Conversational RAG (single mode for everything) ======
def _build_context(hits: List[Dict], max_chars_per_hit: int = 800) -> str:
    """Compact, numbered context block for the LLM. Truncates long texts."""
    lines = []
    for i, h in enumerate(hits, 1):
        title = h.get("title", "(untitled)")
        arc = h.get("arc", "?")
        text = (h.get("text") or "").strip()
        # Truncate long texts to prevent slow LLM responses
        if len(text) > max_chars_per_hit:
            text = text[:max_chars_per_hit] + "..."
        lines.append(f"[{i}] {title} ({arc}) — {text}")
    return "\n".join(lines)

def rag_chat(user_text: str, k: int = 5, temperature: float = 0.5) -> Dict:
    """
    One unified mode:
      • If it's small talk → chat via LLM.
      • Else retrieve top-k and, if strong enough, ask LLM to synthesize using ONLY provided sources (with citations).
      • If retrieval is weak → general LLM reply (no sources).
    """
    # 0) Small talk shortcut
    if is_small_talk(user_text):
        sys = {"role": "system", "content": "You are a friendly assistant for a One Piece app. Keep replies short and warm."}
        usr = {"role": "user", "content": user_text}
        reply = llm_chat([sys, usr], temperature=0.6)
        return {"reply": reply, "passages": []}

    # 1) Retrieve & filter
    raw_hits = search_topk(user_text, k=k)
    hits = filter_hits_by_relevance(user_text, raw_hits)
    top_score = hits[0]["score"] if hits else 0.0

    # 2) If retrieval is too weak, just chat
    if not hits or top_score < 0.12:
        sys = {"role": "system", "content": "You are a friendly assistant. Answer briefly and clearly."}
        usr = {"role": "user", "content": user_text}
        reply = llm_chat([sys, usr], temperature=0.7)
        return {"reply": reply, "passages": []}

    # 3) Build grounded context and ask LLM to synthesize (multi-passage)
    context = _build_context(hits)
    system_prompt = (
        "You are a passionate One Piece expert and fan who has read every chapter and knows the story deeply. "
        "Answer questions naturally as if you're chatting with a fellow fan. "
        "Use the reference material below to ensure accuracy, but DO NOT mention 'sources', 'provided text', or 'based on the text'. "
        "Speak confidently about One Piece lore, characters, and events. "
        "If something isn't covered in the references, say you're not sure about that specific detail. "
        "Keep answers engaging and conversational. Use character names and story context naturally.\n\n"
        "Reference material (use for accuracy but don't mention directly):\n"
    )
    user_prompt = f"{context}\n\n---\nFan question: {user_text}\n\nAnswer as a One Piece expert:"

    msgs = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    reply = llm_chat(msgs, temperature=temperature)

    return {"reply": reply, "passages": hits}
