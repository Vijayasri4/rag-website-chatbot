"""
frontend/frontend.py
--------------------
UI helper functions used by app.py.
Keeps rendering logic separate from app orchestration.
"""
import streamlit as st


def render_user_bubble(text: str):
    st.markdown(
        f'<div class="user-bubble">👤 {text}</div>',
        unsafe_allow_html=True,
    )


def render_bot_bubble(text: str, streaming: bool = False):
    cursor = "▌" if streaming else ""
    st.markdown(
        f'<div class="bot-bubble">🤖 {text}{cursor}</div>',
        unsafe_allow_html=True,
    )


def render_meta(chunks_used: int, latency: float, sources: list[str]):
    badges = (
        f'<div class="meta-row">'
        f'<span class="badge">📚 {chunks_used} chunks used</span>'
        f'<span class="badge">⚡ {latency}s</span>'
        f'</div>'
    )
    if sources:
        source_html = " · ".join(
            f'<span class="source-link">🔗 {s}</span>' for s in sources[:3]
        )
        badges += f'<div style="margin-top:5px">{source_html}</div>'
    st.markdown(badges, unsafe_allow_html=True)


def render_welcome():
    st.markdown("""
<div class="welcome-card">
    <div style="font-size:56px;margin-bottom:12px">🔍</div>
    <h3 style="color:#e2e8f0;margin-bottom:8px">Get Started</h3>
    <p style="color:#94a3b8;font-size:14px">
        Enter any website URL in the sidebar and click<br>
        <b style="color:#a78bfa">⚡ Crawl & Index</b> to begin.
    </p>
</div>
""", unsafe_allow_html=True)


def render_stats(stats: dict, model: str, pages: list[str]):
    st.markdown(f"""
<div class="info-box">
🌐 <b>Source:</b> {stats['source_url'][:40]}…<br>
📄 <b>Pages scraped:</b> {stats['pages_scraped']}<br>
🧩 <b>Chunks indexed:</b> {stats['chunks']}<br>
🤖 <b>Model:</b> {model}
</div>
""", unsafe_allow_html=True)

    with st.expander("📄 Scraped Pages"):
        for p in pages:
            st.markdown(
                f'<div class="source-link">🔗 {p}</div>',
                unsafe_allow_html=True
            )