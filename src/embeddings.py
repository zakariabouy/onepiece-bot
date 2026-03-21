# src/embeddings.py — FastEmbed loading, caching, and semantic search

from typing import List, Dict, Optional
import os
import time
import threading
import sqlite3
import numpy as np

from .config import (
    DB_PATH,
    EMB_CACHE_PATH,
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE,
    MAX_TEXT_LEN,
    RELOAD_INTERVAL_SEC,
    MIN_PASSAGE_SCORE,
)

# Lazy-loaded heavy imports
_TextEmbedding = None
_cosine_similarity = None
_TextCrossEncoder = None

# Globals for notes + index
_notes: List[Dict] = []
_emb_model = None
_rerank_model = None
_emb_matrix: Optional[np.ndarray] = None
_lock = threading.Lock()
_last_reload = 0.0


def _get_embedding_model():
    """Lazy load embedding model."""
    global _TextEmbedding, _emb_model
    if _TextEmbedding is None:
        print("Loading embedding model...")
        from fastembed import TextEmbedding as TE
        _TextEmbedding = TE
    if _emb_model is None:
        _emb_model = _TextEmbedding(model_name=EMBEDDING_MODEL)
    return _emb_model


def _get_cosine_similarity():
    global _cosine_similarity
    if _cosine_similarity is None:
        from sklearn.metrics.pairwise import cosine_similarity
        _cosine_similarity = cosine_similarity
    return _cosine_similarity


def _get_rerank_model():
    """Lazy load cross-encoder reranking model."""
    global _TextCrossEncoder, _rerank_model
    if _TextCrossEncoder is None:
        print("Loading reranking model...")
        from fastembed.rerank.cross_encoder import TextCrossEncoder as TCE
        _TextCrossEncoder = TCE
    if _rerank_model is None:
        _rerank_model = _TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")
    return _rerank_model


def rerank(query: str, hits: List[Dict], top_k: int = 5, text_key: str = "text") -> List[Dict]:
    """
    Rerank retrieved passages using a cross-encoder for higher precision.
    Takes the rough embedding results and re-scores each (query, passage) pair.
    Returns top_k results sorted by cross-encoder score.
    """
    if not hits:
        return []

    model = _get_rerank_model()
    documents = [(h.get(text_key) or h.get("title") or "")[:500] for h in hits]

    # fastembed rerank returns flat list of float scores in input order
    scores = list(model.rerank(query, documents))

    # Pair with indices, sort by score descending
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in indexed[:top_k]:
        item = dict(hits[idx])
        item["rerank_score"] = float(score)
        results.append(item)

    return results


# ---------- Cache ----------

def _get_db_hash():
    try:
        return os.path.getmtime(DB_PATH)
    except Exception:
        return 0


def _load_cache():
    if not os.path.exists(EMB_CACHE_PATH):
        return None, None, None
    try:
        data = np.load(EMB_CACHE_PATH, allow_pickle=True)
        cached_hash = float(data.get("db_hash", 0))
        if cached_hash != _get_db_hash():
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
    try:
        np.savez(
            EMB_CACHE_PATH,
            notes=np.array(notes, dtype=object),
            embeddings=emb_matrix,
            db_hash=db_hash,
        )
        print(f"Saved {len(notes)} embeddings to cache")
    except Exception as e:
        print(f"Cache save error: {e}")


# ---------- Index building ----------

def load_notes_and_build_index():
    """Load notes from SQLite and build an embedding matrix. Uses disk cache."""
    global _notes, _emb_model, _emb_matrix

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
        c.execute(
            """CREATE TABLE IF NOT EXISTS notes (
                id   TEXT PRIMARY KEY,
                title TEXT,
                arc   TEXT,
                text  TEXT
            )"""
        )
        rows = c.execute("SELECT id, title, arc, text FROM notes").fetchall()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        rows = []

    notes = [{"id": r[0], "title": r[1], "arc": r[2], "text": r[3]} for r in rows]

    docs = []
    for n in notes:
        text = (n["text"] or "")[:MAX_TEXT_LEN]
        docs.append(f"{n['title']} — {text}")

    if _emb_model is None:
        _emb_model = _get_embedding_model()

    print(f"Embedding {len(docs)} documents in small batches...")
    all_vecs = []
    for i in range(0, len(docs), EMBEDDING_BATCH_SIZE):
        batch = docs[i : i + EMBEDDING_BATCH_SIZE]
        batch_vecs = list(_emb_model.embed(batch))
        all_vecs.extend(batch_vecs)
        if (i // EMBEDDING_BATCH_SIZE) % 10 == 0:
            print(f"  Embedded {min(i + EMBEDDING_BATCH_SIZE, len(docs))}/{len(docs)} docs...")

    emb_matrix = np.array(all_vecs, dtype="float32") if all_vecs else None

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


# ---------- Embedding utilities ----------

def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a list of texts and return the matrix. Reuses the cached model."""
    global _emb_model
    if _emb_model is None:
        _emb_model = _get_embedding_model()
    vecs = list(_emb_model.embed(texts))
    return np.array(vecs, dtype="float32")


def embed_single(text: str) -> np.ndarray:
    """Embed a single text and return a (1, dim) matrix."""
    return embed_texts([text])


# ---------- Search ----------

def _is_latest_query(query: str) -> bool:
    patterns = [
        "latest", "recent", "newest", "last chapter", "last event",
        "current", "now", "happening now", "most recent", "currently",
    ]
    q_lower = query.lower()
    return any(p in q_lower for p in patterns)


def _get_latest_chapters(k: int = 5) -> List[Dict]:
    _maybe_reload()
    chapter_notes = [n for n in _notes if n.get("id", "").startswith("chapter_")]
    chapter_notes.sort(
        key=lambda x: int(x["id"].replace("chapter_", "") or 0), reverse=True
    )
    results = []
    for note in chapter_notes[:k]:
        item = dict(note)
        item["score"] = 1.0
        results.append(item)
    return results


def search_topk(query: str, k: int = 5) -> List[Dict]:
    """Semantic search over all notes. Returns top-k with scores."""
    global _emb_model
    _maybe_reload()
    if not _notes or _emb_matrix is None:
        return []

    if _is_latest_query(query):
        return _get_latest_chapters(k)

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
    allowed_arcs = {
        (h.get("arc") or "").lower()
        for h in hits
        if (h.get("arc") or "").lower() in q
    }
    filtered = []
    for h in hits:
        score_ok = h.get("score", 0.0) > MIN_PASSAGE_SCORE
        arc_ok = ((h.get("arc") or "").lower() in allowed_arcs) if allowed_arcs else False
        if score_ok or arc_ok:
            filtered.append(h)
    if not filtered and hits:
        filtered = [hits[0]]
    return filtered
