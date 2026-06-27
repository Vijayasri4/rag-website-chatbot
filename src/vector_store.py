"""
vector_store.py
- Key is based on the FULL URL path, not just domain
  so wikipedia.org/wiki/Python and wikipedia.org/wiki/Java are separate stores
- list_all() returns all stores for Home page display
"""
import os, pickle, re, hashlib
from pathlib import Path
from urllib.parse import urlparse
from src.embedder import Embedder

STORE_DIR = Path("data/stores")


def url_key(url: str) -> str:
    """
    Generate a safe unique key from the full URL.
    e.g. https://en.wikipedia.org/wiki/Java_(programming_language)
         → en_wikipedia_org_wiki_Java__programming_language_
    Truncated to 60 chars + 8-char hash suffix to avoid too-long filenames.
    """
    # Normalize
    url = url.rstrip("/").lower()
    parsed = urlparse(url)
    full   = parsed.netloc + parsed.path
    # Make filesystem-safe
    safe   = re.sub(r"[^\w]", "_", full).strip("_")
    # Truncate + add hash suffix to guarantee uniqueness
    suffix = hashlib.md5(url.encode()).hexdigest()[:8]
    key    = safe[:60] + "_" + suffix
    return key


class VectorStore:
    def __init__(self):
        self.chunks        = []
        self.embedder      = Embedder()
        self.source_url    = ""
        self.url_key       = ""
        self.domain_key    = ""   # kept for backward compat display
        self.pages_scraped = 0
        self._indexed      = False

    def build(self, chunks, source_url, pages):
        self.chunks        = chunks
        self.source_url    = source_url
        self.url_key       = url_key(source_url)
        # Human-readable domain for display only
        parsed = urlparse(source_url)
        self.domain_key    = re.sub(r"[^\w]", "_",
                             parsed.netloc.lower().replace("www.", "")).strip("_")
        self.pages_scraped = pages
        self.embedder.fit([c["text"] for c in chunks])
        self._indexed = True

    def search(self, query, top_k=5):
        if not self._indexed:
            raise RuntimeError("VectorStore not built yet.")
        return self.embedder.top_k(query, self.chunks, k=top_k)

    @property
    def is_ready(self): return self._indexed

    @property
    def stats(self):
        return {
            "chunks":        len(self.chunks),
            "pages_scraped": self.pages_scraped,
            "source_url":    self.source_url,
            "url_key":       self.url_key,
            "domain_key":    self.domain_key,
        }

    # ── Persistence ───────────────────────────────────────────────────────────
    def save(self):
        STORE_DIR.mkdir(parents=True, exist_ok=True)
        path = STORE_DIR / f"{self.url_key}.pkl"
        with open(path, "wb") as f:
            pickle.dump(self, f)
        return path

    @classmethod
    def load(cls, uk: str) -> "VectorStore":
        """Load by url_key."""
        path = STORE_DIR / f"{uk}.pkl"
        if not path.exists():
            raise FileNotFoundError(f"No store found for key: {uk}")
        with open(path, "rb") as f:
            return pickle.load(f)

    @classmethod
    def load_by_url(cls, url: str) -> "VectorStore":
        return cls.load(url_key(url))

    @staticmethod
    def exists_url(url: str) -> bool:
        return (STORE_DIR / f"{url_key(url)}.pkl").exists()

    @staticmethod
    def delete(uk: str):
        p = STORE_DIR / f"{uk}.pkl"
        if p.exists():
            p.unlink()

    @staticmethod
    def list_all() -> list[dict]:
        """Return metadata for every saved store, sorted newest first."""
        if not STORE_DIR.exists():
            return []
        result = []
        for pkl in sorted(STORE_DIR.glob("*.pkl"),
                          key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(pkl, "rb") as f:
                    vs = pickle.load(f)
                # Handle old stores that don't have url_key
                uk = getattr(vs, "url_key", None) or getattr(vs, "domain_key", pkl.stem)
                result.append({
                    "url_key":       uk,
                    "domain_key":    getattr(vs, "domain_key", uk),
                    "source_url":    vs.source_url,
                    "chunks":        len(vs.chunks),
                    "pages_scraped": vs.pages_scraped,
                })
            except Exception:
                continue
        return result