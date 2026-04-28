"""
config.py — Centralised configuration loader.
Reads from .env using python-dotenv.
Import this module FIRST in any file that needs settings.
"""

import os
from dotenv import load_dotenv

# Load .env from project root (works from any working directory)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"\n\n❌  Missing environment variable: {key}\n"
            f"    → Copy .env.example to .env and set your Groq API key.\n"
        )
    return val


# ── Settings ──────────────────────────────────────────────────────────────────

GROQ_API_KEY: str = _require("GROQ_API_KEY")

# llama-3.3-70b-versatile supports multilingual (EN + AR) well
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Sentence-transformers model for multilingual embeddings
EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"

# RAG settings
RAG_TOP_K: int = 10
RAG_CHUNK_MAX_CHARS: int = 300