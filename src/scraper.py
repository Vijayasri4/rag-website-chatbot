"""
scraper.py
----------
Hybrid scraper:
  1. Tries fast httpx first
  2. Falls back to Playwright (real browser) for JS/Cloudflare-protected sites
"""
import asyncio
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

TIMEOUT = 15


def _normalize(href: str, base: str) -> str:
    try:
        joined = urljoin(base, href.strip())
        return urlparse(joined)._replace(fragment="").geturl()
    except Exception:
        return ""


def _same_domain(url: str, seed: str) -> bool:
    try:
        u = urlparse(url).netloc.lower().replace("www.", "")
        s = urlparse(seed).netloc.lower().replace("www.", "")
        return u == s
    except Exception:
        return False


def _extract_text(html: str, page_url: str) -> tuple[str, list[str]]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script","style","nav","footer","header","aside",
                     "form","noscript","svg","iframe","button"]):
        tag.decompose()

    title = (soup.title.string or page_url).strip()

    seen_keys = set()
    blocks = []
    for el in soup.find_all(["h1","h2","h3","h4","h5","h6",
                              "p","li","td","th","pre","blockquote","article","section","main"]):
        text = el.get_text(" ", strip=True)
        key  = text[:80]
        if len(text) > 60 and key not in seen_keys:
            seen_keys.add(key)
            blocks.append(text)

    content = f"[PAGE: {title}]\n[URL: {page_url}]\n\n" + "\n\n".join(blocks)

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href and not href.startswith(("mailto:","tel:","javascript:","#")):
            norm = _normalize(href, page_url)
            if norm:
                links.append(norm)

    return content, links


# ── Fast httpx fetch ──────────────────────────────────────────────────────────
async def _fetch_httpx(url: str, client: httpx.AsyncClient) -> str | None:
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        if "html" not in resp.headers.get("content-type", ""):
            return None
        return resp.text
    except Exception:
        return None


def _is_blocked(html: str | None) -> bool:
    """Detect Cloudflare / JS-only / empty pages."""
    if not html or len(html.strip()) < 500:
        return True
    lower = html.lower()
    signals = [
        "just a moment",          # Cloudflare spinner
        "checking your browser",  # Cloudflare check
        "enable javascript",      # JS-required
        "cf-browser-verification",
        "ddos-guard",
        "please wait",
        "<body></body>",
        "<body>\n</body>",
    ]
    return any(s in lower for s in signals)


# ── Playwright fetch (real browser) ───────────────────────────────────────────
async def _fetch_playwright(url: str) -> str | None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage",
                      "--disable-blink-features=AutomationControlled"]
            )
            ctx = await browser.new_context(
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1280, "height": 800},
                java_script_enabled=True,
            )
            page = await ctx.new_page()

            # Hide webdriver flag (anti-bot evasion)
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)   # let JS fully render

            html = await page.content()
            await browser.close()
            return html
    except Exception as e:
        print(f"[Playwright error] {url}: {e}")
        return None


# ── Main crawl ────────────────────────────────────────────────────────────────
async def crawl(seed_url: str, max_pages: int = 20,
                progress_callback=None,
                use_playwright: bool = False) -> list[tuple[str, str]]:

    if not seed_url.startswith(("http://", "https://")):
        seed_url = "https://" + seed_url

    visited: set[str]           = set()
    queue:   list[str]          = [seed_url]
    results: list[tuple[str,str]] = []

    # ── Auto-detect if site needs Playwright ──────────────────────────────────
    async with httpx.AsyncClient(
        timeout=TIMEOUT, follow_redirects=True,
        headers=HEADERS, verify=False
    ) as client:
        probe_html = await _fetch_httpx(seed_url, client)

    if _is_blocked(probe_html):
        print(f"[Scraper] httpx blocked by {seed_url}, switching to Playwright…")
        use_playwright = True
    # ─────────────────────────────────────────────────────────────────────────

    async with httpx.AsyncClient(
        timeout=TIMEOUT, follow_redirects=True,
        headers=HEADERS, verify=False
    ) as client:

        while queue and len(visited) < max_pages:
            batch = []
            while queue and len(batch) < 3 and len(visited) < max_pages:
                url = queue.pop(0)
                if url not in visited:
                    visited.add(url)
                    batch.append(url)

            if not batch:
                break

            for url in batch:
                # Choose fetch method
                if use_playwright:
                    html = await _fetch_playwright(url)
                else:
                    html = await _fetch_httpx(url, client)
                    if _is_blocked(html):
                        html = await _fetch_playwright(url)

                if not html:
                    continue

                text, links = _extract_text(html, url)
                body = "\n".join(text.split("\n")[2:]).strip()
                if len(body) > 150:
                    results.append((url, text))
                    if progress_callback:
                        progress_callback(len(results), max_pages, url)

                for link in links:
                    if _same_domain(link, seed_url) and link not in visited:
                        queue.append(link)

    return results


def crawl_sync(seed_url: str, max_pages: int = 20,
               progress_callback=None) -> list[tuple[str, str]]:
    """Synchronous wrapper for Streamlit."""
    return asyncio.run(crawl(seed_url, max_pages, progress_callback))

