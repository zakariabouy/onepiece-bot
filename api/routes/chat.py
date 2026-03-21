import asyncio
import re
from pathlib import Path
from fastapi import APIRouter
from api.schemas import ChatRequest

router = APIRouter()

CHARACTER_IMAGE_DIR = Path("data/characters")

ASKING_PATTERNS = [
    r"who\s+is\s+",
    r"tell\s+me\s+about\s+",
    r"what\s+(is|are|about|does|did|can|was|were)\s+.{0,20}('s|s')?\s*",
    r"describe\s+",
    r"explain\s+",
    r"^(luffy|zoro|nami|sanji|robin|chopper|franky|brook|jinbe|usopp)",
]

CHARACTERS = [
    (r'\bluffy\b', "Monkey D. Luffy", "monkey_d__luffy"),
    (r'\bzoro\b', "Roronoa Zoro", "roronoa_zoro"),
    (r'\bnami\b', "Nami", "nami"),
    (r'\busopp\b', "Usopp", "usopp"),
    (r'\bsanji\b', "Sanji", "sanji"),
    (r'\bchopper\b', "Tony Tony Chopper", "tony_tony_chopper"),
    (r'\brobin\b', "Nico Robin", "nico_robin"),
    (r'\bfranky\b', "Franky", "franky"),
    (r'\bbrook\b', "Brook", "brook"),
    (r'\bjinbe\b', "Jinbe", "jinbe"),
    (r'\bshanks\b', "Shanks", "shanks"),
    (r'\bace\b', "Portgas D. Ace", "portgas_d__ace"),
    (r'\bsabo\b', "Sabo", "sabo"),
    (r'\blaw\b', "Trafalgar Law", "trafalgar_law"),
    (r'\bkaido\b', "Kaido", "kaido"),
    (r'\bbig\s*mom\b', "Big Mom", "big_mom"),
    (r'\bblackbeard\b', "Blackbeard", "blackbeard"),
    (r'\bwhitebeard\b', "Whitebeard", "whitebeard"),
    (r'\bdoflamingo\b', "Doflamingo", "donquixote_doflamingo"),
    (r'\bmihawk\b', "Dracule Mihawk", "dracule_mihawk"),
    (r'\bhancock\b', "Boa Hancock", "boa_hancock"),
    (r'\bkatakuri\b', "Katakuri", "katakuri"),
    (r'\bmarco\b', "Marco", "marco"),
    (r'\bgarp\b', "Monkey D. Garp", "monkey_d__garp"),
    (r'\brayleigh\b', "Silvers Rayleigh", "silvers_rayleigh"),
    (r'\broger\b', "Gol D. Roger", "gol_d__roger"),
    (r'\benel\b', "Enel", "enel"),
    (r'\bcrocodile\b', "Crocodile", "crocodile"),
    (r'\bbuggy\b', "Buggy", "buggy"),
    (r'\byamato\b', "Yamato", "yamato"),
    (r'\bvivi\b', "Nefertari Vivi", "nefertari_vivi"),
    (r'\bsmoker\b', "Smoker", "smoker"),
    (r'\bkoby\b', "Koby", "koby"),
    (r'\bcarrot\b', "Carrot", "carrot"),
    (r'\bbonney\b', "Jewelry Bonney", "jewelry_bonney"),
    (r'\bkid\b', "Eustass Kid", "eustass_kid"),
    (r'\baokiji\b', "Aokiji", "aokiji"),
    (r'\bkizaru\b', "Kizaru", "kizaru"),
    (r'\bfujitora\b', "Fujitora", "fujitora"),
    (r'\bmagellan\b', "Magellan", "magellan"),
    (r'\bivankov\b', "Ivankov", "emporio_ivankov"),
    (r'\balvida\b', "Alvida", "alvida"),
    (r'\barlong\b', "Arlong", "arlong"),
]


def find_character_image(question: str) -> dict | None:
    q = question.lower().strip()
    if not any(re.search(p, q) for p in ASKING_PATTERNS):
        return None
    for pattern, display_name, filename_base in CHARACTERS:
        if re.search(pattern, q):
            img_path = CHARACTER_IMAGE_DIR / f"{filename_base}.jpg"
            if img_path.exists():
                return {"name": display_name, "image": f"/static/characters/{filename_base}.jpg"}
    return None


@router.post("/api/chat")
async def chat(req: ChatRequest):
    from src.chat import rag_chat

    history = [{"role": m.role, "content": m.content} for m in req.history]

    result = await asyncio.to_thread(
        rag_chat, req.message, k=req.k, temperature=req.temperature, history=history
    )

    char = find_character_image(req.message)

    return {
        "reply": result.get("reply", ""),
        "passages": result.get("passages", []),
        "character": char,
    }
