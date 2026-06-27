import streamlit as st

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stSidebar"] { background: #1a1d2e; border-right: 1px solid #2e3150; }
[data-testid="stSidebarNav"] a { color: #94a3b8 !important; }
[data-testid="stSidebarNav"] a:hover { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] .stMarkdown p { color: #94a3b8; font-size: 12px; }
h1,h2,h3 { color: #e2e8f0 !important; }
.stButton > button { background: #6c63ff; color: white; border: none; border-radius: 8px; }
.stButton > button:hover { background: #5a52d5; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
# 🤖 RAG Website Chatbot
**Use the sidebar to navigate between pages.**

| Page | What it does |
|------|-------------|
| 🏠 Home | Overview — stats, indexed sites, recent activity |
| 🌐 Crawl & Index | Add websites to your knowledge base |
| 💬 Chat | Ask questions about any indexed website |
| 🕒 History | Browse and search all past Q&A sessions |
""")