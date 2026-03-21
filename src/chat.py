# src/chat.py — conversational RAG (semantic retrieval + LLM synthesis)

from typing import List, Dict
import re

from .config import MAX_HISTORY_TURNS, WEAK_RETRIEVAL_THRESHOLD
from .llm import llm_chat
from .embeddings import search_topk, filter_hits_by_relevance, rerank

# ---------- Small talk detection ----------
GREET_RE = re.compile(
    r"^\s*(hi|hello|hey|yo|good\s*(morning|evening|afternoon)|sup)\b", re.I
)
THANKS_RE = re.compile(r"\b(thanks|thank you|ty)\b", re.I)


def is_small_talk(q: str) -> bool:
    ql = q.strip().lower()
    return bool(
        GREET_RE.search(ql)
        or THANKS_RE.search(ql)
        or ql in {"how are you?", "who are you?", "what can you do?"}
    )


# ---------- Context building ----------
def _build_context(hits: List[Dict], max_chars_per_hit: int = 800) -> str:
    """Compact, numbered context block for the LLM."""
    lines = []
    for i, h in enumerate(hits, 1):
        title = h.get("title", "(untitled)")
        arc = h.get("arc", "?")
        text = (h.get("text") or "").strip()
        if len(text) > max_chars_per_hit:
            text = text[:max_chars_per_hit] + "..."
        lines.append(f"[{i}] {title} ({arc}) — {text}")
    return "\n".join(lines)


# ---------- Simple QA ----------
def answer_question(question: str, k: int = 3) -> Dict:
    raw_hits = search_topk(question, k=k)
    hits = filter_hits_by_relevance(question, raw_hits)
    if not hits:
        return {"reply": "Sorry, I don't know yet.", "passages": []}
    top = hits[0]
    reply = f"Q: {question}\n\nA: {top['text']}\n\nSources: {top['title']} ({top['arc']})"
    return {"reply": reply, "passages": [top]}


# ---------- Conversational RAG ----------
def rag_chat(
    user_text: str,
    k: int = 5,
    temperature: float = 0.5,
    history: List[Dict] = None,
) -> Dict:
    """
    Conversational RAG with memory:
      - Accepts conversation history for multi-turn context
      - Small talk → LLM with history
      - Otherwise retrieve top-k and synthesize
      - Weak retrieval → general LLM reply
    """
    history = history or []
    recent_history = history[-MAX_HISTORY_TURNS:]

    # Small talk shortcut
    if is_small_talk(user_text):
        sys = {
            "role": "system",
            "content": (
                "You are a friendly assistant for a One Piece app. "
                "Keep replies short and warm. Remember the conversation context."
            ),
        }
        msgs = [sys] + recent_history + [{"role": "user", "content": user_text}]
        reply = llm_chat(msgs, temperature=0.6)
        return {"reply": reply, "passages": []}

    # Retrieve, filter, rerank
    raw_hits = search_topk(user_text, k=k * 2)  # fetch more candidates for reranking
    hits = filter_hits_by_relevance(user_text, raw_hits)
    hits = rerank(user_text, hits, top_k=k) if hits else []
    top_score = hits[0].get("rerank_score", hits[0].get("score", 0)) if hits else 0.0

    # Weak retrieval → just chat
    if not hits or top_score < WEAK_RETRIEVAL_THRESHOLD:
        sys = {
            "role": "system",
            "content": (
                "You are a friendly One Piece expert. "
                "Answer briefly and clearly. Remember the conversation context."
            ),
        }
        msgs = [sys] + recent_history + [{"role": "user", "content": user_text}]
        reply = llm_chat(msgs, temperature=0.7)
        return {"reply": reply, "passages": []}

    # Build grounded context
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
    user_prompt = f"{context}\n\n---\nFan question: {user_text}\n\nAnswer as a One Piece expert:"

    msgs = [{"role": "system", "content": system_prompt}]
    msgs.extend(recent_history)
    msgs.append({"role": "user", "content": user_prompt})

    reply = llm_chat(msgs, temperature=temperature)
    return {"reply": reply, "passages": hits}
