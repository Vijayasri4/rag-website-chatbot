"""
retriever.py
------------
Retrieval layer — queries the VectorStore and returns
the most relevant chunks for a given user question.
"""
from src.vector_store import VectorStore

TOP_K      = 5
MIN_SCORE  = 0.01


def retrieve(query: str, store: VectorStore,
             top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks for *query*.

    Returns:
        List of chunk dicts with keys: text, url, chunk_id, score
        Sorted descending by relevance score.
    """
    if not store.is_ready:
        return []

    results = store.search(query, top_k=top_k)

    # Sort by score descending (already sorted, but be explicit)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def format_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a single context string for the LLM.
    Includes source URL for grounding.
    """
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Chunk {i} | Source: {c['url']} | Relevance: {c['score']:.2f}]\n"
            f"{c['text']}"
        )
    return "\n\n" + ("-" * 60 + "\n\n").join(parts)