from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
async def health():
    from src.embeddings import _notes
    return {"status": "ok", "notes_loaded": len(_notes)}
