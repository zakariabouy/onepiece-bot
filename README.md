# One Piece Bot

AI chatbot for One Piece with a theory evaluation system. Chat about the story using RAG-powered search across 2,000+ canon sources, or submit fan theories and get them scored against canon evidence.

## Features

**Chat** — Ask anything about One Piece. The bot retrieves relevant passages from a knowledge base of chapter summaries, character profiles, and lore notes, then generates answers with source citations.

**Theory Scorer** — Submit a fan theory and get a multi-dimensional analysis:
- Semantic search against SBS data, Oda interviews, foreshadowing patterns, and debunked theories
- Canon database search with cross-encoder reranking
- NLI (Natural Language Inference) contradiction detection
- 5-dimension scoring: Thematic Fit, Narrative Style, Power Consistency, Evidence Quality, Originality

## Architecture

```
Next.js (frontend)  -->  FastAPI (backend)  -->  Groq (fast chat)
                                            -->  Cerebras 235B (theory analysis)
                                            -->  FastEmbed (semantic search)
                                            -->  SQLite (canon database)
```

- **Chat LLM**: Groq (llama-3.1-8b-instant) for fast responses
- **Theory LLM**: Cerebras (qwen-3-235b-a22b-instruct-2507) for deep analysis, falls back to Groq
- **Embeddings**: FastEmbed (BAAI/bge-small-en-v1.5) with disk caching
- **Reranking**: Cross-encoder (Xenova/ms-marco-MiniLM-L-6-v2)

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Groq API Key](https://console.groq.com/keys) (free)
- [Cerebras API Key](https://cloud.cerebras.ai/) (free, optional — improves theory scoring)

### Setup

```bash
git clone https://github.com/zakariabouy/onepiece-bot.git
cd onepiece-bot

# Python backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..

# Environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Run

```bash
# Terminal 1 — API server
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Project Structure

```
onepiece-bot/
├── api/                     # FastAPI backend
│   ├── main.py              # App entry, CORS, static mounts
│   ├── schemas.py           # Pydantic request/response models
│   └── routes/
│       ├── chat.py          # POST /api/chat
│       ├── theory.py        # POST /api/theory/evaluate
│       └── health.py        # GET /api/health
├── src/                     # Core logic
│   ├── config.py            # Paths, model names, API key helpers
│   ├── llm.py               # Dual LLM client (Groq + Cerebras)
│   ├── embeddings.py        # Embedding, search, caching, reranking
│   ├── chat.py              # RAG chat pipeline
│   ├── theory.py            # Theory evaluation pipeline
│   └── core.py              # Re-exports for backwards compatibility
├── frontend/                # Next.js 14 app
│   ├── src/app/             # Pages (chat, theory)
│   ├── src/components/      # Shared components
│   ├── src/lib/             # API client, types
│   └── public/              # Static assets
├── data/
│   ├── db/onepiece.db       # SQLite canon database
│   ├── assets/              # JSONL theory data, images
│   ├── cache/               # Embedding caches
│   └── characters/          # Character portrait images
├── ui.py                    # Legacy Streamlit UI
├── requirements.txt
└── .env                     # API keys (not in git)
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for chat |
| `CEREBRAS_API_KEY` | No | Cerebras API key for theory scoring (falls back to Groq) |
| `GROQ_MODEL` | No | Override chat model (default: `llama-3.1-8b-instant`) |
| `CEREBRAS_MODEL` | No | Override theory model (default: `qwen-3-235b-a22b-instruct-2507`) |

## Data Sources

- 2,295 canon notes (chapter summaries, character profiles, lore)
- 59 SBS Q&A entries
- 36 Oda interview excerpts
- 39 foreshadowing patterns
- 34 debunked theories
- 56+ character portrait images
