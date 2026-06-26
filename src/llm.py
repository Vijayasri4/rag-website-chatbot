"""
llm.py
------
Groq LLM client with improved RAG prompt.
"""
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS    = 1024
TEMPERATURE   = 0.0   # fully deterministic for factual Q&A


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Set it in your .env file.")
    return Groq(api_key=api_key)


SYSTEM_PROMPT = """You are a helpful assistant that answers questions using ONLY \
the provided website content chunks below. 

STRICT RULES:
- Use ONLY the information present in the chunks. Never use external knowledge.
- If the chunks contain the answer, give a clear direct answer immediately.
- Do NOT say "I couldn't find" if the answer IS in the chunks.
- Do NOT add disclaimers like "based on the context" — just answer directly.
- If truly not in the chunks, say: "This information is not available on the scraped website."
- Keep answers concise and factual."""


def build_prompt(question: str, context: str) -> str:
    return f"""WEBSITE CONTENT CHUNKS:
{context}

QUESTION: {question}

Answer directly and concisely using only the chunks above:"""


def ask_groq(
    question: str,
    context:  str,
    model:    str  = DEFAULT_MODEL,
    stream:   bool = False,
):
    client   = _get_client()
    prompt   = build_prompt(question, context)
    response = client.chat.completions.create(
        model       = model,
        max_tokens  = MAX_TOKENS,
        temperature = TEMPERATURE,
        stream      = stream,
        messages    = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
    )

    if stream:
        def _gen():
            for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        return _gen()

    return response.choices[0].message.content.strip()