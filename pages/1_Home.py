import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.vector_store import VectorStore
from src.history import get_stats, get_all_sessions, get_session_messages, init_db

st.set_page_config(page_title="Home — RAG Chatbot", page_icon="🏠", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0f1117;}
[data-testid="stSidebar"]{background:#1a1d2e;border-right:1px solid #2e3150;}
h1,h2,h3{color:#e2e8f0 !important;}
.stat-card{background:#1a1d2e;border:1px solid #2e3150;border-radius:12px;padding:20px;text-align:center;}
.stat-num{font-size:36px;font-weight:700;margin:8px 0;}
.stat-label{font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.6px;}
.site-row{background:#1a1d2e;border:1px solid #2e3150;border-radius:10px;padding:14px 16px;margin-bottom:8px;}
.site-url{font-size:13px;font-weight:500;color:#e2e8f0;word-break:break-all;}
.site-domain{font-size:11px;color:#64748b;margin-top:2px;}
.site-badge{display:inline-block;background:#1e1b4b;border:1px solid #6c63ff;color:#a78bfa;border-radius:20px;padding:2px 9px;font-size:11px;margin-right:4px;margin-top:4px;}
.activity-card{background:#1a1d2e;border:1px solid #2e3150;border-radius:10px;padding:12px 16px;margin-bottom:6px;}
.activity-q{font-size:13px;color:#e2e8f0;}
.activity-meta{font-size:11px;color:#64748b;margin-top:3px;}
footer{visibility:hidden;}#MainMenu{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

init_db()
stats    = get_stats()
stores   = VectorStore.list_all()
sessions = get_all_sessions()

st.markdown("# 🏠 Home Dashboard")
st.markdown("Overview of your RAG knowledge base")
st.markdown("---")

# ── Stat cards ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
cards = [
    (c1, "Sites Indexed",   len(stores),                             "#60a5fa", "websites crawled"),
    (c2, "Total Chunks",    sum(s["chunks"] for s in stores),        "#4ade80", "text segments"),
    (c3, "Questions Asked", stats["total_questions"],                 "#a78bfa", "across all sessions"),
    (c4, "Chat Sessions",   stats["total_sessions"],                  "#fb923c", "conversations"),
]
for col, label, val, color, hint in cards:
    with col:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-num" style="color:{color}">{val:,}</div>
            <div class="stat-label">{hint}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
left, right = st.columns([1.5, 1])

# ── Indexed websites (no Chat button — just info) ─────────────────────────────
with left:
    st.markdown("### 🌐 Indexed Websites")
    if not stores:
        st.info("No websites indexed yet. Go to **Crawl & Index** to add one.")
    else:
        for s in stores:
            st.markdown(f"""<div class="site-row">
                <div class="site-url">🔗 {s['source_url']}</div>
                <div class="site-domain">{s['domain_key']}</div>
                <div style="margin-top:6px">
                    <span class="site-badge">📄 {s['chunks']} chunks</span>
                    <span class="site-badge">🌐 {s['pages_scraped']} pages</span>
                </div>
            </div>""", unsafe_allow_html=True)

# ── Right column ──────────────────────────────────────────────────────────────
with right:
    st.markdown("### ⚡ Quick Actions")
    q1, q2 = st.columns(2)
    with q1:
        if st.button("🌐 Crawl New Site", use_container_width=True):
            st.switch_page("pages/2_Crawl.py")
    with q2:
        if st.button("💬 Start Chatting", use_container_width=True):
            st.switch_page("pages/3_Chat.py")
    q3, q4 = st.columns(2)
    with q3:
        if st.button("🕒 View History", use_container_width=True):
            st.switch_page("pages/4_History.py")
    with q4:
        if st.button("🔄 Refresh", use_container_width=True):
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
                <div class="activity-q">❓ {r['q'][:70]}{'...' if len(r['q'])>70 else ''}</div>
                <div class="activity-meta">🌐 {r['url'][:50]} · {r['time'][:16]}</div>
            </div>""", unsafe_allow_html=True)