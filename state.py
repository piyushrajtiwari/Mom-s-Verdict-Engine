"""
state.py — LangGraph State + Pydantic Output Schemas
"""

from __future__ import annotations
from typing import Annotated, TypedDict
import operator
from pydantic import BaseModel, Field, field_validator


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class ProCon(BaseModel):
    aspect: str = Field(..., description="Feature/aspect being discussed")
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: str = Field(..., description="Near-verbatim snippet from reviews")
    rating_impact: float = Field(..., ge=-1.0, le=1.0)

    @field_validator("confidence", "rating_impact")
    @classmethod
    def round_f(cls, v: float) -> float:
        return round(v, 3)


class VerdictOutput(BaseModel):
    summary_en: str
    summary_ar: str
    pros: list[ProCon] = Field(default_factory=list)
    cons: list[ProCon] = Field(default_factory=list)
    rating: float = Field(..., ge=0.0, le=5.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    disagreements: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)

    @field_validator("rating", "confidence_score")
    @classmethod
    def round_s(cls, v: float) -> float:
        return round(v, 2)


# ─── LangGraph State ──────────────────────────────────────────────────────────

class VerdictState(TypedDict):
    reviews:            list[str]
    retrieved_context:  str
    review_chunks:      list[str]
    raw_pros:           list[dict]
    raw_cons:           list[dict]
    disagreements:      list[str]
    unknowns:           list[str]
    summary_en:         str
    summary_ar:         str
    rating:             float
    confidence_score:   float
    verdict:            dict
    errors:             Annotated[list[str], operator.add]