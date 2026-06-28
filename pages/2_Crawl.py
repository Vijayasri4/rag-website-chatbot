import sys, os, asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.scraper      import crawl_sync
from src.chunker      import chunk_documents
from src.vector_store import VectorStore
from src.shared_sidebar import render_sidebar

st.set_page_config(page_title="Crawl & Index", page_icon="🌐", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0f1117;}
[data-testid="stSidebar"]{background:#1a1d2e;border-right:1px solid #2e3150;}
h1,h2,h3{color:#e2e8f0!important;}
.site-card{background:#1a1d2e;border:1px solid #2e3150;border-radius:10px;padding:14px 18px;margin-bottom:10px;}
.how-step{background:#1a1d2e;border:1px solid #2e3150;border-radius:8px;padding:12px 16px;margin-bottom:8px;display:flex;gap:12px;align-items:flex-start;}
.step-num{width:28px;height:28px;background:#6c63ff;border-radius:50%;display:grid;place-items:center;font-size:13px;font-weight:700;color:white;flex-shrink:0;margin-top:1px;}
.step-body{font-size:13px;color:#94a3b8;line-height:1.6;}
.step-title{font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:3px;}
footer{visibility:hidden;}#MainMenu{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

render_sidebar("Crawl")

st.markdown("# 🌐 Crawl & Index")
st.markdown("Add any website to your knowledge base. Each URL is stored as a **separate index**.")

# ── How crawling works ────────────────────────────────────────────────────────
with st.expander("ℹ️ How does crawling work?", expanded=False):
    st.markdown("""
    <div style="font-size:13px;color:#94a3b8;line-height:1.8;margin-bottom:12px">
    When you enter a URL and click <b style="color:#e2e8f0">Crawl & Index</b>, here is what happens behind the scenes:
    </div>

    <div class="how-step">
        <div class="step-num">1</div>
        <div class="step-body">
            <div class="step-title">🕷️ Crawl — Visit pages</div>
            The scraper visits your URL and finds all links on the page. It follows only links on the <b style="color:#e2e8f0">same domain and path</b>. For example, if you give <code>w3schools.com/python/</code> it only visits <code>/python/*</code> pages, not <code>/html/</code> or <code>/css/</code>.
        </div>
    </div>
    <div class="how-step">
        <div class="step-num">2</div>
        <div class="step-body">
            <div class="step-title">🧹 Extract — Clean the text</div>
            Navigation bars, footers, ads, scripts, and buttons are removed. Only the actual content (headings, paragraphs, lists, tables) is kept.
        </div>
    </div>
    <div class="how-step">
        <div class="step-num">3</div>
        <div class="step-body">
            <div class="step-title">✂️ Chunk — Split into pieces</div>
            Each page's text is split into <b style="color:#e2e8f0">200-token chunks</b> with a 40-token overlap between them. This ensures no sentence is cut off mid-thought at a boundary.
        </div>
    </div>
    <div class="how-step">
        <div class="step-num">4</div>
        <div class="step-body">
            <div class="step-title">⚡ Embed — Convert to vectors</div>
            Each chunk is converted into a <b style="color:#e2e8f0">TF-IDF vector</b> (an array of numbers representing word importance). This lets the system find relevant chunks instantly using math instead of keyword search.
        </div>
    </div>
    <div class="how-step">
        <div class="step-num">5</div>
        <div class="step-body">
            <div class="step-title">💾 Save — Store to disk</div>
            The chunks and their vectors are saved to <code>data/stores/</code> as a <b style="color:#e2e8f0">unique .pkl file per URL</b>. You never need to re-crawl — just pick the site from the Chat page.
        </div>
    </div>

    <div style="background:#052e16;border:1px solid #22c55e;border-radius:8px;padding:12px 16px;margin-top:8px;font-size:12px;color:#86efac">
    💡 <b>Tip:</b> For best results, give the most specific URL possible.<br>
    e.g. <code>https://en.wikipedia.org/wiki/Python_(programming_language)</code> instead of <code>https://en.wikipedia.org</code>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
left, right = st.columns([1.2, 1])

with left:
    st.markdown("### ➕ Add New Website")
    url = st.text_input("Website URL", placeholder="https://en.wikipedia.org/wiki/Python_(programming_language)")
    c1,c2 = st.columns(2)
    with c1: max_pages = st.number_input("Max pages", 1, 50, 15)
    with c2:
        model = st.selectbox("Groq Model", [
            "llama-3.3-70b-versatile","llama-3.1-8b-instant",
            "mixtral-8x7b-32768","gemma2-9b-it"])
    st.session_state["groq_model"] = model

    if url and VectorStore.exists_url(url):
        st.warning("⚠️ This URL is already indexed. Crawling again will overwrite it.")

    if st.button("⚡ Crawl & Index", type="primary", use_container_width=True):
        if not url:
            st.error("Please enter a URL.")
        else:
            progress = st.progress(0, text="Starting crawler…")
            status   = st.empty()

            def on_progress(cur, total, page_url):
                pct   = min(int(cur / max(total,1) * 88), 88)
                short = page_url[:55]+"…" if len(page_url)>55 else page_url
                progress.progress(pct, text=f"Page {cur}: {short}")

            try:
                status.info("🕷️ Crawling… JS-heavy sites may take 30–60 seconds.")
                docs = crawl_sync(url, max_pages=max_pages, progress_callback=on_progress)
                if not docs:
                    st.error("❌ No content scraped. Site may block bots.\nTry: `playwright install chromium`")
                    st.stop()

                progress.progress(92, text="Chunking text…")
                status.info("✂️ Splitting into 200-token chunks…")
                chunks = chunk_documents(docs)

                progress.progress(96, text="Building vector index…")
                status.info("⚡ Building TF-IDF vector index…")
                store = VectorStore()
                store.build(chunks, source_url=url, pages=len(docs))
                store.save()

                progress.progress(100, text="Done!")
                status.success(f"✅ Indexed **{len(docs)} pages** → **{len(chunks)} chunks** ready to chat!")

                with st.expander("📄 Pages scraped"):
                    for d in docs:
                        st.markdown(f"🔗 {d[0]}")
            except Exception as e:
                st.error(f"❌ Error: {e}")

with right:
    st.markdown("### 📚 All Indexed Sites")
    st.markdown("<small style='color:#64748b'>Click Chat to start asking questions about any site.</small>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    stores = VectorStore.list_all()
    if not stores:
        st.info("No sites indexed yet.")
    else:
        for s in stores:
            st.markdown(f"""<div class="site-card">
                <div style="font-size:13px;font-weight:500;color:#e2e8f0;word-break:break-all">🌐 {s['source_url']}</div>
                <div style="margin-top:6px">
                    <span style="background:#1e1b4b;border:1px solid #6c63ff;color:#a78bfa;border-radius:20px;padding:2px 9px;font-size:11px;margin-right:4px">{s['chunks']} chunks</span>
                    <span style="background:#1e1b4b;border:1px solid #6c63ff;color:#a78bfa;border-radius:20px;padding:2px 9px;font-size:11px">{s['pages_scraped']} pages</span>
                </div>
            </div>""", unsafe_allow_html=True)
            ca,cb = st.columns(2)
            with ca:
                if st.button("💬 Chat", key=f"ch_{s['url_key']}", use_container_width=True):
                    st.session_state["selected_url_key"] = s["url_key"]
                    st.switch_page("pages/3_Chat.py")
            with cb:
                if st.button("🗑 Delete", key=f"dl_{s['url_key']}", use_container_width=True):
                    VectorStore.delete(s["url_key"]); st.rerun()