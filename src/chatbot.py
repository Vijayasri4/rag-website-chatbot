"""
chatbot.py
----------
RAG orchestrator — ties retrieval and generation together.
Called by the Streamlit app for every user message.
"""
import time
from dataclasses import dataclass, field

from src.retriever   import retrieve, format_context
from src.llm         import ask_groq, DEFAULT_MODEL
from src.vector_store import VectorStore


@dataclass
class ChatMessage:
    role:    str          # "user" | "assistant"
    content: str
    sources: list[str]    = field(default_factory=list)
    latency: float        = 0.0
    chunks_used: int      = 0


def rag_chat(
    question: str,
    store: VectorStore,
    history: list[ChatMessage],
    model: str = DEFAULT_MODEL,
    top_k: int = 5,
    stream: bool = True,
):
    """
    Full RAG pipeline for a single turn.

    Args:
        question  : user's question
        store     : populated VectorStore
        history   : previous ChatMessage list (for context display)
        model     : Groq model to use
        top_k     : number of chunks to retrieve
        stream    : whether to stream the answer

    Yields (stream=True):
        str tokens as they arrive from Groq

    Returns (stream=False):
        ChatMessage with answer, sources, latency
    """
    t0 = time.time()

    # ── 1. RETRIEVE ───────────────────────────────────────────────────────────
    chunks = retrieve(question, store, top_k=top_k)

    if not chunks:
        no_answer = "I couldn't find relevant content on the scraped website to answer that."
        if stream:
            yield no_answer
            return
        return ChatMessage(
            role="assistant",
            content=no_answer,
            sources=[],
            latency=round(time.time() - t0, 2),
            chunks_used=0,
        )

    # ── 2. AUGMENT ────────────────────────────────────────────────────────────
    context = format_context(chunks)
    sources = list(dict.fromkeys(c["url"] for c in chunks))  # deduplicated

    # ── 3. GENERATE ───────────────────────────────────────────────────────────
    if stream:
        # Yield tokens; caller assembles and stores final ChatMessage
        yield from ask_groq(question, context, model=model, stream=True)
        return

    answer = ask_groq(question, context, model=model, stream=False)
    latency = round(time.time() - t0, 2)

    return ChatMessage(
        role        = "assistant",
        content     = answer,
        sources     = sources,
        latency     = latency,
        chunks_used = len(chunks),
    )