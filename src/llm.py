import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS    = 1024
TEMPERATURE   = 0.0

def _client():
    key = os.getenv("GROQ_API_KEY")
    if not key: raise ValueError("GROQ_API_KEY not set in .env")
    return Groq(api_key=key)

SYSTEM = """You are a helpful assistant that answers questions using ONLY the website content provided.
RULES:
- Answer ONLY from the context chunks. Never use outside knowledge.
- If the answer is clearly in the chunks, answer directly and confidently.
- If not found, say: "This information is not available on the scraped website."
- Be concise and factual. No disclaimers."""

def build_prompt(question, context, history=None):
    history_text = ""
    if history:
        history_text = "\n\nCONVERSATION SO FAR:\n"
        for m in history:
            role = "User" if m.get("role") == "user" else "Assistant"
            history_text += f"{role}: {m.get('content','')}\n"
    return f"""WEBSITE CONTENT:
{context}
{history_text}
CURRENT QUESTION: {question}

Answer directly using only the website content above:"""

def ask_groq(question, context, model=DEFAULT_MODEL, stream=False, history=None):
    prompt = build_prompt(question, context, history)
    resp = _client().chat.completions.create(
        model=model, max_tokens=MAX_TOKENS, temperature=TEMPERATURE, stream=stream,
        messages=[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]
    )
    if stream:
        def _gen():
            for chunk in resp:
                d = chunk.choices[0].delta.content
                if d: yield d
        return _gen()
    return resp.choices[0].message.content.strip()