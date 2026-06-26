from pathlib import Path

# ==========================
# Paths
# ==========================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

CHROMA_DIR = DATA_DIR / "chroma"

CHROMA_COLLECTION = "website_docs"

# ==========================
# Scraper
# ==========================

MAX_PAGES = 500
MAX_DEPTH = 5
MAX_WORKERS = 8
REQUEST_TIMEOUT = 30000

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/137.0 Safari/537.36"
)

# ==========================
# Chunking
# ==========================

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# ==========================
# Embedding
# ==========================

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ==========================
# Retrieval
# ==========================

TOP_K = 5