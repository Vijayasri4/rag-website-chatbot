import streamlit as st
from src.vector_store import VectorStore
from src.history import get_stats, init_db

def render_sidebar(active: str = ""):
    init_db()
    stores = VectorStore.list_all()
    stats  = get_stats()

    with st.sidebar:
        st.markdown("""
        <style>
        [data-testid="stSidebarNav"]         { display:none !important; }
        [data-testid="stSidebarNavItems"]    { display:none !important; }
        [data-testid="stSidebarNavSeparator"]{ display:none !important; }
        [data-testid="stSidebar"] > div:first-child { padding-top: 12px; }
        [data-testid="stSidebar"] button {
            background: transparent !important;
            border: none !important;
            color: #94a3b8 !important;
            text-align: left !important;
            padding: 0 !important;
            font-size: 13px !important;
            margin: 0 !important;
            width: 100% !important;
            box-shadow: none !important;
        }
        [data-testid="stSidebar"] button:hover { color:#e2e8f0 !important; }
        [data-testid="stSidebar"] button p { font-size:13px !important; }
        </style>
        """, unsafe_allow_html=True)

        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:4px 0 14px">
            <div style="width:38px;height:38px;background:#6c63ff;border-radius:10px;
                        display:grid;place-items:center;font-size:22px;flex-shrink:0">🤖</div>
            <div>
                <div style="font-size:15px;font-weight:700;color:#e2e8f0">RAG Chatbot</div>
                <div style="font-size:11px;color:#64748b">AI-Powered Website Q&A</div>
            </div>
        </div>
        <hr style="border-color:#2e3150;margin:0 0 12px">
        """, unsafe_allow_html=True)

        # ── Navigation ────────────────────────────────────────────────────────
        st.markdown("<div style='font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px'>Menu</div>", unsafe_allow_html=True)

        pages = [
            ("🏠", "Home",          "pages/1_Home.py"),
            ("🌐", "Crawl & Index", "pages/2_Crawl.py"),
            ("💬", "Chat",          "pages/3_Chat.py"),
            ("🕒", "History",       "pages/4_History.py"),
        ]
        for icon, label, path in pages:
            is_active = label.split()[0] in active or active in label
            bg    = "#2a2d4a" if is_active else "transparent"
            color = "#a78bfa" if is_active else "#94a3b8"
            bdr   = "1px solid #6c63ff" if is_active else "1px solid transparent"
            st.markdown(f"""
            <div style="background:{bg};border:{bdr};border-radius:8px;
                padding:8px 12px;margin-bottom:3px;display:flex;align-items:center;gap:8px">
                <span style="font-size:15px">{icon}</span>
                <span style="font-size:13px;color:{color};font-weight:{'600' if is_active else '400'}">{label}</span>
            </div>""", unsafe_allow_html=True)
            if st.button(label, key=f"nav_{label}", use_container_width=True):
                st.switch_page(path)

        st.markdown("<hr style='border-color:#2e3150;margin:10px 0'>", unsafe_allow_html=True)

        # ── Stats ─────────────────────────────────────────────────────────────
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div style="background:#1a1d2e;border:1px solid #2e3150;
                border-radius:8px;padding:10px;text-align:center">
                <div style="font-size:22px;font-weight:700;color:#60a5fa">{len(stores)}</div>
                <div style="font-size:10px;color:#64748b">Sites</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div style="background:#1a1d2e;border:1px solid #2e3150;
                border-radius:8px;padding:10px;text-align:center">
                <div style="font-size:22px;font-weight:700;color:#4ade80">{stats['total_questions']}</div>
                <div style="font-size:10px;color:#64748b">Questions</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#2e3150;margin:10px 0'>", unsafe_allow_html=True)

        # ── Page-specific contextual info ─────────────────────────────────────
        if "Home" in active:
            st.markdown("""
            <div style="font-size:11px;color:#94a3b8;line-height:1.8">
            <b style="color:#a78bfa;font-size:12px">📋 What's on this page?</b><br><br>
            • <b style="color:#e2e8f0">Stats panel</b> — total sites, chunks, questions and sessions at a glance<br>
            • <b style="color:#e2e8f0">Indexed websites</b> — all crawled sites with chunk and page counts<br>
            • <b style="color:#e2e8f0">Quick actions</b> — jump to Crawl, Chat or History in one click<br>
            • <b style="color:#e2e8f0">Recent questions</b> — last 5 questions asked across all sessions<br><br>
            <b style="color:#a78bfa;font-size:12px">💡 What is RAG?</b><br><br>
            RAG stands for <b style="color:#e2e8f0">Retrieval-Augmented Generation</b>. Instead of the AI answering from its training data, it first <b style="color:#e2e8f0">searches your website content</b> and answers only from what it finds — making answers accurate and sourced.
            </div>
            """, unsafe_allow_html=True)

        elif "Crawl" in active:
            st.markdown("""
            <div style="font-size:11px;color:#94a3b8;line-height:1.8">
            <b style="color:#a78bfa;font-size:12px">🕷️ How crawling works</b><br><br>
            <b style="color:#e2e8f0">1. Visit</b> — Opens the URL and reads its HTML<br>
            <b style="color:#e2e8f0">2. Extract</b> — Removes ads, nav, scripts. Keeps only real content<br>
            <b style="color:#e2e8f0">3. Follow links</b> — Visits all linked pages on the same domain/path<br>
            <b style="color:#e2e8f0">4. Chunk</b> — Splits text into 200-token pieces with 40-token overlap<br>
            <b style="color:#e2e8f0">5. Embed</b> — Converts chunks to TF-IDF vectors for fast search<br>
            <b style="color:#e2e8f0">6. Save</b> — Stores each URL as a separate .pkl file in data/stores/<br><br>
            <b style="color:#a78bfa;font-size:12px">💡 Tips</b><br><br>
            • Give a specific URL like <code style="color:#e2e8f0">/wiki/Python</code> not just <code style="color:#e2e8f0">wikipedia.org</code><br>
            • Wikipedia, docs sites work best<br>
            • JS-heavy sites need Playwright: <code style="color:#e2e8f0">playwright install chromium</code>
            </div>
            """, unsafe_allow_html=True)

        elif "Chat" in active:
            st.markdown("""
            <div style="font-size:11px;color:#94a3b8;line-height:1.8">
            <b style="color:#a78bfa;font-size:12px">💬 How Chat works</b><br><br>
            <b style="color:#e2e8f0">1. Select</b> — Pick any indexed website from the dropdown<br>
            <b style="color:#e2e8f0">2. Retrieve</b> — Your question is matched against all chunks using cosine similarity<br>
            <b style="color:#e2e8f0">3. Augment</b> — Top 5 most relevant chunks are injected into the prompt<br>
            <b style="color:#e2e8f0">4. Generate</b> — Groq LLM answers using ONLY those chunks<br>
            <b style="color:#e2e8f0">5. Memory</b> — Last 4 turns are remembered for follow-up questions<br><br>
            <b style="color:#a78bfa;font-size:12px">💡 Tips</b><br><br>
            • Ask specific questions for best results<br>
            • Download your session as PDF from sidebar<br>
            • Switch websites using the dropdown — chat resets automatically
            </div>
            """, unsafe_allow_html=True)

        elif "History" in active:
            st.markdown("""
            <div style="font-size:11px;color:#94a3b8;line-height:1.8">
            <b style="color:#a78bfa;font-size:12px">🕒 How history is stored</b><br><br>
            Every Q&A session is saved permanently in a <b style="color:#e2e8f0">local SQLite database</b> at <code style="color:#e2e8f0">data/history.db</code><br><br>
            The database has two tables:<br>
            • <b style="color:#e2e8f0">sessions</b> — one row per chat session (website, start time)<br>
            • <b style="color:#e2e8f0">messages</b> — every question and answer with timestamp, source URLs, latency<br><br>
            <b style="color:#a78bfa;font-size:12px">📋 What you can do here</b><br><br>
            • Browse all sessions grouped by website<br>
            • Expand any session to read full Q&A<br>
            • Download any session as a PDF report<br>
            • Search across all past questions<br>
            • Delete individual sessions or clear all history
            </div>
            """, unsafe_allow_html=True)

        # ── Indexed sites list ─────────────────────────────────────────────────
        if stores:
            st.markdown("<hr style='border-color:#2e3150;margin:10px 0'>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px'>Indexed Sites</div>", unsafe_allow_html=True)
            for s in stores[:4]:
                url = s["source_url"].replace("https://","").replace("http://","")
                url = url[:30]+"…" if len(url)>30 else url
                st.markdown(f"""<div style="background:#1a1d2e;border:1px solid #2e3150;
                    border-radius:6px;padding:7px 10px;margin-bottom:4px">
                    <div style="font-size:11px;color:#e2e8f0;white-space:nowrap;
                        overflow:hidden;text-overflow:ellipsis">🌐 {url}</div>
                    <div style="font-size:10px;color:#64748b;margin-top:2px">
                        {s['chunks']} chunks · {s['pages_scraped']} pages</div>
                </div>""", unsafe_allow_html=True)
            if len(stores) > 4:
                st.markdown(f"<div style='font-size:10px;color:#64748b;text-align:center'>+{len(stores)-4} more</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#2e3150;margin:10px 0'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:10px;color:#475569;text-align:center'>Powered by Groq · Built with Streamlit</div>", unsafe_allow_html=True)