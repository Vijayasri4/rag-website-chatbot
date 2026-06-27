import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.vector_store import VectorStore
from src.retriever    import retrieve, format_context
from src.llm          import ask_groq, DEFAULT_MODEL
from src.history      import create_session, add_message, get_recent_messages, init_db
from src.pdf_export   import generate_pdf

st.set_page_config(page_title="Chat — RAG Chatbot", page_icon="💬", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0f1117;}
[data-testid="stSidebar"]{background:#1a1d2e;border-right:1px solid #2e3150;}
h1,h2,h3{color:#e2e8f0 !important;}
.user-bubble{background:#6c63ff;color:white;padding:12px 18px;border-radius:18px 18px 4px 18px;
  margin:6px 0 6px 15%;font-size:14px;line-height:1.6;}
.bot-bubble{background:#1e2235;color:#e2e8f0;border:1px solid #2e3150;padding:12px 18px;
  border-radius:18px 18px 18px 4px;margin:6px 15% 6px 0;font-size:14px;line-height:1.7;}
.badge{display:inline-block;background:#1e1b4b;border:1px solid #6c63ff;color:#a78bfa;
  border-radius:20px;padding:2px 9px;font-size:11px;margin-right:4px;}
.src{font-size:11px;color:#64748b;margin-top:4px;}
footer{visibility:hidden;}#MainMenu{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

init_db()
stores = VectorStore.list_all()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💬 Chat Settings")
    if not stores:
        st.warning("No sites indexed. Go to **Crawl & Index** first.")
        st.stop()

    # Build display labels showing full URL
    url_options = {s["source_url"]: s["url_key"] for s in stores}
    
    # Pre-select if coming from another page
    preselect_key = st.session_state.get("selected_url_key", "")
    preselect_url = next((s["source_url"] for s in stores if s["url_key"] == preselect_key), stores[0]["source_url"])
    
    selected_url = st.selectbox(
        "Select website to chat with",
        list(url_options.keys()),
        index=list(url_options.keys()).index(preselect_url),
        format_func=lambda u: u[:60] + "…" if len(u) > 60 else u
    )
    selected_uk = url_options[selected_url]

    top_k = st.slider("Chunks to retrieve", 3, 10, 5)
    model = st.selectbox("Groq Model", [
        "llama-3.3-70b-versatile", "llama-3.1-8b-instant",
        "mixtral-8x7b-32768", "gemma2-9b-it"
    ])

    if st.button("🆕 New Chat Session", use_container_width=True):
        for k in ["chat_session_id", "chat_messages", "chat_url_key"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown("---")
    if st.session_state.get("chat_messages"):
        pdf_bytes = generate_pdf(selected_url, st.session_state["chat_messages"])
        st.download_button("📄 Download PDF", data=pdf_bytes,
                           file_name=f"chat_{selected_uk[:20]}.pdf",
                           mime="application/pdf", use_container_width=True)

# ── Load correct store ────────────────────────────────────────────────────────
try:
    store = VectorStore.load(selected_uk)
except Exception:
    st.error(f"❌ Could not load index for:\n`{selected_url}`\n\nPlease re-crawl it.")
    st.stop()

# ── Reset session when switching sites ────────────────────────────────────────
if st.session_state.get("chat_url_key") != selected_uk:
    st.session_state["chat_messages"]   = []
    st.session_state["chat_session_id"] = create_session(selected_uk, selected_url)
    st.session_state["chat_url_key"]    = selected_uk

session_id = st.session_state["chat_session_id"]
messages   = st.session_state["chat_messages"]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 💬 Chat")
st.markdown(f"Chatting with **{selected_url}** · `{store.stats['chunks']} chunks indexed`")
st.markdown("---")

# ── Show chat messages ────────────────────────────────────────────────────────
if not messages:
    st.markdown("""<div style="text-align:center;color:#64748b;padding:40px;font-size:14px">
        💡 Ask anything about this specific website!
    </div>""", unsafe_allow_html=True)

for msg in messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
        badges = f'<span class="badge">📚 {msg.get("chunks_used",0)} chunks</span>'
        badges += f'<span class="badge">⚡ {msg.get("latency",0)}s</span>'
        srcs = msg.get("sources", [])
        if isinstance(srcs, str):
            try: srcs = json.loads(srcs)
            except: srcs = []
        src_text = " · ".join(srcs[:2]) if srcs else ""
        st.markdown(f'<div>{badges}</div><div class="src">{src_text}</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────────────────────
question = st.chat_input("Ask a question about this website…")

if question:
    messages.append({"role": "user", "content": question})
    add_message(session_id, "user", question)
    st.markdown(f'<div class="user-bubble">👤 {question}</div>', unsafe_allow_html=True)

    chunks  = retrieve(question, store, top_k=top_k)
    sources = list(dict.fromkeys(c["url"] for c in chunks)) if chunks else []
    context = format_context(chunks) if chunks else ""
    history = get_recent_messages(session_id, n=4)

    t0 = time.time()
    answer_box  = st.empty()
    answer_text = ""

    if not chunks:
        answer_text = "I couldn't find relevant content on this website to answer that."
        answer_box.markdown(f'<div class="bot-bubble">🤖 {answer_text}</div>', unsafe_allow_html=True)
    else:
        stream = ask_groq(question, context, model=model, stream=True, history=history)
        for token in stream:
            answer_text += token
            answer_box.markdown(f'<div class="bot-bubble">🤖 {answer_text}▌</div>', unsafe_allow_html=True)
        answer_box.markdown(f'<div class="bot-bubble">🤖 {answer_text}</div>', unsafe_allow_html=True)

    latency = round(time.time() - t0, 2)
    bot_msg = {"role": "assistant", "content": answer_text,
               "sources": sources, "latency": latency, "chunks_used": len(chunks)}
    messages.append(bot_msg)
    add_message(session_id, "assistant", answer_text, sources, latency, len(chunks))

    badges   = f'<span class="badge">📚 {len(chunks)} chunks</span><span class="badge">⚡ {latency}s</span>'
    src_text = " · ".join(sources[:2]) if sources else ""
    st.markdown(f'<div>{badges}</div><div class="src">{src_text}</div>', unsafe_allow_html=True)
    st.session_state["chat_messages"] = messages