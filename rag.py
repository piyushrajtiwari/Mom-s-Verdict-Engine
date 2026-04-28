"""
rag.py — Multilingual FAISS RAG using sentence-transformers

Model: paraphrase-multilingual-MiniLM-L12-v2
  → Handles English + Arabic natively in the same embedding space.
  → Downloaded automatically on first run (~120 MB, cached after that).

Fallback: TF-IDF cosine similarity (no external dependencies needed).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Text Helpers ─────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Strip control characters and normalise whitespace."""
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _chunk(review: str, max_chars: int = 300) -> list[str]:
    """
    Split a review into sentence-level chunks.
    Handles both English (. ! ?) and Arabic (؟) sentence endings.
    """
    review = _clean(review)
    if not review:
        return []

    # Split on sentence boundaries (EN + AR)
    sentences = re.split(r"(?<=[.!?؟])\s+", review)
    chunks, current = [], ""

    for sent in sentences:
        if len(current) + len(sent) + 1 <= max_chars:
            current = (current + " " + sent).strip()
        else:
            if current:
                chunks.append(current)
            current = sent[:max_chars]

    if current:
        chunks.append(current)

    return chunks if chunks else [review[:max_chars]]


# ─── RAG Store ────────────────────────────────────────────────────────────────

@dataclass
class ReviewRAG:
    """
    Builds a FAISS index from review chunks using multilingual embeddings.
    Falls back to TF-IDF if FAISS or sentence-transformers are unavailable.
    """

    chunks:      list[str]         = field(default_factory=list)
    _index:      Optional[object]  = field(default=None, repr=False)
    _embedder:   Optional[object]  = field(default=None, repr=False)
    _use_faiss:  bool              = field(default=True,  repr=False)
    _tfidf:      Optional[object]  = field(default=None, repr=False)
    _tfidf_mat:  Optional[object]  = field(default=None, repr=False)

    # ── Public API ────────────────────────────────────────────────────────────

    def build(self, reviews: list[str], embedding_model: str) -> "ReviewRAG":
        """Chunk all reviews and build the index."""
        self.chunks = []
        for rev in reviews:
            self.chunks.extend(_chunk(rev))

        if not self.chunks:
            logger.warning("RAG: No chunks produced — skipping index build.")
            return self

        try:
            self._build_faiss(embedding_model)
        except Exception as exc:
            logger.warning("FAISS/SentenceTransformer unavailable (%s). Using TF-IDF fallback.", exc)
            self._use_faiss = False
            self._build_tfidf()

        return self

    def retrieve(self, query: str = "product quality", top_k: int = 10) -> str:
        """Return top-k chunks joined as a context string."""
        if not self.chunks:
            return ""
        results = self._faiss_query(query, top_k) if self._use_faiss else self._tfidf_query(query, top_k)
        return "\n---\n".join(results)

    # ── FAISS ─────────────────────────────────────────────────────────────────

    def _build_faiss(self, model_name: str):
        import faiss
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", model_name)
        self._embedder = SentenceTransformer(model_name)

        vecs = self._embedder.encode(
            self.chunks,
            convert_to_numpy=True,
            normalize_embeddings=True,   # cosine via inner product
            show_progress_bar=False,
        )
        dim = vecs.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(vecs.astype("float32"))
        logger.info("FAISS index built: %d chunks, dim=%d", len(self.chunks), dim)

    def _faiss_query(self, query: str, top_k: int) -> list[str]:
        q_vec = self._embedder.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        )
        _, ids = self._index.search(
            q_vec.astype("float32"), min(top_k, len(self.chunks))
        )
        return [self.chunks[i] for i in ids[0] if i != -1]

    # ── TF-IDF fallback ───────────────────────────────────────────────────────

    def _build_tfidf(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._tfidf = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=1
        )
        self._tfidf_mat = self._tfidf.fit_transform(self.chunks)
        logger.info("TF-IDF fallback index built: %d chunks", len(self.chunks))

    def _tfidf_query(self, query: str, top_k: int) -> list[str]:
        from sklearn.metrics.pairwise import cosine_similarity
        q_vec = self._tfidf.transform([query])
        sims = cosine_similarity(q_vec, self._tfidf_mat).flatten()
        top_ids = sims.argsort()[::-1][:top_k]
        return [self.chunks[i] for i in top_ids]