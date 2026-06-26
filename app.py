import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import time
import streamlit as st
from dotenv import load_dotenv

from src.scraper      import crawl_sync
from src.chunker      import chunk_documents
from src.vector_store import VectorStore
from src.chatbot      import rag_chat, ChatMessage
from src.llm          import DEFAULT_MODEL

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Website Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global */
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stSidebar"] { background: #1a1d2e; border-right: 1px solid #2e3150; }

/* Chat message area */
.chat-container { max-height: 62vh; overflow-y: auto; padding: 8px 0; }

/* User bubble */
.user-bubble {
    background: #6c63ff;
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 6px 0 6px 15%;
    font-size: 15px;
    line-height: 1.6;
    word-wrap: break-word;
}

/* Bot bubble */
.bot-bubble {
    background: #1e2235;
    color: #e2e8f0;
    border: 1px solid #2e3150;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 6px 15% 6px 0;
    font-size: 15px;
    line-height: 1.7;
    word-wrap: break-word;
}

/* Meta badges */
.meta-row { margin-top: 6px; display: flex; gap: 8px; flex-wrap: wrap; }
.badge {
    background: #1e1b4b;
    border: 1px solid #6c63ff;
    color: #a78bfa;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
}

/* Source links */
.source-link {
    font-size: 11px;
    color: #94a3b8;
    word-break: break-all;
}

/* Welcome card */
.welcome-card {
    background: #1a1d2e;
    border: 1px solid #2e3150;
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    margin: 40px auto;
    max-width: 500px;
}

/* Sidebar info box */
.info-box {
    background: #0f1117;
    border: 1px solid #2e3150;
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 12px;
    color: #94a3b8;
    line-height: 1.8;
}

