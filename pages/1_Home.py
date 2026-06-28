import sys, os, asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.vector_store import VectorStore
from src.history import get_stats, get_all_sessions, get_session_messages, init_db
from src.shared_sidebar import render_sidebar

st.set_page_config(page_title="Home — RAG Chatbot", page_icon="🏠", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0f1117;}
[data-testid="stSidebar"]{background:#1a1d2e;border-right:1px solid #2e3150;}
h1,h2,h3{color:#e2e8f0!important;}
.stat-card{background:#1a1d2e;border:1px solid #2e3150;border-radius:12px;padding:20px;text-align:center;}
.stat-num{font-size:36px;font-weight:700;margin:8px 0;}
.stat-lbl{font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.6px;}
.site-row{background:#1a1d2e;border:1px solid #2e3150;border-radius:10px;padding:14px 16px;margin-bottom:8px;}
.activity-card{background:#1a1d2e;border:1px solid #2e3150;border-radius:10px;padding:12px 16px;margin-bottom:6px;}
.info-box{background:#1a1d2e;border-left:3px solid #6c63ff;border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:10px;font-size:13px;color:#94a3b8;line-height:1.7;}
footer{visibility:hidden;}#MainMenu{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

render_sidebar("Home")
init_db()
stats    = get_stats()
stores   = VectorStore.list_all()
sessions = get_all_sessions()

# ── About section (top of Home) ───────────────────────────────────────────────
st.markdown("# 🤖 RAG Website Chatbot")
st.markdown("**Ask questions about any website. Get accurate answers powered by AI.**")

with st.expander("📖 What is this app? How does it work?", expanded=True):
    st.markdown("""
    <div class="info-box">
    <b style="color:#a78bfa">RAG (Retrieval-Augmented Generation)</b> is an AI technique that:<br><br>
    1. <b style="color:#e2e8f0">Scrapes</b> a website and collects all its text content<br>
    2. <b style="color:#e2e8f0">Splits</b> the content into small searchable chunks<br>
    3. <b style="color:#e2e8f0">Indexes</b> the chunks using TF-IDF vectors for fast search<br>
    4. <b style="color:#e2e8f0">Retrieves</b> the most relevant chunks when you ask a question<br>
    5. <b style="color:#e2e8f0">Generates</b> an answer using Groq LLM — based ONLY on the website content<br><br>
    Unlike ChatGPT which answers from training data, this bot answers <b style="color:#4ade80">only from the website you give it</b> — so answers are always accurate and sourced.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""**🌐 Step 1 — Crawl**
Go to **Crawl & Index**, enter any URL. The bot will visit that page and all linked pages on the same domain.""")
    with col2:
        st.markdown("""**💬 Step 2 — Chat**
Go to **Chat**, select your indexed website from the dropdown, and start asking questions.""")
    with col3:
        st.markdown("""**🕒 Step 3 — History**
Every Q&A is saved. Go to **History** to browse past sessions or download them as PDF.""")

st.markdown("---")

# ── Stats ─────────────────────────────────────────────────────────────────────
st.markdown("### 📊 Your Knowledge Base")
c1,c2,c3,c4 = st.columns(4)
for col, lbl, val, color, hint in [
    (c1, "Sites Indexed",   len(stores),                         "#60a5fa", "websites crawled"),
    (c2, "Total Chunks",    sum(s["chunks"] for s in stores),    "#4ade80", "text segments"),
    (c3, "Questions Asked", stats["total_questions"],             "#a78bfa", "across all sessions"),
    (c4, "Chat Sessions",   stats["total_sessions"],             "#fb923c", "conversations"),
]:
    with col:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-lbl">{lbl}</div>
            <div class="stat-num" style="color:{color}">{val:,}</div>
            <div class="stat-lbl">{hint}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
left, right = st.columns([1.5, 1])

# ── Indexed sites ─────────────────────────────────────────────────────────────
with left:
    st.markdown("### 🌐 Indexed Websites")
    st.markdown("<small style='color:#64748b'>These websites are ready to chat with. No re-crawling needed.</small>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if not stores:
        st.info("No websites indexed yet. Go to **🌐 Crawl & Index** to add your first website.")
    else:
        for s in stores:
            st.markdown(f"""<div class="site-row">
                <div style="font-size:13px;font-weight:500;color:#e2e8f0;word-break:break-all">🔗 {s['source_url']}</div>
                <div style="font-size:11px;color:#64748b;margin-top:2px">{s['domain_key']}</div>
                <div style="margin-top:8px">
                    <span style="background:#1e1b4b;border:1px solid #6c63ff;color:#a78bfa;border-radius:20px;padding:2px 9px;font-size:11px;margin-right:4px">📄 {s['chunks']} chunks</span>
                    <span style="background:#1e1b4b;border:1px solid #6c63ff;color:#a78bfa;border-radius:20px;padding:2px 9px;font-size:11px">🌐 {s['pages_scraped']} pages crawled</span>
                </div>
            </div>""", unsafe_allow_html=True)

# ── Right col ─────────────────────────────────────────────────────────────────
with right:
    st.markdown("### ⚡ Quick Actions")
    q1,q2 = st.columns(2)
    with q1:
        if st.button("🌐 Crawl New Site", use_container_width=True, key="qa1"):
            st.switch_page("pages/2_Crawl.py")
    with q2:
        if st.button("💬 Start Chatting", use_container_width=True, key="qa2"):
            st.switch_page("pages/3_Chat.py")
    q3,q4 = st.columns(2)
    with q3:
        if st.button("🕒 View History", use_container_width=True, key="qa3"):
            st.switch_page("pages/4_History.py")
    with q4:
        if st.button("🔄 Refresh", use_container_width=True, key="qa4"):
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🕒 Recent Questions")
    recent = []
    for sess in sessions[:10]:
        for m in get_session_messages(sess["id"]):
            if m["role"] == "user":
                recent.append({"q": m["content"], "url": sess["source_url"], "time": m["created_at"]})
    recent = recent[-5:][::-1]
    if not recent:
        st.info("No questions yet. Start chatting!")
    else:
        for r in recent:
            st.markdown(f"""<div class="activity-card">
                <div style="font-size:13px;color:#e2e8f0">❓ {r['q'][:65]}{'...' if len(r['q'])>65 else ''}</div>
                <div style="font-size:11px;color:#64748b;margin-top:3px">🌐 {r['url'][:40]} · {r['time'][:16]}</div>
            </div>""", unsafe_allow_html=True)