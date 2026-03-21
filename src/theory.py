# src/theory.py — Theory evaluation using semantic search + LLM-based NLI
#
# Scoring pipeline:
#   1. Semantic search against JSONL data (SBS, interviews, foreshadowing, debunked)
#   2. Semantic search against the main DB (2,295 canon notes)
#   3. LLM-based NLI: classify each retrieved passage as SUPPORTS / CONTRADICTS / NEUTRAL
#   4. Score aggregation + final LLM analysis

from typing import List, Dict, Optional, Tuple
import json
import os
import re
import hashlib
import numpy as np

from .config import THEORY_DATA_DIR
from .llm import llm_chat_quality
from .embeddings import embed_single, embed_texts, search_topk, rerank, _get_cosine_similarity

# ---------- Cache path ----------
THEORY_CACHE_PATH = os.getenv(
    "THEORY_EMB_CACHE", "data/cache/theory_embeddings_cache.npz"
)

# ---------- Module-level cache ----------
_theory_data: Optional[Dict[str, List[Dict]]] = None
_theory_embeddings: Optional[Dict[str, np.ndarray]] = None


# ---------- Data loading + embedding cache ----------

def _jsonl_hash() -> str:
    """Hash all JSONL file contents to detect changes."""
    h = hashlib.md5()
    for name in sorted(os.listdir(THEORY_DATA_DIR)):
        if name.endswith(".jsonl"):
            path = THEORY_DATA_DIR / name
            h.update(str(os.path.getmtime(path)).encode())
            h.update(str(os.path.getsize(path)).encode())
    return h.hexdigest()


def _load_theory_data_raw() -> Dict[str, List[Dict]]:
    """Load all theory evaluation data from JSONL files."""
    data = {"sbs": [], "interviews": [], "foreshadowing": [], "debunked": []}
    file_mapping = {
        "sbs_data.jsonl": "sbs",
        "oda_interviews.jsonl": "interviews",
        "foreshadowing.jsonl": "foreshadowing",
        "debunked_theories.jsonl": "debunked",
    }
    for filename, key in file_mapping.items():
        filepath = THEORY_DATA_DIR / filename
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data[key].append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    return data


def _text_for_entry(entry: Dict, entry_type: str) -> str:
    """Build a searchable text representation of a data entry."""
    if entry_type == "sbs":
        return f"{entry.get('question', '')} {entry.get('answer', '')}"
    elif entry_type == "interviews":
        return f"{entry.get('source', '')} {entry.get('statement', '')}"
    elif entry_type == "foreshadowing":
        return f"{entry.get('setup', '')} {entry.get('payoff', '')} {entry.get('category', '')}"
    elif entry_type == "debunked":
        return f"{entry.get('theory', '')} {entry.get('reason', '')} {entry.get('lesson', '')}"
    return ""


def _load_theory_cache() -> Tuple[Optional[Dict[str, np.ndarray]], Optional[str]]:
    """Try loading cached theory embeddings from disk."""
    if not os.path.exists(THEORY_CACHE_PATH):
        return None, None
    try:
        cached = np.load(THEORY_CACHE_PATH, allow_pickle=True)
        cached_hash = str(cached["data_hash"])
        embs = {}
        for key in ("sbs", "interviews", "foreshadowing", "debunked"):
            if key in cached:
                embs[key] = cached[key]
        return embs, cached_hash
    except Exception as e:
        print(f"Theory cache load error: {e}")
        return None, None


def _save_theory_cache(embeddings: Dict[str, np.ndarray], data_hash: str):
    """Save theory embeddings to disk."""
    try:
        os.makedirs(os.path.dirname(THEORY_CACHE_PATH), exist_ok=True)
        np.savez(
            THEORY_CACHE_PATH,
            data_hash=np.array(data_hash),
            **embeddings,
        )
        total = sum(m.shape[0] for m in embeddings.values())
        print(f"Saved {total} theory embeddings to cache")
    except Exception as e:
        print(f"Theory cache save error: {e}")


