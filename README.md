# 🏴‍☠️ One Piece RAG Chatbot

An AI-powered chatbot that answers questions about One Piece using **Retrieval-Augmented Generation (RAG)**.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://onepiece-bot.streamlit.app)

## ✨ Features

- 🤖 **AI-Powered Answers**: Uses Groq's LLaMA 3.1 for fast, accurate responses
- 📚 **RAG Architecture**: Retrieves relevant information from 2,300+ One Piece sources
- 🔍 **Semantic Search**: FastEmbed embeddings for intelligent context matching
- 💬 **Conversation Memory**: Remembers context from previous messages
- 🖼️ **Character Images**: Shows character portraits when discussing them
- ⚡ **Fast Responses**: 2-5 second response times via Groq cloud

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [Groq API Key](https://console.groq.com/keys) (free!)

### Local Installation

```bash
# Clone the repository
git clone https://github.com/zakariabouy/onepiece-bot.git
cd onepiece-bot

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Run the chatbot
streamlit run ui.py
```

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│  Streamlit  │────▶│   Groq      │
│   Query     │     │   UI        │     │   LLM       │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                    ┌─────▼─────┐
                    │ FastEmbed │
                    │ Embeddings│
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │  SQLite   │
                    │  Database │
                    └───────────┘
```

## 📁 Project Structure

```
onepiece-bot/
├── ui.py                    # 🎯 Main Streamlit app
├── src/                     # 📦 Source code
│   ├── __init__.py
│   └── core.py              # RAG logic & Groq LLM
├── data/                    # 📊 Data files
│   ├── db/
│   │   └── onepiece.db      # SQLite database
│   ├── cache/
│   │   └── embeddings_cache.npz
│   ├── assets/
│   │   ├── bg.jpeg          # Background image
│   │   ├── chapters.csv     # Chapter data
│   │   └── notes.jsonl      # Character notes
│   └── characters/          # Character images (56+)
├── scripts/                 # 🔧 Data utilities
├── tests/                   # 🧪 Unit tests
├── notebooks/               # 📓 Jupyter notebooks
├── .streamlit/              # Streamlit config
├── requirements.txt
└── .env                     # API keys (not in git)
```

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | Required | Your Groq API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | LLM model to use |

## 📊 Data Sources

- 1,158 Chapter summaries (up to Chapter 1130+)
- 25+ Character profiles with images
- 20+ Devil Fruit details
- 56+ Character portrait images

## 🚀 Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add `GROQ_API_KEY` in Secrets
5. Deploy!

---

*"I'm gonna be King of the Pirates!"* - Monkey D. Luffy 🏴‍☠️