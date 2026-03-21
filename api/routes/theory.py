import asyncio
from fastapi import APIRouter
from api.schemas import TheoryRequest

router = APIRouter()


@router.post("/api/theory/evaluate")
async def evaluate(req: TheoryRequest):
    from src.theory import evaluate_theory

    result = await asyncio.to_thread(evaluate_theory, req.theory, req.evidence)
    return result