def _load_theory_data() -> Tuple[Dict[str, List[Dict]], Dict[str, np.ndarray]]:
    """
    Load theory data + embeddings. Uses disk cache.
    Returns (data_dict, embeddings_dict).
    """
    global _theory_data, _theory_embeddings

    # Return in-memory cache if available
    if _theory_data is not None and _theory_embeddings is not None:
        return _theory_data, _theory_embeddings

    data = _load_theory_data_raw()
    current_hash = _jsonl_hash()

    # Try disk cache
    cached_embs, cached_hash = _load_theory_cache()
    if cached_embs is not None and cached_hash == current_hash:
        print(f"Loaded theory embeddings from cache")
        _theory_data = data
        _theory_embeddings = cached_embs
        return data, cached_embs

    # Build embeddings from scratch
    print("Building theory embeddings (first time or data changed)...")
    embeddings = {}
    for key, entries in data.items():
        if entries:
            texts = [_text_for_entry(e, key) for e in entries]
            embeddings[key] = embed_texts(texts)
            print(f"  Embedded {len(texts)} {key} entries")
        else:
            embeddings[key] = np.empty((0, 0), dtype="float32")

    _save_theory_cache(embeddings, current_hash)
    _theory_data = data
    _theory_embeddings = embeddings
    return data, embeddings


# ---------- Semantic matching ----------

