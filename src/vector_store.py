"""
vector_store.py
---------------
In-memory vector store.
Wraps Embedder + chunk list into a single persistent object
stored in Streamlit session_state.
"""
import pickle
import os
from pathlib import Path

from src.embedder import Embedder


class VectorStore:
    """
    Stores chunks and their TF-IDF embeddings.
    Can be serialised to disk for persistence across Streamlit reruns.
    """

    def __init__(self):
        self.chunks:   list[dict]  = []   # [{text, url, chunk_id}, ...]
        self.embedder: Embedder    = Embedder()
        self.source_url: str       = ""
        self.pages_scraped: int    = 0
        self._indexed = False

    # ── Build index ───────────────────────────────────────────────────────────
    def build(self, chunks: list[dict], source_url: str, pages: int) -> None:
        """Index a list of chunk dicts."""
        self.chunks      = chunks
        self.source_url  = source_url
        self.pages_scraped = pages
        texts = [c["text"] for c in chunks]
        self.embedder.fit(texts)
        self._indexed = True

    # ── Query ─────────────────────────────────────────────────────────────────
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self._indexed:
            raise RuntimeError("VectorStore is empty. Call build() first.")
        return self.embedder.top_k(query, self.chunks, k=top_k)

    @property
    def is_ready(self) -> bool:
        return self._indexed

    @property
    def stats(self) -> dict:
        return {
            "chunks":        len(self.chunks),
            "pages_scraped": self.pages_scraped,
            "source_url":    self.source_url,
        }

    # ── Persistence ───────────────────────────────────────────────────────────
    def save(self, path: str = "data/vector_store.pkl") -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str = "data/vector_store.pkl") -> "VectorStore":
        with open(path, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def exists(path: str = "data/vector_store.pkl") -> bool:
        return os.path.exists(path)