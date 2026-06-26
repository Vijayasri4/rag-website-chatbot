"""
embedder.py
-----------
Sentence-Transformer based dense embedder.
Uses 'all-MiniLM-L6-v2' — small (80MB), fast, and semantically strong.
Downloads once and caches locally. No API key needed.

Why switch from TF-IDF?
  TF-IDF is keyword-based. "What is Python?" won't match a chunk saying
  "Python is a high-level programming language" because the words differ.
  Sentence-transformers encode *meaning*, so semantic queries work correctly.
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = "all-MiniLM-L6-v2"   # 80MB, fast CPU inference, great quality


class Embedder:
    """Encode chunks once at index time; encode queries at retrieval time."""

    def __init__(self, model_name: str = MODEL_NAME):
        self._model  = SentenceTransformer(model_name)
        self._matrix: np.ndarray | None = None
        self._fitted = False

    # ── Indexing ──────────────────────────────────────────────────────────────
    def fit(self, texts: list[str]) -> np.ndarray:
        """
        Encode all chunk texts into dense vectors.
        Returns shape (N, 384) float32 array.
        Called once during ingest.
        """
        self._matrix = self._model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,   # unit vectors → cosine = dot product
        ).astype(np.float32)
        self._fitted = True
        return self._matrix

    @property
    def matrix(self) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Call fit() first.")
        return self._matrix

    # ── Retrieval ─────────────────────────────────────────────────────────────
    def query_vector(self, query: str) -> np.ndarray:
        """Encode a single query string."""
        if not self._fitted:
            raise RuntimeError("Call fit() first.")
        return self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)

    def top_k(self, query: str, chunks: list[dict],
              k: int = 5, min_score: float = 0.20) -> list[dict]:
        """
        Return top-k semantically most relevant chunks for *query*.
        min_score=0.20 filters out truly unrelated chunks.
        """
        q_vec = self.query_vector(query)                        # (1, 384)
        sims  = cosine_similarity(q_vec, self._matrix)[0]      # (N,)
        order = np.argsort(sims)[::-1]

        results = []
        for i in order[:k]:
            if sims[i] >= min_score:
                results.append({**chunks[i], "score": float(sims[i])})
        return results