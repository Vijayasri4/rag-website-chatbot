"""
chunker.py
----------
Splits raw page text into token-bounded chunks with overlap.
Uses tiktoken (cl100k_base) for accurate token counts.

Tuning for better RAG quality:
  MAX_TOKENS = 200  (smaller chunks = more precise retrieval)
  OVERLAP    = 40   (overlap preserves context at chunk boundaries)
"""
import hashlib
import tiktoken

_ENC = tiktoken.get_encoding("cl100k_base")

MAX_TOKENS = 200   # smaller = more precise semantic match
OVERLAP    = 40    # overlap to avoid cutting sentences mid-thought


def chunk_text(text: str,
               max_tokens: int = MAX_TOKENS,
               overlap: int = OVERLAP) -> list[str]:
    """Split a single text into overlapping token-bounded chunks."""
    tokens = _ENC.encode(text)
    chunks = []
    start  = 0

    while start < len(tokens):
        end   = min(start + max_tokens, len(tokens))
        chunk = _ENC.decode(tokens[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        if end == len(tokens):
            break
        start += max_tokens - overlap

    return chunks


def chunk_documents(docs: list[tuple[str, str]]) -> list[dict]:
    """
    Chunk all scraped documents and deduplicate.

    Args:
        docs: list of (page_url, page_text)

    Returns:
        List of dicts: { 'text': str, 'url': str, 'chunk_id': str }
    """
    seen:   set[str]  = set()
    result: list[dict] = []

    for url, text in docs:
        for chunk in chunk_text(text):
            h = hashlib.md5(chunk.encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                result.append({
                    "text":     chunk,
                    "url":      url,
                    "chunk_id": h,
                })

    return result