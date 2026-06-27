import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.history    import (get_all_sessions, get_session_messages,
                             search_history, delete_session, delete_all_history, init_db)
from src.pdf_export import generate_pdf

st.set_page_config(page_title="History — RAG Chatbot", page_icon="🕒", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0f1117;}
[data-testid="stSidebar"]{background:#1a1d2e;border-right:1px solid #2e3150;}
h1,h2,h3{color:#e2e8f0 !important;}
.session-card{background:#1a1d2e;border:1px solid #2e3150;border-radius:10px;padding:14px 18px;margin-bottom:10px;}
.sess-title{font-size:14px;font-weight:600;color:#e2e8f0;}
.sess-sub{font-size:12px;color:#64748b;margin-top:2px;}
.badge{display:inline-block;background:#1e1b4b;border:1px solid #6c63ff;color:#a78bfa;border-radius:20px;padding:2px 9px;font-size:11px;margin-right:4px;}
.q-item{background:#0f1117;border-left:3px solid #6c63ff;padding:8px 12px;margin:6px 0;border-radius:0 6px 6px 0;}
.a-item{background:#0f1117;border-left:3px solid #22c55e;padding:8px 12px;margin:6px 0;border-radius:0 6px 6px 0;font-size:13px;color:#94a3b8;}
.search-result{background:#1a1d2e;border:1px solid #2e3150;border-radius:8px;padding:12px 16px;margin-bottom:8px;}
footer{visibility:hidden;}#MainMenu{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

init_db()
st.markdown("# 🕒 Chat History")
st.markdown("Browse and search all past Q&A sessions.")
st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📋 All Sessions", "🔍 Search"])

# ── Tab 1: All sessions ───────────────────────────────────────────────────────
with tab1:
    sessions = get_all_sessions()
    if not sessions:
        st.info("No chat history yet. Start chatting on the Chat page!")
    else:
        col_top, col_del = st.columns([4,1])
        with col_del:
            if st.button("🗑 Clear All History", type="secondary"):
                delete_all_history()
                st.success("All history deleted.")
                st.rerun()

        # Group by domain
        domains = {}
        for s in sessions:
            dk = s["domain_key"]
            if dk not in domains:
                domains[dk] = []
            domains[dk].append(s)

        for dk, domain_sessions in domains.items():
            url = domain_sessions[0]["source_url"]
            st.markdown(f"### 🌐 {url}")

            for sess in domain_sessions:
                msgs = get_session_messages(sess["id"])
                user_msgs = [m for m in msgs if m["role"] == "user"]
                q_count = len(user_msgs)

                with st.expander(f"💬 Session #{sess['id']} · {q_count} questions · {sess['started_at'][:16]}"):
                    # PDF download for this session
                    if msgs:
                        pdf_bytes = generate_pdf(url, msgs)
                        st.download_button(
                            f"📄 Download PDF",
                            data=pdf_bytes,
                            file_name=f"session_{sess['id']}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{sess['id']}"
                        )

                    # Show Q&A
                    for m in msgs:
                        if m["role"] == "user":
                            st.markdown(f'<div class="q-item">❓ <b>{m["content"]}</b></div>',
                                        unsafe_allow_html=True)
                        else:
                            ans = m["content"][:400] + ("…" if len(m["content"]) > 400 else "")
                            srcs = m.get("sources", "[]")
                            if isinstance(srcs, str):
                                try: srcs = json.loads(srcs)
                                except: srcs = []
                            src_text = f"<br><small>🔗 {srcs[0]}</small>" if srcs else ""
                            st.markdown(f'<div class="a-item">🤖 {ans}{src_text}</div>',
                                        unsafe_allow_html=True)

                    if st.button(f"🗑 Delete Session #{sess['id']}", key=f"del_{sess['id']}"):
                        delete_session(sess["id"])
                        st.rerun()

# ── Tab 2: Search ─────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### 🔍 Search Past Questions")
    query = st.text_input("Search your question history", placeholder="e.g. what is python")

    if query:
        results = search_history(query)
        if not results:
            st.info(f"No questions found matching '{query}'")
        else:
            st.markdown(f"Found **{len(results)}** matching questions:")
            for r in results:
                st.markdown(f"""<div class="search-result">
                    <div style="font-size:13px;color:#e2e8f0;font-weight:500">❓ {r['content']}</div>
                    <div style="font-size:11px;color:#64748b;margin-top:4px">
                        🌐 {r['source_url']} · 📅 {r['created_at'][:16]}
                    </div>
                </div>""", unsafe_allow_html=True)