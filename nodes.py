"""
nodes.py — LangGraph Node Functions (Groq API)

Pipeline order:
  rag_node → pros_node → cons_node → conflict_node
           → summary_node → scoring_node → validation_node
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from groq import Groq

import config
from prompts import (
    PROS_EXTRACTION_PROMPT,
    CONS_EXTRACTION_PROMPT,
    CONFLICT_DETECTION_PROMPT,
    SUMMARY_EN_PROMPT,
    SUMMARY_AR_PROMPT,
    SCORING_PROMPT,
)
from rag import ReviewRAG
from state import VerdictState, VerdictOutput, ProCon

logger = logging.getLogger(__name__)


# ─── Groq Client (singleton) ──────────────────────────────────────────────────

_client: Groq | None = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


# ─── LLM Call ─────────────────────────────────────────────────────────────────

def _call_llm(prompt: str, temperature: float = 0.0) -> str:
    """
    Call Groq chat completion.
    Uses config.GROQ_MODEL (default: llama-3.3-70b-versatile).
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()


# ─── JSON Parser ─────────────────────────────────────────────────────────────

def _parse_json(raw: str, default: Any) -> Any:
    """
    Robustly extract JSON from LLM output.
    Handles markdown fences and leading/trailing text.
    """
    # Strip markdown fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    # Find outermost [ or { boundary
    starts = [raw.find(c) for c in "[{" if raw.find(c) != -1]
    if not starts:
        logger.warning("_parse_json: no JSON boundary found. Raw: %.150s", raw)
        return default
    start = min(starts)
    end = max(raw.rfind("]"), raw.rfind("}")) + 1

    if end <= start:
        return default

    try:
        return json.loads(raw[start:end])
    except json.JSONDecodeError as exc:
        logger.warning("_parse_json error: %s | Raw: %.150s", exc, raw)
        return default


# ─── Formatting helpers ───────────────────────────────────────────────────────

def _fmt_reviews(reviews: list[str]) -> str:
    return "\n".join(f"[{i+1}] {r}" for i, r in enumerate(reviews))

def _fmt_items(items: list[dict]) -> str:
    if not items:
        return "None identified."
    return "\n".join(f"- {p['aspect']}: {p['evidence']}" for p in items)

def _fmt_list(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items) if items else "None."


# ─── Node 1: RAG ─────────────────────────────────────────────────────────────

def rag_node(state: VerdictState) -> dict:
    reviews = state.get("reviews", [])
    if not reviews:
        return {
            "review_chunks": [],
            "retrieved_context": "",
            "errors": ["rag_node: No reviews provided."],
        }

    rag = ReviewRAG()
    rag.build(reviews, embedding_model=config.EMBEDDING_MODEL)

    context = rag.retrieve(
        query="product quality features pros cons performance",
        top_k=config.RAG_TOP_K,
    )

    logger.info("rag_node: %d chunks built, context len=%d", len(rag.chunks), len(context))
    return {
        "review_chunks": rag.chunks,
        "retrieved_context": context,
        "errors": [],
    }


# ─── Node 2: Pros Extractor ──────────────────────────────────────────────────

def pros_node(state: VerdictState) -> dict:
    reviews = state.get("reviews", [])
    if not reviews:
        return {"raw_pros": [], "errors": []}

    prompt = PROS_EXTRACTION_PROMPT.format(
        reviews=_fmt_reviews(reviews),
        context=state.get("retrieved_context", ""),
    )
    raw = _call_llm(prompt)
    items = _parse_json(raw, default=[])

    validated = []
    for item in (items if isinstance(items, list) else []):
        try:
            validated.append(ProCon(**item).model_dump())
        except Exception as exc:
            logger.warning("pros_node: skipped invalid item — %s | item=%s", exc, item)

    logger.info("pros_node: %d pros extracted.", len(validated))
    return {"raw_pros": validated, "errors": []}


# ─── Node 3: Cons Extractor ──────────────────────────────────────────────────

def cons_node(state: VerdictState) -> dict:
    reviews = state.get("reviews", [])
    if not reviews:
        return {"raw_cons": [], "errors": []}

    prompt = CONS_EXTRACTION_PROMPT.format(
        reviews=_fmt_reviews(reviews),
        context=state.get("retrieved_context", ""),
    )
    raw = _call_llm(prompt)
    items = _parse_json(raw, default=[])

    validated = []
    for item in (items if isinstance(items, list) else []):
        try:
            validated.append(ProCon(**item).model_dump())
        except Exception as exc:
            logger.warning("cons_node: skipped invalid item — %s | item=%s", exc, item)

    logger.info("cons_node: %d cons extracted.", len(validated))
    return {"raw_cons": validated, "errors": []}


# ─── Node 4: Conflict Detector ───────────────────────────────────────────────

