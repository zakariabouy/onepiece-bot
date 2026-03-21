# src/core.py — backwards-compatible re-exports
#
# The actual logic now lives in focused modules:
#   config.py      → paths, constants, API key
#   llm.py         → Groq client
#   embeddings.py  → FastEmbed, caching, search
#   chat.py        → conversational RAG
#   theory.py      → theory evaluation (semantic search)

from .embeddings import load_notes_and_build_index, search_topk, filter_hits_by_relevance
from .llm import llm_chat
from .chat import rag_chat, answer_question, is_small_talk
from .theory import evaluate_theory

__all__ = [
    "load_notes_and_build_index",
    "search_topk",
    "filter_hits_by_relevance",
    "llm_chat",
    "rag_chat",
    "answer_question",
    "is_small_talk",
    "evaluate_theory",
]
