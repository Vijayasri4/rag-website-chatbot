import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.scraper      import crawl_sync
from src.chunker      import chunk_documents
from src.vector_store import VectorStore

st.set_page_config(page_title="Crawl & Index", page_icon="🌐", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0f1117;}
[data-testid="stSidebar"]{background:#1a1d2e;border-right:1px solid #2e3150;}
h1,h2,h3{color:#e2e8f0 !important;}
.site-card{background:#1a1d2e;border:1px solid #2e3150;border-radius:10px;padding:14px 18px;margin-bottom:10px;}
.site-url{font-size:13px;font-weight:500;color:#e2e8f0;word-break:break-all;}
.site-sub{font-size:12px;color:#64748b;margin-top:3px;}
.site-badge{display:inline-block;background:#1e1b4b;border:1px solid #6c63ff;color:#a78bfa;border-radius:20px;padding:2px 9px;font-size:11px;margin-right:4px;margin-top:5px;}
footer{visibility:hidden;}#MainMenu{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🌐 Crawl & Index")
st.markdown("Each URL is saved as a **separate index** — even multiple pages from the same domain.")
st.markdown("---")

left, right = st.columns([1.2, 1])

with left:
    st.markdown("### ➕ Add New Website")
    url = st.text_input("Website URL", placeholder="https://en.wikipedia.org/wiki/Python_(programming_language)")
    col1, col2 = st.columns(2)
    with col1:
        max_pages = st.number_input("Max pages", 1, 50, 15)
    with col2:
        model = st.selectbox("Groq Model", [
            "llama-3.3-70b-versatile", "llama-3.1-8b-instant",
            "mixtral-8x7b-32768", "gemma2-9b-it"
        ])
    st.session_state["groq_model"] = model

    # Warn if already indexed
    if url and VectorStore.exists_url(url):
        st.warning("⚠️ This URL is already indexed. Crawling again will overwrite it.")

    crawl_btn = st.button("⚡ Crawl & Index", type="primary", use_container_width=True)

    if crawl_btn and url:
        progress = st.progress(0, text="Starting crawler…")
        status   = st.empty()
        scraped  = []

        def on_progress(cur, total, page_url):
            scraped.append(page_url)
            pct = min(int(cur / max(total, 1) * 88), 88)
            short = page_url[:55] + "…" if len(page_url) > 55 else page_url
            progress.progress(pct, text=f"Page {cur}: {short}")

        try:
            status.info("🕷️ Crawling website…")
            docs = crawl_sync(url, max_pages=max_pages, progress_callback=on_progress)

            if not docs:
                st.error("❌ No content scraped. Site may block bots or require JavaScript.\nTry: playwright install chromium")
                st.stop()

            progress.progress(92, text="Chunking text…")
            status.info("✂️ Splitting into chunks…")
            chunks = chunk_documents(docs)

            progress.progress(96, text="Building vector index…")
            status.info("⚡ Building vector index…")
            store = VectorStore()
            store.build(chunks, source_url=url, pages=len(docs))
            store.save()

            progress.progress(100, text="Done!")
            status.success(f"✅ Indexed **{len(docs)} pages** → **{len(chunks)} chunks**")
            st.info(f"🔑 Saved as: `{store.url_key}`")

            with st.expander("📄 Pages scraped"):
                for d in docs:
                    st.markdown(f"🔗 {d[0]}")

        except Exception as e:
            st.error(f"❌ Error: {e}")

with right:
    st.markdown("### 📚 All Indexed Sites")
    stores = VectorStore.list_all()

    if not stores:
        st.info("No sites indexed yet.")
    else:
        for s in stores:
            with st.container():
                st.markdown(f"""<div class="site-card">
                    <div class="site-url">🌐 {s['source_url']}</div>
                    <div class="site-sub">{s['domain_key']}</div>
                    <div>
                        <span class="site-badge">{s['chunks']} chunks</span>
                        <span class="site-badge">{s['pages_scraped']} pages</span>
                    </div>
                </div>""", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("💬 Chat", key=f"ch_{s['url_key']}", use_container_width=True):
                        st.session_state["selected_url_key"] = s["url_key"]
                        st.switch_page("pages/3_Chat.py")
                with c2:
                    if st.button("🗑 Delete", key=f"del_{s['url_key']}", use_container_width=True):
                        VectorStore.delete(s["url_key"])
                        st.rerun()