def conflict_node(state: VerdictState) -> dict:
    reviews = state.get("reviews", [])
    if not reviews:
        return {
            "disagreements": [],
            "unknowns": ["No reviews provided — cannot detect conflicts."],
            "errors": [],
        }

    prompt = CONFLICT_DETECTION_PROMPT.format(
        pros=json.dumps(state.get("raw_pros", []), ensure_ascii=False, indent=2),
        cons=json.dumps(state.get("raw_cons", []), ensure_ascii=False, indent=2),
        reviews=_fmt_reviews(reviews),
    )
    raw = _call_llm(prompt)
    result = _parse_json(raw, default={"disagreements": [], "unknowns": []})

    disagreements = result.get("disagreements", []) if isinstance(result, dict) else []
    unknowns      = result.get("unknowns", [])      if isinstance(result, dict) else []

    logger.info("conflict_node: %d disagreements, %d unknowns.", len(disagreements), len(unknowns))
    return {"disagreements": disagreements, "unknowns": unknowns, "errors": []}


# ─── Node 5: Summary Generator ───────────────────────────────────────────────

def summary_node(state: VerdictState) -> dict:
    reviews = state.get("reviews", [])
    pros    = state.get("raw_pros", [])
    cons    = state.get("raw_cons", [])
    disag   = state.get("disagreements", [])
    unkn    = state.get("unknowns", [])

    if not reviews:
        return {
            "summary_en": "I don't know — no reviews were provided.",
            "summary_ar": "لا أعلم — لم يتم تقديم أي مراجعات.",
            "errors": [],
        }

    kwargs = dict(
        pros=_fmt_items(pros),
        cons=_fmt_items(cons),
        disagreements=_fmt_list(disag),
        unknowns=_fmt_list(unkn),
    )

    summary_en = _call_llm(SUMMARY_EN_PROMPT.format(**kwargs))
    summary_ar = _call_llm(SUMMARY_AR_PROMPT.format(**kwargs))

    logger.info("summary_node: EN=%d chars, AR=%d chars.", len(summary_en), len(summary_ar))
    return {"summary_en": summary_en, "summary_ar": summary_ar, "errors": []}


# ─── Node 6: Scoring Engine ──────────────────────────────────────────────────

def scoring_node(state: VerdictState) -> dict:
    pros     = state.get("raw_pros", [])
    cons     = state.get("raw_cons", [])
    reviews  = state.get("reviews", [])
    disag    = state.get("disagreements", [])
    unkn     = state.get("unknowns", [])

    def avg(lst, key):
        vals = [x.get(key, 0) for x in lst if x.get(key) is not None]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    prompt = SCORING_PROMPT.format(
        pros_count=len(pros),
        cons_count=len(cons),
        avg_pro_conf=avg(pros, "confidence"),
        avg_con_conf=avg(cons, "confidence"),
        avg_pro_impact=avg(pros, "rating_impact"),
        avg_con_impact=avg(cons, "rating_impact"),
        disagreements_count=len(disag),
        unknowns_count=len(unkn),
        total_reviews=len(reviews),
    )

    raw = _call_llm(prompt)
    result = _parse_json(raw, default={})

    # ── Deterministic fallback if LLM fails ──────────────────────────────────
    if "rating" not in result or "confidence_score" not in result:
        logger.warning("scoring_node: LLM failed — using deterministic fallback.")
        baseline = 2.5
        shift = (
            sum(p["rating_impact"] * p["confidence"] for p in pros) +
            sum(c["rating_impact"] * c["confidence"] for c in cons)
        )
        rating = max(0.0, min(5.0, round(baseline + shift * 2.5 - len(disag) * 0.1, 2)))
        n = len(reviews)
        conf_base = min(n / 10, 1.0) * (avg(pros + cons, "confidence") or 0.5)
        confidence = max(0.0, min(1.0, round(conf_base - len(disag) * 0.05 - len(unkn) * 0.03, 2)))
        if n == 0:
            rating, confidence = 0.0, 0.0
        elif n < 2:
            confidence = min(confidence, 0.4)
        result = {"rating": rating, "confidence_score": confidence}

    rating = max(0.0, min(5.0, round(float(result.get("rating", 0.0)), 2)))
    conf   = max(0.0, min(1.0, round(float(result.get("confidence_score", 0.0)), 2)))
    logger.info("scoring_node: rating=%.2f, confidence=%.2f", rating, conf)
    return {"rating": rating, "confidence_score": conf, "errors": []}


# ─── Node 7: Validation & Assembly ───────────────────────────────────────────

def validation_node(state: VerdictState) -> dict:
    """Assemble and validate final VerdictOutput. Safe fallback on failure."""
    try:
        output = VerdictOutput(
            summary_en=state.get("summary_en", "I don't know."),
            summary_ar=state.get("summary_ar", "لا أعلم."),
            pros=[ProCon(**p) for p in state.get("raw_pros", [])],
            cons=[ProCon(**c) for c in state.get("raw_cons", [])],
            rating=state.get("rating", 0.0),
            confidence_score=state.get("confidence_score", 0.0),
            disagreements=state.get("disagreements", []),
            unknowns=state.get("unknowns", []),
        )
        return {"verdict": output.model_dump(), "errors": []}

    except Exception as exc:
        logger.error("validation_node: Pydantic validation failed — %s", exc)
        safe = VerdictOutput(
            summary_en="I don't know — validation failed.",
            summary_ar="لا أعلم — فشل التحقق.",
            pros=[], cons=[],
            rating=0.0, confidence_score=0.0,
            disagreements=[],
            unknowns=[f"Validation error: {exc}"],
        )
        return {"verdict": safe.model_dump(), "errors": [str(exc)]}