/* Hide Streamlit branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ─────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "vector_store": None,
        "messages":     [],        # list[ChatMessage]
        "ingesting":    False,
        "pages":        [],
        "model":        DEFAULT_MODEL,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 RAG Chatbot")
    st.markdown("---")

    # URL input
    st.markdown("### 🔗 Data Source")
    url = st.text_input("Website URL", placeholder="https://example.com",
                        label_visibility="collapsed")

    col1, col2 = st.columns(2)
    with col1:
        max_pages = st.number_input("Max pages", min_value=1, max_value=50, value=15)
    with col2:
        top_k = st.number_input("Top-K chunks", min_value=1, max_value=10, value=5)

    # Model selector
    model = st.selectbox("Groq Model", [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ], index=0)
    st.session_state["model"] = model

    ingest_btn = st.button("⚡ Crawl & Index", use_container_width=True,
                            type="primary", disabled=st.session_state["ingesting"])

    # Ingest logic
    if ingest_btn and url:
        st.session_state["ingesting"] = True
        st.session_state["messages"]  = []
        st.session_state["vector_store"] = None

        progress_bar  = st.progress(0, text="Starting crawler…")
        status_text   = st.empty()

        scraped_pages = []

        def on_progress(current, total, page_url):
            scraped_pages.append(page_url)
            pct = min(int(current / max(total, 1) * 90), 90)
            short = page_url[:50] + "…" if len(page_url) > 50 else page_url
            progress_bar.progress(pct, text=f"Scraping page {current}: {short}")

        try:
            # 1. CRAWL
            status_text.info("🕷️ Crawling website…")
            docs = crawl_sync(url, max_pages=max_pages, progress_callback=on_progress)

            if not docs:
                st.error(
                    "❌ No content could be scraped from this URL.\n\n"
                    "Possible reasons:\n"
                    "- The site blocks bots (Cloudflare, captcha, JS-only rendering)\n"
                    "- The URL is incorrect or the site is down\n"
                    "- The site requires login\n\n"
                    "Try a different URL like https://en.wikipedia.org/wiki/Python_(programming_language)"
                )
                st.session_state["ingesting"] = False
                st.stop()

            # 2. CHUNK
            progress_bar.progress(92, text="Chunking text…")
            status_text.info("✂️ Splitting into chunks…")
            chunks = chunk_documents(docs)

            # 3. EMBED & INDEX
            progress_bar.progress(96, text="Building semantic vector index…")
            status_text.info("🧠 Building Sentence Embedding index… (first run downloads ~80MB model)")
            store = VectorStore()
            store.build(chunks, source_url=url, pages=len(docs))
            store.save()

            st.session_state["vector_store"] = store
            st.session_state["pages"]        = [d[0] for d in docs]

            progress_bar.progress(100, text="Done!")
            status_text.success(
                f"✅ Indexed **{len(docs)} pages** → **{len(chunks)} chunks**"
            )

        except Exception as e:
            st.error(f"❌ Error: {e}")
        finally:
            st.session_state["ingesting"] = False

    # Show index stats
    if st.session_state["vector_store"] is not None:
        store = st.session_state["vector_store"]
        stats = store.stats
        st.markdown("---")
        st.markdown("### 📊 Index Stats")
        st.markdown(f"""
<div class="info-box">
🌐 <b>Source:</b> {stats['source_url'][:40]}…<br>
📄 <b>Pages scraped:</b> {stats['pages_scraped']}<br>
🧩 <b>Chunks indexed:</b> {stats['chunks']}<br>
🤖 <b>Model:</b> {model}
</div>
""", unsafe_allow_html=True)

        with st.expander("📄 Scraped Pages"):
            for p in st.session_state["pages"]:
                st.markdown(f"<div class='source-link'>🔗 {p}</div>",
                            unsafe_allow_html=True)

        if st.button("🗑 Clear & Reset", use_container_width=True):
            st.session_state["vector_store"] = None
            st.session_state["messages"]     = []
            st.session_state["pages"]        = []
            st.rerun()

    st.markdown("---")
    st.markdown("""
<div class="info-box">
<b style="color:#a78bfa">RAG Pipeline:</b><br>
🕷️ <b>Crawl</b> — async recursive scraper<br>
✂️ <b>Chunk</b> — 200-token overlapping windows<br>
🧠 <b>Embed</b> — Sentence Transformers (all-MiniLM-L6-v2)<br>
🔍 <b>Retrieve</b> — cosine similarity top-K<br>
💬 <b>Generate</b> — Groq LLM (context-only)
</div>
""", unsafe_allow_html=True)


# ── MAIN CHAT AREA ─────────────────────────────────────────────────────────────
st.markdown("# 🤖 RAG Website Chatbot")
st.markdown("Ask anything about any website. Powered by **Groq** + **Sentence Transformer RAG**.")
st.markdown("---")

store: VectorStore | None = st.session_state["vector_store"]

# ── Welcome screen ─────────────────────────────────────────────────────────────
if store is None:
    st.markdown("""
<div class="welcome-card">
    <div style="font-size:56px;margin-bottom:12px">🔍</div>
    <h3 style="color:#e2e8f0;margin-bottom:8px">Get Started</h3>
    <p style="color:#94a3b8;font-size:14px">
        Enter any website URL in the sidebar and click<br>
        <b style="color:#a78bfa">⚡ Crawl & Index</b> to begin.
    </p>
    <div style="margin-top:20px;font-size:12px;color:#64748b">
        The bot will scrape the site, chunk the content,<br>
        build a vector index, and answer your questions.
    </div>
</div>
""", unsafe_allow_html=True)
    st.stop()


# ── Chat history ───────────────────────────────────────────────────────────────
messages: list[ChatMessage] = st.session_state["messages"]

if not messages:
    st.markdown("""
<div style="text-align:center;color:#64748b;padding:32px 0;font-size:14px">
    💡 Website indexed! Ask your first question below.
</div>
""", unsafe_allow_html=True)

for msg in messages:
    if msg.role == "user":
        st.markdown(
            f'<div class="user-bubble">👤 {msg.content}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="bot-bubble">🤖 {msg.content}</div>',
            unsafe_allow_html=True
        )
        # Meta badges
        badges = (
            f'<div class="meta-row">'
            f'<span class="badge">📚 {msg.chunks_used} chunks used</span>'
            f'<span class="badge">⚡ {msg.latency}s</span>'
            f'</div>'
        )
        if msg.sources:
            source_html = " · ".join(
                f'<span class="source-link">🔗 {s}</span>' for s in msg.sources[:3]
            )
            badges += f'<div style="margin-top:5px">{source_html}</div>'
        st.markdown(badges, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)


# ── Chat input ────────────────────────────────────────────────────────────────
question = st.chat_input("Ask a question about the website…")

if question:
    # Add user message
    user_msg = ChatMessage(role="user", content=question)
    st.session_state["messages"].append(user_msg)

    # Display user bubble immediately
    st.markdown(
        f'<div class="user-bubble">👤 {question}</div>',
        unsafe_allow_html=True
    )

    # Stream bot response
    t0 = time.time()
    answer_placeholder = st.empty()
    answer_text = ""

    with st.spinner("🤖 Thinking…"):
        from src.retriever import retrieve, format_context
        from src.llm import ask_groq

        chunks = retrieve(question, store, top_k=int(top_k))
        sources = list(dict.fromkeys(c["url"] for c in chunks))

        if not chunks:
            answer_text = "I couldn't find relevant content on the website to answer that."
            answer_placeholder.markdown(
                f'<div class="bot-bubble">🤖 {answer_text}</div>',
                unsafe_allow_html=True
            )
        else:
            context = format_context(chunks)
            stream  = ask_groq(question, context, model=model, stream=True)

            for token in stream:
                answer_text += token
                answer_placeholder.markdown(
                    f'<div class="bot-bubble">🤖 {answer_text}▌</div>',
                    unsafe_allow_html=True
                )

            # Final render without cursor
            answer_placeholder.markdown(
                f'<div class="bot-bubble">🤖 {answer_text}</div>',
                unsafe_allow_html=True
            )

    latency = round(time.time() - t0, 2)

    # Save bot message to history
    bot_msg = ChatMessage(
        role        = "assistant",
        content     = answer_text,
        sources     = sources if chunks else [],
        latency     = latency,
        chunks_used = len(chunks),
    )
    st.session_state["messages"].append(bot_msg)

    # Show meta after streaming
    badges = (
        f'<div class="meta-row">'
        f'<span class="badge">📚 {len(chunks)} chunks used</span>'
        f'<span class="badge">⚡ {latency}s</span>'
        f'</div>'
    )
    if sources:
        source_html = " · ".join(
            f'<span class="source-link">🔗 {s}</span>' for s in sources[:3]
        )
        badges += f'<div style="margin-top:5px">{source_html}</div>'
    st.markdown(badges, unsafe_allow_html=True)
