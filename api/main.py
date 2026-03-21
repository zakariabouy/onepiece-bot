import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import chat, theory, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: pre-warm embeddings
    from src.embeddings import load_notes_and_build_index
    print("Loading embeddings on startup...")
    load_notes_and_build_index()
    print("Ready!")
    yield


app = FastAPI(title="One Piece Bot API", lifespan=lifespan)

# CORS
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Routes
app.include_router(chat.router)
app.include_router(theory.router)
app.include_router(health.router)

# Static files (character images + assets)
app.mount("/static/characters", StaticFiles(directory="data/characters"), name="characters")
app.mount("/static/assets", StaticFiles(directory="data/assets"), name="assets")
