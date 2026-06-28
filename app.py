import sys, asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st

st.set_page_config(page_title="RAG Chatbot", page_icon="🤖", layout="wide")

# Redirect immediately to Home
st.switch_page("pages/1_Home.py")