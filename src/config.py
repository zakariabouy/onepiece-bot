# src/config.py — shared configuration for the One Piece Bot

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------- Paths ----------
DB_PATH = os.getenv("ONEPIECE_DB", "data/db/onepiece.db")
EMB_CACHE_PATH = os.getenv("EMB_CACHE", "data/cache/embeddings_cache.npz")
THEORY_DATA_DIR = Path("data/assets")

# ---------- LLM: fast model (chat) ----------
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ---------- LLM: quality model (theory/NLI) ----------
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "qwen-3-235b-a22b-instruct-2507")
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"

# ---------- Embedding ----------
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_BATCH_SIZE = 8
MAX_TEXT_LEN = 1000  # max chars per document for embedding

# ---------- RAG ----------
RELOAD_INTERVAL_SEC = 3600
MAX_HISTORY_TURNS = 6
WEAK_RETRIEVAL_THRESHOLD = 0.12
MIN_PASSAGE_SCORE = 0.05


def get_api_key() -> str:
    """Get Groq API key from Streamlit secrets (cloud) or .env (local)."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "")


def get_cerebras_api_key() -> str:
    """Get Cerebras API key from Streamlit secrets (cloud) or .env (local)."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "CEREBRAS_API_KEY" in st.secrets:
            return st.secrets["CEREBRAS_API_KEY"]
    except Exception:
        pass
    return os.getenv("CEREBRAS_API_KEY", "")
