# core.py — unified conversational RAG (semantic retrieval + cloud LLM via Groq)
# - Retrieval: FastEmbed (BAAI/bge-small-en-v1.5)
# - Synthesis: Groq cloud LLM (fast & free)
# - Fallbacks for small talk / weak retrieval

from typing import List, Dict
import os, re, time, threading, sqlite3, json
import numpy as np
from dotenv import load_dotenv

# Load .env file (for local development)
load_dotenv()

# ---------- Get API key from Streamlit secrets OR .env ----------
def _get_api_key():
    """Get Groq API key from Streamlit secrets (cloud) or .env (local)."""
    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'GROQ_API_KEY' in st.secrets:
            return st.secrets['GROQ_API_KEY']
    except:
        pass
    # Fall back to environment variable
    return os.getenv("GROQ_API_KEY", "")

# ---------- Cloud LLM (Groq - fast & free) ----------
from groq import Groq

# ====== Config ======
DB_PATH = os.getenv("ONEPIECE_DB", "onepiece.db")
EMB_CACHE_PATH = os.getenv("EMB_CACHE", "embeddings_cache.npz")  # Disk cache!
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Fast model
RELOAD_INTERVAL_SEC = 3600  # Only reload every hour (embeddings cached)

# Initialize Groq client
_groq_client = None

def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = _get_api_key()
        if not api_key:
            raise ValueError("GROQ_API_KEY not set! Get free key at: https://console.groq.com/keys")
        _groq_client = Groq(api_key=api_key)
    return _groq_client

# LAZY LOAD heavy libraries
_TextEmbedding = None
_cosine_similarity = None

def _get_embedding_model():
    """Lazy load embedding model."""
    global _TextEmbedding, _emb_model
    if _TextEmbedding is None:
        print("Loading embedding model...")
        from fastembed import TextEmbedding as TE
        _TextEmbedding = TE
    if _emb_model is None:
        _emb_model = _TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _emb_model

def _get_cosine_similarity():
    global _cosine_similarity
    if _cosine_similarity is None:
        from sklearn.metrics.pairwise import cosine_similarity
        _cosine_similarity = cosine_similarity
    return _cosine_similarity

# ====== Globals for notes + index ======
_notes: List[Dict] = []
_emb_model = None
_emb_matrix: np.ndarray | None = None
_lock = threading.Lock()
_last_reload = 0.0

# ====== Data / Index ======
def _get_db_hash():
    """Quick hash to detect if DB changed."""
    try:
        return os.path.getmtime(DB_PATH)
    except:
        return 0

def _load_cache():
    """Load embeddings from disk cache if valid."""
    if not os.path.exists(EMB_CACHE_PATH):
        return None, None, None
    try:
        data = np.load(EMB_CACHE_PATH, allow_pickle=True)
        cached_hash = float(data.get("db_hash", 0))
        current_hash = _get_db_hash()
        if cached_hash != current_hash:
            print("DB changed, cache invalidated")
            return None, None, None
        notes = data["notes"].tolist()
        emb_matrix = data["embeddings"]
        print(f"Loaded {len(notes)} embeddings from cache")
        return notes, emb_matrix, cached_hash
    except Exception as e:
        print(f"Cache load error: {e}")
        return None, None, None

def _save_cache(notes, emb_matrix, db_hash):
    """Save embeddings to disk."""
    try:
        np.savez(EMB_CACHE_PATH, notes=np.array(notes, dtype=object), 
                 embeddings=emb_matrix, db_hash=db_hash)
        print(f"Saved {len(notes)} embeddings to cache")
    except Exception as e:
        print(f"Cache save error: {e}")

