"""
main.py — LangGraph Pipeline for Moms Verdict Engine

Run directly:
    python main.py

Or import:
    from main import run_pipeline
    result = run_pipeline(["Great product!", "المنتج رائع"])
"""

from __future__ import annotations

import json
import logging

from langgraph.graph import StateGraph, START, END

from nodes import (
    rag_node, pros_node, cons_node,
    conflict_node, summary_node,
    scoring_node, validation_node,
)
from state import VerdictState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Build Graph ─────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(VerdictState)

    g.add_node("rag",        rag_node)
    g.add_node("pros",       pros_node)
    g.add_node("cons",       cons_node)
    g.add_node("conflict",   conflict_node)
    g.add_node("summary",    summary_node)
    g.add_node("scoring",    scoring_node)
    g.add_node("validation", validation_node)

    g.add_edge(START,        "rag")
    g.add_edge("rag",        "pros")
    g.add_edge("pros",       "cons")
    g.add_edge("cons",       "conflict")
    g.add_edge("conflict",   "summary")
    g.add_edge("summary",    "scoring")
    g.add_edge("scoring",    "validation")
    g.add_edge("validation", END)

    return g.compile()


# ─── Public API ───────────────────────────────────────────────────────────────

def run_pipeline(reviews: list[str]) -> dict:
    """
    Run the full Moms Verdict Engine pipeline.

    Args:
        reviews: list of raw review strings (EN, AR, or mixed)

    Returns:
        VerdictOutput as a JSON-serialisable dict
    """
    if not isinstance(reviews, list):
        raise TypeError("reviews must be a list of strings")

    clean = [str(r).strip() for r in reviews if str(r).strip()]
    logger.info("▶ Pipeline starting — %d reviews", len(clean))

    app = build_graph()

    initial_state: VerdictState = {
        "reviews":           clean,
        "retrieved_context": "",
        "review_chunks":     [],
        "raw_pros":          [],
        "raw_cons":          [],
        "disagreements":     [],
        "unknowns":          [],
        "summary_en":        "",
        "summary_ar":        "",
        "rating":            0.0,
        "confidence_score":  0.0,
        "verdict":           {},
        "errors":            [],
    }

    final_state = app.invoke(initial_state)
    verdict = final_state.get("verdict", {})
    errors  = final_state.get("errors", [])

    if errors:
        logger.warning("Pipeline completed with errors: %s", errors)
    else:
        logger.info("✅ Pipeline complete. Rating=%.2f, Confidence=%.2f",
                    verdict.get("rating", 0), verdict.get("confidence_score", 0))
    return verdict


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = [
        "This product is absolutely amazing! Battery lasts forever.",
        "المنتج رائع جداً، البطارية تدوم طويلاً والشاشة جميلة.",
        "Decent quality but the customer service is terrible.",
        "Battery dies in 2 hours. Very disappointed.",
        "Great screen, poor build quality. Mixed feelings.",
        "لا أوصي بهذا المنتج. الجودة سيئة للغاية.",
    ]

    result = run_pipeline(sample)
    print(json.dumps(result, ensure_ascii=False, indent=2))