def _semantic_search_entries(
    theory_vec: np.ndarray,
    entries: List[Dict],
    entry_matrix: np.ndarray,
    top_k: int = 5,
    threshold: float = 0.25,
) -> List[Dict]:
    """
    Cosine-sim between theory vector and pre-computed entry embeddings.
    Return top-k above threshold.
    """
    if not entries or entry_matrix.size == 0:
        return []

    cos_sim = _get_cosine_similarity()
    sims = cos_sim(theory_vec, entry_matrix).ravel()

    scored = []
    for i, sim in enumerate(sims):
        if sim >= threshold:
            scored.append({"entry": entries[i], "score": float(sim)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


# ---------- Canon DB search ----------

def _search_canon_db(theory: str, k: int = 8) -> List[Dict]:
    """Search the main 2,295-note database for passages relevant to the theory."""
    return search_topk(theory, k=k)


# ---------- LLM-based NLI ----------

def _classify_passages_nli(theory: str, passages: List[Dict]) -> List[Dict]:
    """
    Ask the LLM to classify each passage's relationship to the theory.
    Returns passages annotated with 'relation' (SUPPORTS/CONTRADICTS/NEUTRAL)
    and 'reasoning'.
    """
    if not passages:
        return []

    # Build a compact list of passages for the LLM
    passage_texts = []
    for i, p in enumerate(passages):
        text = (p.get("text") or "")[:300]
        title = p.get("title", "")
        passage_texts.append(f"[{i+1}] {title}: {text}")

    passages_block = "\n".join(passage_texts)

    nli_prompt = f"""Given this fan theory about One Piece:
THEORY: "{theory}"

Classify each passage below as:
- SUPPORTS: the passage provides evidence that makes the theory more plausible
- CONTRADICTS: the passage contains information that conflicts with the theory
- NEUTRAL: the passage is related but neither supports nor contradicts

For each passage, respond with EXACTLY one line in this format:
[number] RELATION: reasoning in 10 words or less

Passages:
{passages_block}"""

    try:
        response = llm_chat_quality(
            [
                {"role": "system", "content": "You are a precise fact-checker for One Piece canon. Be strict: only mark SUPPORTS if there is real evidence, and CONTRADICTS if there is a genuine conflict."},
                {"role": "user", "content": nli_prompt},
            ],
            temperature=0.1,
        )

        # Parse response lines
        results = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # Match "[1] SUPPORTS: some reasoning"
            m = re.match(r"\[(\d+)\]\s*(SUPPORTS|CONTRADICTS|NEUTRAL):?\s*(.*)", line, re.I)
            if m:
                idx = int(m.group(1)) - 1
                relation = m.group(2).upper()
                reasoning = m.group(3).strip()
                if 0 <= idx < len(passages):
                    results.append({
                        **passages[idx],
                        "relation": relation,
                        "nli_reasoning": reasoning,
                    })

        # Add any passages that weren't classified as NEUTRAL
        classified_indices = {r.get("id") or r.get("title") for r in results}
        for p in passages:
            key = p.get("id") or p.get("title")
            if key not in classified_indices:
                results.append({**p, "relation": "NEUTRAL", "nli_reasoning": ""})

        return results

    except Exception:
        # If LLM fails, return all as NEUTRAL
        return [{**p, "relation": "NEUTRAL", "nli_reasoning": ""} for p in passages]


# ---------- Sub-scoring functions ----------

def _search_supporting_evidence(
    theory_vec: np.ndarray, data: Dict, embs: Dict[str, np.ndarray]
) -> List[Dict]:
    """Find SBS/interview entries semantically related to the theory."""
    matches = []

    sbs_hits = _semantic_search_entries(
        theory_vec, data.get("sbs", []), embs.get("sbs", np.empty((0,0))),
        top_k=5, threshold=0.20,
    )
    for hit in sbs_hits:
        matches.append({"type": "sbs", "entry": hit["entry"], "relevance": hit["score"]})

    interview_hits = _semantic_search_entries(
        theory_vec, data.get("interviews", []), embs.get("interviews", np.empty((0,0))),
        top_k=5, threshold=0.20,
    )
    for hit in interview_hits:
        matches.append({"type": "interview", "entry": hit["entry"], "relevance": hit["score"]})

    matches.sort(key=lambda x: x["relevance"], reverse=True)
    return matches[:5]


def _check_foreshadowing_patterns(
    theory_vec: np.ndarray, data: Dict, embs: Dict[str, np.ndarray]
) -> List[Dict]:
    """Check if theory aligns with Oda's known foreshadowing patterns."""
    hits = _semantic_search_entries(
        theory_vec, data.get("foreshadowing", []), embs.get("foreshadowing", np.empty((0,0))),
        top_k=3, threshold=0.25,
    )
    return [
        {"pattern": hit["entry"], "match_type": "semantic", "score": hit["score"]}
        for hit in hits
    ]


def _check_debunked_patterns(
    theory_vec: np.ndarray, data: Dict, embs: Dict[str, np.ndarray]
) -> List[Dict]:
    """Check if theory is semantically close to debunked theories."""
    hits = _semantic_search_entries(
        theory_vec, data.get("debunked", []), embs.get("debunked", np.empty((0,0))),
        top_k=3, threshold=0.30,
    )
    warnings = []
    for hit in hits:
        entry = hit["entry"]
        severity = "high" if hit["score"] > 0.50 else "medium"
        warnings.append({
            "warning": f"Similar to debunked theory: '{entry.get('theory', '')}'",
            "reason": entry.get("reason", ""),
            "lesson": entry.get("lesson", ""),
            "severity": severity,
            "score": hit["score"],
        })
    return warnings[:2]


# ---------- Main evaluator ----------

def evaluate_theory(theory: str, evidence: str = "") -> Dict:
    """
    Evaluate a One Piece fan theory and return a score (0-1000).

    Scoring breakdown:
      - Base score: 300
      - Supporting evidence from JSONL data: +50 to +200
      - Foreshadowing alignment: +50 to +150
      - Debunked pattern match: -100 to -300
      - Canon DB NLI (SUPPORTS boost, CONTRADICTS penalty): -150 to +150
      - LLM final analysis: -100 to +200
    """
    data, embs = _load_theory_data()
    full_theory = f"{theory}\n\nEvidence provided: {evidence}" if evidence else theory

    # Embed the theory once
    theory_vec = embed_single(full_theory)

    # 1) JSONL evidence (SBS + interviews)
    supporting = _search_supporting_evidence(theory_vec, data, embs)

    # 2) Foreshadowing alignment
    foreshadowing = _check_foreshadowing_patterns(theory_vec, data, embs)

    # 3) Debunked pattern warnings
    debunked_warnings = _check_debunked_patterns(theory_vec, data, embs)

    # 4) Canon DB search + NLI classification
    canon_hits = _search_canon_db(full_theory, k=16)  # fetch more candidates for reranking
    relevant_canon = [h for h in canon_hits if h.get("score", 0) > 0.10]
    # Rerank for precision before sending to NLI
    relevant_canon = rerank(full_theory, relevant_canon, top_k=8) if relevant_canon else []
    nli_results = _classify_passages_nli(theory, relevant_canon) if relevant_canon else []

    supports = [r for r in nli_results if r["relation"] == "SUPPORTS"]
    contradicts = [r for r in nli_results if r["relation"] == "CONTRADICTS"]

    # 5) Score calculation
    score = 300
    breakdown = {"base": 300}

    # JSONL evidence boost
    if supporting:
        evidence_boost = 0
        for s in supporting:
            evidence_boost += int(s["relevance"] * 80)
        critical = sum(1 for s in supporting if s["entry"].get("importance") == "critical")
        evidence_boost += critical * 30
        evidence_boost = min(evidence_boost, 200)
        score += evidence_boost
        breakdown["supporting_evidence"] = f"+{evidence_boost}"

    # Foreshadowing boost
    if foreshadowing:
        foreshadow_boost = 0
        for f in foreshadowing:
            foreshadow_boost += int(f["score"] * 100)
        foreshadow_boost = min(foreshadow_boost, 150)
        score += foreshadow_boost
        breakdown["foreshadowing_patterns"] = f"+{foreshadow_boost}"

    # Debunked penalty
    if debunked_warnings:
        debunk_penalty = 0
        for w in debunked_warnings:
            debunk_penalty += 150 if w["severity"] == "high" else 75
        debunk_penalty = min(debunk_penalty, 300)
        score -= debunk_penalty
        breakdown["debunked_pattern_warning"] = f"-{debunk_penalty}"

    # Canon NLI: SUPPORTS boost + CONTRADICTS penalty
    if supports:
        canon_boost = min(len(supports) * 50, 150)
        score += canon_boost
        breakdown["canon_supports"] = f"+{canon_boost}"
    if contradicts:
        canon_penalty = min(len(contradicts) * 75, 150)
        score -= canon_penalty
        breakdown["canon_contradicts"] = f"-{canon_penalty}"

    # 6) Multi-dimensional LLM analysis
    # Build a summary of NLI findings for the LLM
    nli_summary = ""
    if supports:
        nli_summary += "SUPPORTING CANON PASSAGES:\n"
        for s in supports[:3]:
            nli_summary += f"  - {s.get('title', '')}: {s.get('nli_reasoning', '')}\n"
    if contradicts:
        nli_summary += "CONTRADICTING CANON PASSAGES:\n"
        for c in contradicts[:3]:
            nli_summary += f"  - {c.get('title', '')}: {c.get('nli_reasoning', '')}\n"

    analysis_prompt = f"""You are evaluating a One Piece fan theory across 5 dimensions. Be fair but critical.

THEORY: {theory}

USER'S EVIDENCE: {evidence if evidence else "None provided"}

SUPPORTING CANON DATA (SBS/Interviews):
{json.dumps([{"type": s["type"], "relevance": round(s["relevance"], 2), "content": str(s["entry"])[:200]} for s in supporting[:3]], indent=2) if supporting else "None"}

FORESHADOWING PATTERN MATCHES:
{json.dumps([{"setup": f["pattern"].get("setup", "")[:100], "payoff": f["pattern"].get("payoff", "")[:100], "similarity": round(f["score"], 2)} for f in foreshadowing], indent=2) if foreshadowing else "None"}

{nli_summary if nli_summary else "No strong canon passage matches found."}

DEBUNKED PATTERN WARNINGS:
{json.dumps([{"warning": w["warning"], "similarity": round(w["score"], 2)} for w in debunked_warnings], indent=2) if debunked_warnings else "None"}

Score this theory on each dimension from 1 to 5:

1. THEMATIC_FIT: Does it align with One Piece's core themes? (inherited will, freedom, dreams, found family, anti-authoritarianism, the cycle of history). 5=perfectly thematic, 1=contradicts themes.

2. NARRATIVE_STYLE: Is this how Oda writes? (long foreshadowed setups, emotional payoffs, creative powers, humor mixed with drama, rarely kills characters, avoids grimdark). 5=very Oda-like, 1=not his style at all.

3. POWER_CONSISTENCY: Does it respect established power scaling, Devil Fruit rules, Haki mechanics, and world laws? 5=fully consistent, 1=breaks established rules.

4. EVIDENCE_QUALITY: How well does the user's evidence support their claim? Are they citing real events, chapters, or patterns? Or is it vague speculation? 5=strong specific evidence, 1=no real evidence.

5. ORIGINALITY: Is this a fresh take or angle? Or is it recycled common speculation everyone has heard? 5=very original, 1=extremely common/overdone.

Respond in EXACTLY this format (no deviation):
THEMATIC_FIT: [1-5]
NARRATIVE_STYLE: [1-5]
POWER_CONSISTENCY: [1-5]
EVIDENCE_QUALITY: [1-5]
ORIGINALITY: [1-5]
ANALYSIS: [Your 3-4 sentence overall analysis]"""

    analysis = ""
    dimensions = {}
    dimension_keys = [
        "THEMATIC_FIT", "NARRATIVE_STYLE", "POWER_CONSISTENCY",
        "EVIDENCE_QUALITY", "ORIGINALITY",
    ]

    try:
        llm_response = llm_chat_quality(
            [
                {"role": "system", "content": "You are a One Piece theory analyst. Score each dimension strictly and fairly. Always respond in the exact format requested."},
                {"role": "user", "content": analysis_prompt},
            ],
            temperature=0.2,
        )

        # Parse dimension scores
        for key in dimension_keys:
            match = re.search(rf"{key}:\s*(\d)", llm_response)
            if match:
                dim_score = int(match.group(1))
                dim_score = max(1, min(5, dim_score))
                dimensions[key] = dim_score

        # Parse analysis text
        if "ANALYSIS:" in llm_response:
            analysis = llm_response.split("ANALYSIS:")[-1].strip()

        # Convert dimension scores to point adjustments
        # 1=-40, 2=-20, 3=0, 4=+20, 5=+40
        total_adjustment = 0
        for key in dimension_keys:
            if key in dimensions:
                dim_pts = (dimensions[key] - 3) * 20  # center on 3=neutral
                total_adjustment += dim_pts

        # Clamp total adjustment to -200..+200
        total_adjustment = max(-200, min(200, total_adjustment))

        score += total_adjustment
        if total_adjustment != 0:
            breakdown["dimensions"] = f"{'+' if total_adjustment > 0 else ''}{total_adjustment}"

    except Exception:
        analysis = "Could not perform detailed analysis."

    # Clamp
    score = max(0, min(1000, score))

    # Verdict
    if score >= 700:
        final_verdict = "HIGHLY PLAUSIBLE"
    elif score >= 500:
        final_verdict = "INTERESTING"
    elif score >= 300:
        final_verdict = "NEEDS MORE EVIDENCE"
    elif score >= 150:
        final_verdict = "WEAK"
    else:
        final_verdict = "UNLIKELY"

    return {
        "score": score,
        "max_score": 1000,
        "verdict": final_verdict,
        "breakdown": breakdown,
        "dimensions": dimensions,
        "analysis": analysis,
        "supporting_evidence": [
            {
                "type": s["type"],
                "summary": s["entry"].get("answer", s["entry"].get("statement", ""))[:150],
                "relevance": round(s["relevance"], 2),
            }
            for s in supporting[:3]
        ],
        "canon_evidence": [
            {
                "title": s.get("title", ""),
                "relation": s["relation"],
                "reasoning": s.get("nli_reasoning", ""),
            }
            for s in (supports + contradicts)[:5]
        ],
        "foreshadowing_matches": [
            f["pattern"].get("category", "unknown") for f in foreshadowing
        ],
        "warnings": [w["warning"] for w in debunked_warnings],
    }