def load_notes_and_build_index():
    """Load notes from SQLite and build an embedding matrix. Uses disk cache."""
    global _notes, _emb_model, _emb_matrix

    # Try loading from cache first
    cached_notes, cached_emb, _ = _load_cache()
    if cached_notes is not None and cached_emb is not None:
        with _lock:
            _notes = cached_notes
            _emb_matrix = cached_emb
        return

    print("Building embeddings (this only happens once)...")
    
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
    
    # Truncate text to avoid memory issues during embedding
    MAX_TEXT_LEN = 500  # Characters per document for embedding
    docs = []
    for n in notes:
        text = (n['text'] or "")[:MAX_TEXT_LEN]
        docs.append(f"{n['title']} — {text}")

    if _emb_model is None:
        _emb_model = _get_embedding_model()

    print(f"Embedding {len(docs)} documents in small batches...")
    
    # Embed in very small batches to avoid memory issues
    BATCH_SIZE = 8  # Smaller batch for low memory
    all_vecs = []
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        batch_vecs = list(_emb_model.embed(batch))
        all_vecs.extend(batch_vecs)
        if (i // BATCH_SIZE) % 10 == 0:  # Print every 10 batches
            print(f"  Embedded {min(i + BATCH_SIZE, len(docs))}/{len(docs)} docs...")
    
    emb_matrix = np.array(all_vecs, dtype="float32") if all_vecs else None

    # Save to cache for next time
    if emb_matrix is not None:
        _save_cache(notes, emb_matrix, _get_db_hash())

    with _lock:
        _notes = notes
        _emb_matrix = emb_matrix
    
    print("Embeddings ready!")

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
    global _emb_model
    _maybe_reload()
    if not _notes or _emb_matrix is None:
        return []
    
    # Special handling for "latest/recent" queries
    if _is_latest_query(query):
        return _get_latest_chapters(k)
    
    # Ensure embedding model is loaded (needed for query embedding)
    if _emb_model is None:
        _emb_model = _get_embedding_model()
    
    q_vec = np.array(list(_emb_model.embed([query]))[0], dtype="float32").reshape(1, -1)
    sims = _get_cosine_similarity()(q_vec, _emb_matrix).ravel()
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
def llm_chat(messages, temperature: float = 0.5, timeout: float = 30.0) -> str:
    """
    messages: [{"role":"system"|"user"|"assistant","content":"..."}]
    Uses Groq cloud API for fast inference.
    """
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip() or "(no reply)"
    except Exception as e:
        return f"(LLM error: {e})"

# ====== Small talk heuristic ======
GREET_RE = re.compile(r"^\s*(hi|hello|hey|yo|good\s*(morning|evening|afternoon)|sup)\b", re.I)
THANKS_RE = re.compile(r"\b(thanks|thank you|ty)\b", re.I)

def is_small_talk(q: str) -> bool:
    ql = q.strip().lower()
    return bool(GREET_RE.search(ql) or THANKS_RE.search(ql) or ql in {"how are you?", "who are you?", "what can you do?"})

# ====== Simple QA (uses Groq instead of heavy local model) ======
def answer_question(question: str, k: int = 3) -> Dict:
    """
    Simple retrieval + LLM answer.
    """
    raw_hits = search_topk(question, k=k)
    hits = filter_hits_by_relevance(question, raw_hits)
    if not hits:
        return {"reply": "Sorry, I don't know yet.", "passages": []}

    # Use top passage
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

def rag_chat(user_text: str, k: int = 5, temperature: float = 0.5, history: List[Dict] = None) -> Dict:
    """
    Conversational RAG with memory:
      • Accepts conversation history for multi-turn context
      • If it's small talk → chat via LLM with history
      • Else retrieve top-k and synthesize with history context
      • If retrieval is weak → general LLM reply with history
    
    history: List of {"role": "user"|"assistant", "content": "..."}
    """
    history = history or []
    
    # Limit history to last 6 turns (3 user + 3 assistant) to save tokens
    MAX_HISTORY = 6
    recent_history = history[-MAX_HISTORY:] if len(history) > MAX_HISTORY else history
    
    # 0) Small talk shortcut
    if is_small_talk(user_text):
        sys = {"role": "system", "content": "You are a friendly assistant for a One Piece app. Keep replies short and warm. Remember the conversation context."}
        msgs = [sys] + recent_history + [{"role": "user", "content": user_text}]
        reply = llm_chat(msgs, temperature=0.6)
        return {"reply": reply, "passages": []}

    # 1) Retrieve & filter
    raw_hits = search_topk(user_text, k=k)
    hits = filter_hits_by_relevance(user_text, raw_hits)
    top_score = hits[0]["score"] if hits else 0.0

    # 2) If retrieval is too weak, just chat with history
    if not hits or top_score < 0.12:
        sys = {"role": "system", "content": "You are a friendly One Piece expert. Answer briefly and clearly. Remember the conversation context."}
        msgs = [sys] + recent_history + [{"role": "user", "content": user_text}]
        reply = llm_chat(msgs, temperature=0.7)
        return {"reply": reply, "passages": []}

    # 3) Build grounded context and ask LLM to synthesize (multi-passage)
    context = _build_context(hits)
    system_prompt = (
        "You are a passionate One Piece expert and fan who has read every chapter and knows the story deeply. "
        "Answer questions naturally as if you're chatting with a fellow fan. "
        "Use the reference material below to ensure accuracy, but DO NOT mention 'sources', 'provided text', or 'based on the text'. "
        "Speak confidently about One Piece lore, characters, and events. "
        "If something isn't covered in the references, say you're not sure about that specific detail. "
        "Keep answers engaging and conversational. Use character names and story context naturally. "
        "IMPORTANT: Remember the conversation history and refer back to previous topics when relevant.\n\n"
        "Reference material (use for accuracy but don't mention directly):\n"
    )
    
    # Build conversation-aware prompt
    user_prompt = f"{context}\n\n---\nFan question: {user_text}\n\nAnswer as a One Piece expert:"

    msgs = [{"role": "system", "content": system_prompt}]
    # Add conversation history for context
    msgs.extend(recent_history)
    msgs.append({"role": "user", "content": user_prompt})
    
    reply = llm_chat(msgs, temperature=temperature)

    return {"reply": reply, "passages": hits}
