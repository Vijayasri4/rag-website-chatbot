# 🤖 RAG Website Chatbot

YOUTUBE VIDEO LINK: https://youtu.be/jvlk7vhArbQ?si=F34-5Y6-pJQGlG1j

An AI-powered chatbot that scrapes any website and answers questions based **only** on the scraped content. Built with **Python**, **Streamlit**, and **Groq LLM** using the **RAG (Retrieval-Augmented Generation)** technique.

---

## 📌 What is RAG?

**RAG (Retrieval-Augmented Generation)** is an AI technique that grounds LLM answers in real content instead of training data.

```
WITHOUT RAG:
  User Question ──► LLM ──► Answer (from training data, may hallucinate)

WITH RAG:
  User Question ──► Search your website content ──► Inject relevant chunks ──► LLM ──► Grounded Answer
```

The bot answers **only from the website you give it** — so answers are always accurate, sourced, and up to date.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STREAMLIT UI (4 Pages)                             │
│                                                                             │
│   🏠 Home Dashboard  │  🌐 Crawl & Index  │  💬 Chat  │  🕒 History        │
│   Stats, sites list  │  Add websites      │  Ask Q&A  │  Past sessions     │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │        RAG PIPELINE          │
                    │                             │
                    │  1. CRAWL   → scraper.py    │
                    │  2. CHUNK   → chunker.py    │
                    │  3. EMBED   → embedder.py   │
                    │  4. STORE   → vector_store  │
                    │  5. RETRIEVE→ retriever.py  │
                    │  6. GENERATE→ llm.py (Groq) │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │          DATA LAYER          │
                    │                             │
                    │  data/stores/*.pkl           │
                    │    └─ one per URL           │
                    │  data/history.db             │
                    │    └─ SQLite chat log        │
                    └─────────────────────────────┘
```

---

## 📁 Project Structure

```
rag-website-chatbot/
│
├── app.py                          ← Entry point — redirects to Home page
│
├── pages/                          ← Streamlit multi-page app (auto-detected)
│   ├── 1_Home.py                   ← Dashboard: stats, indexed sites, recent activity
│   ├── 2_Crawl.py                  ← Crawl & index any website
│   ├── 3_Chat.py                   ← Chat with any indexed website
│   └── 4_History.py                ← Browse, search & export past Q&A sessions
│
├── src/                            ← All backend logic
│   ├── __init__.py
│   ├── scraper.py                  ← 3-tier web crawler (httpx / requests / playwright)
│   ├── chunker.py                  ← Token-aware text splitter (200 tokens, 40 overlap)
│   ├── embedder.py                 ← TF-IDF vectoriser + cosine similarity search
│   ├── vector_store.py             ← Per-URL index manager (saved as .pkl files)
│   ├── retriever.py                ← Top-K chunk retrieval from vector store
│   ├── llm.py                      ← Groq API client with conversational memory
│   ├── chatbot.py                  ← RAG orchestrator (retrieve → augment → generate)
│   ├── history.py                  ← SQLite database for chat session storage
│   ├── pdf_export.py               ← PDF report generator using ReportLab
│   └── shared_sidebar.py           ← Common sidebar UI rendered on all pages
│
├── .streamlit/
│   └── config.toml                 ← Hides Streamlit default nav, sets dark theme
│
├── data/                           ← Auto-created at runtime (do not edit manually)
│   ├── stores/                     ← One .pkl file per indexed URL
│   │   ├── en_wikipedia_org_wiki_Python_abc12345.pkl
│   │   ├── en_wikipedia_org_wiki_Java_xyz98765.pkl
│   │   └── www_w3schools_com_python_def11111.pkl
│   └── history.db                  ← SQLite database (all chat sessions)
│
├── .env                            ← Your API key (never commit this file)
├── .env.example                    ← Template showing required variables
├── requirements.txt                ← Python dependencies
├── .gitignore
└── README.md
```

---

## 🔄 RAG Pipeline — Step by Step

### Step 1 — CRAWL (`scraper.py`)

```
User gives URL:  https://en.wikipedia.org/wiki/Python_(programming_language)
                        │
                        ▼
        Scraper visits the page and reads HTML
                        │
                        ▼
        Extracts all outgoing <a href> links
                        │
              ┌─────────┴──────────────────┐
              ▼                            ▼
   /wiki/Python_syntax  ✅          https://google.com  ❌
   (same domain+path)               (different domain, skipped)
              │
              ▼
   Repeats for every linked page (up to Max Pages limit)
```

**3-Tier Auto-Detection:**
```
Probe the URL first
        │
        ├─ Loads normally?   ──► Tier 1: httpx async (10 concurrent, fastest)
        │
        ├─ Blocked by cookies? ─► Tier 2: requests.Session (cookie warm-up)
        │
        └─ JS / Cloudflare?  ──► Tier 3: Playwright real browser (headless Chromium)
```

> ⚠️ Playwright requires: `pip install playwright` then `playwright install chromium`

---

### Step 2 — CHUNK (`chunker.py`)

```
Full page text (~3000 tokens)
        │
        ▼
Split into overlapping windows:

[Chunk 1: tokens   0─200]
          [Chunk 2: tokens 160─360]   ← 40-token overlap preserves context
                    [Chunk 3: tokens 320─520]
                              [Chunk 4: tokens 480─680]
                                        ...

Each chunk: 200 tokens  (~150 words)
Overlap:     40 tokens  (~30 words)
Duplicates removed with MD5 hash check
```

---

### Step 3 — EMBED (`embedder.py`)

```
"Python is a programming language"  →  [0.0, 0.23, 0.87, 0.0, 0.12, ...]
"Java was created by James Gosling" →  [0.45, 0.0, 0.0, 0.31, 0.67, ...]
"Python syntax uses indentation"    →  [0.0, 0.19, 0.72, 0.0, 0.08, ...]

These vectors capture word importance using TF-IDF.
Similar meaning = similar vectors = found by cosine similarity.
```

**Why TF-IDF instead of neural embeddings?**

| Feature              | TF-IDF (used here)   | Sentence Transformers  |
|----------------------|----------------------|------------------------|
| Indexing speed       | ⚡ Instant            | 🐌 30–60s for 500 chunks |
| Model download       | None                 | ~80MB                  |
| Works offline        | ✅ Yes               | ✅ Yes                 |
| Semantic matching    | Keyword-based        | Meaning-based          |
| RAM usage            | Minimal              | High                   |

---

### Step 4 — STORE (`vector_store.py`)

```
Each URL gets its OWN isolated .pkl file:

data/stores/
├── en_wikipedia_org_wiki_Python_abc12345.pkl   ← Python page only
├── en_wikipedia_org_wiki_Java_xyz98765.pkl     ← Java page only (SEPARATE!)
└── www_w3schools_com_python_def11111.pkl       ← W3Schools Python only

Key = first 60 chars of URL path + MD5 hash suffix
    → guarantees uniqueness even for URLs on the same domain
```

This fixes the problem where Python and Java Wikipedia pages (same domain) used to overwrite each other.

---

### Step 5 — RETRIEVE (`retriever.py`)

```
User asks: "Who created Python?"
        │
        ▼
Convert question → TF-IDF vector
        │
        ▼
Compare against ALL chunk vectors using cosine similarity:

  Chunk 42: score 0.91  "Python was created by Guido van Rossum..."  ← TOP
  Chunk 15: score 0.84  "Guido designed Python in the late 1980s..."
  Chunk 7:  score 0.79  "Python 0.9.0 was released in 1991..."
  Chunk 91: score 0.08  (unrelated content)
  Chunk 3:  score 0.01  (unrelated content)
        │
        ▼
Return Top-5 highest scoring chunks → send to LLM
```

---

### Step 6 — GENERATE (`llm.py` + Groq)

```
┌──────────────────────────────────────────────────────────┐
│  SYSTEM PROMPT                                           │
│  "Answer only from the context chunks below."           │
│                                                          │
│  WEBSITE CONTENT (retrieved chunks):                     │
│  [Chunk 1] Python was created by Guido van Rossum...    │
│  [Chunk 2] Guido designed Python in the late 1980s...   │
│  [Chunk 3] Python 0.9.0 was released in 1991...         │
│                                                          │
│  CONVERSATION HISTORY (last 4 turns — memory):          │
│  User: What language inspired Python?                    │
│  Bot:  Python was inspired by ABC language...            │
│                                                          │
│  CURRENT QUESTION: Who created Python?                   │
└──────────────────────────────────────────────────────────┘
        │
        ▼
Groq streams answer token by token → appears in real time on screen
```

**Conversational Memory:** The last 4 Q&A turns are included in every prompt so the bot understands follow-up questions like "Tell me more about that."

---

## 🖥️ Pages Explained

### 🏠 Home Dashboard (`pages/1_Home.py`)
The overview page — shows you the state of your entire knowledge base.

- **4 stat cards** — Sites indexed, Total chunks, Questions asked, Chat sessions
- **Indexed websites list** — All crawled URLs shown with chunk count and pages scraped (info only, no Chat button)
- **Quick actions** — One-click buttons to navigate to Crawl, Chat, or History
- **Recent questions** — Last 5 questions asked across all sessions with timestamps

**Sidebar shows:** What RAG is + what each section on the page does

---

### 🌐 Crawl & Index (`pages/2_Crawl.py`)
Add new websites to your knowledge base.

- **URL input** — Enter any website URL
- **Max pages** — How many pages to crawl (1–50)
- **Model selector** — Choose which Groq model to use for chat
- **Live progress bar** — Shows each page as it is scraped in real time
- **Indexed sites panel** — Lists all previously crawled sites with Chat and Delete buttons
- **How it works expander** — 5-step explanation of the crawl process for users

**Sidebar shows:** Step-by-step explanation of how crawling, chunking, embedding and saving works

---

### 💬 Chat (`pages/3_Chat.py`)
Ask questions about any indexed website.

- **Website selector dropdown** — Pick from all indexed sites
- **Streaming answers** — Responses appear word by word in real time
- **Source display** — Shows which URLs the answer came from
- **Chunk + latency badges** — Shows how many chunks were used and response time
- **Conversational memory** — Bot remembers last 4 turns per session
- **New Chat button** — Resets the conversation
- **PDF Download** — Exports the full session as a formatted PDF (in sidebar)

**Sidebar shows:** How RAG retrieval works step by step + tips for better questions

---

### 🕒 History (`pages/4_History.py`)
Browse and search all past Q&A sessions.

- **All Sessions tab** — Sessions grouped by website, expandable to see full Q&A
- **Search tab** — Full-text search across all past questions
- **PDF Download** — Download any past session as a PDF report
- **Delete options** — Delete individual sessions or clear all history

**Sidebar shows:** How SQLite stores history + table structure + what you can do on this page

---

## 💾 Data Storage

### Vector Stores (`data/stores/*.pkl`)
```
Format:   Python pickle file
Contents: VectorStore object containing:
          - chunks list (text + url + chunk_id per chunk)
          - fitted TF-IDF vectoriser
          - document embedding matrix (numpy array)
          - metadata (source_url, pages_scraped, url_key)
One file per URL — switching websites in Chat loads instantly
```

### Chat History (`data/history.db`)
```sql
-- SQLite database with two tables:

sessions
  id          INTEGER  PRIMARY KEY
  domain_key  TEXT     e.g. "en_wikipedia_org"
  source_url  TEXT     e.g. "https://en.wikipedia.org/wiki/Python"
  started_at  TEXT     "2024-01-15 14:32:00"

messages
  id          INTEGER  PRIMARY KEY
  session_id  INTEGER  → references sessions.id
  role        TEXT     "user" or "assistant"
  content     TEXT     the question or answer text
  sources     TEXT     JSON array of source URLs
  latency     REAL     response time in seconds
  chunks_used INTEGER  how many chunks were retrieved
  created_at  TEXT     timestamp
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11 or higher
- Groq API key — free at https://console.groq.com

### Step 1 — Create virtual environment
```bash
cd rag-website-chatbot
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate

# Activate on Mac/Linux:
source .venv/bin/activate
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Install Playwright browser (for JS sites)
```bash
playwright install chromium
```
This downloads a real Chromium browser (~150MB). Required for JS-heavy sites like W3Schools.

### Step 4 — Configure API key
```bash
cp .env.example .env
```
Edit `.env` and add:
```
GROQ_API_KEY=gsk_your_key_here
```
Get a free key at https://console.groq.com

### Step 5 — Run
```bash
streamlit run app.py
```
Open http://localhost:8501 in your browser.

---

## 📦 Requirements

```
streamlit==1.35.0       Web UI framework — multi-page app with sidebar
groq==0.9.0             Groq LLM API — fast inference, streaming support
httpx==0.27.0           Async HTTP client — Tier 1 scraper (10 concurrent)
requests==2.32.3        Sync HTTP client — Tier 2 scraper (cookie sessions)
playwright==1.44.0      Real browser automation — Tier 3 scraper (JS sites)
beautifulsoup4==4.12.3  HTML parser — extracts clean text from web pages
lxml==5.2.2             Fast HTML parser backend for BeautifulSoup
numpy==1.26.4           Vector math — cosine similarity computation
scikit-learn==1.4.2     TF-IDF vectoriser — text embedding and retrieval
tiktoken==0.7.0         Token counter — accurate chunk size measurement
python-dotenv==1.0.1    Loads GROQ_API_KEY from .env file
reportlab==4.2.0        PDF generation — formats chat sessions for download
```

---

## 🤖 Groq Models

| Model | Speed | Best For |
|---|---|---|
| `llama-3.3-70b-versatile` | Fast | Best quality answers — **default** |
| `llama-3.1-8b-instant` | Fastest | Lower latency, simple questions |
| `mixtral-8x7b-32768` | Fast | Long documents, large context |
| `gemma2-9b-it` | Fast | Lightweight alternative |

---

## ⚠️ Known Limitations

| Issue | Cause | Workaround |
|---|---|---|
| JS-heavy sites fail (W3Schools, etc.) | Needs real browser to render JS | Run `playwright install chromium` |
| Cloudflare-protected sites fail | Advanced bot detection | No reliable fix without paid proxies |
| TF-IDF misses semantic queries | Keyword-based, not meaning-based | Ask specific factual questions |
| Slow on very large sites | Many HTTP requests | Reduce Max Pages to 10–15 |
| Windows asyncio error with Playwright | ProactorEventLoop conflict | Fixed via `WindowsProactorEventLoopPolicy` in scraper.py |

---

## 💡 Example Usage

```
1. Open http://localhost:8501
2. Click  ──►  🌐 Crawl & Index
3. Enter URL:  https://en.wikipedia.org/wiki/Python_(programming_language)
4. Set Max Pages: 10, click Crawl & Index
5. Wait ~20 seconds for crawling and indexing
6. Click  ──►  💬 Chat
7. Select "https://en.wikipedia.org/wiki/Python..." from dropdown
8. Ask: "Who created Python and when?"
9. Ask: "What is Python mainly used for?"
10. Ask: "Tell me more about that"   ← follow-up works via memory
11. In sidebar: click 📄 Download PDF → save full session
12. Click  ──►  🕒 History to browse all past sessions
```

---

## 🔐 Environment Variables

```bash
# .env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx    # Required — get from console.groq.com
```

---

## 📂 Auto-Created Files

These are created automatically when you use the app — do not edit manually:

| Path | Created When | Contains |
|---|---|---|
| `data/stores/*.pkl` | After crawling a URL | Vector index for that URL |
| `data/history.db` | First chat message | All Q&A sessions |

---

*Built with Python · Streamlit · Groq · BeautifulSoup · scikit-learn · ReportLab · SQLite*
