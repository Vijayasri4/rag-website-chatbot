import requests

from bs4 import BeautifulSoup

from urllib.parse import urljoin, urlparse


def fetch_page(url):

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )

        response.raise_for_status()

        return response.text

    except Exception as e:

        print(f"Error fetching {url}: {e}")

        return None
def extract_links(base_url, html):

    soup = BeautifulSoup(html, "html.parser")

    links = set()

    base_domain = urlparse(base_url).netloc

    for tag in soup.find_all("a", href=True):

        href = tag["href"]

        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue

        absolute_url = urljoin(base_url, href)

        parsed = urlparse(absolute_url)

        # Same domain only
        if parsed.netloc != base_domain:

            continue

        # Ignore anchor links
        if parsed.fragment and not parsed.path:

            continue

        # Ignore Cloudflare email protection
        if "cdn-cgi" in absolute_url:

            continue

        # Remove query parameters
        clean_url = (
            f"{parsed.scheme}://"
            f"{parsed.netloc}"
            f"{parsed.path}"
        )

        links.add(clean_url)

    return links
def clean_text(html):

    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted sections
    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "noscript"
        ]
    ):
        tag.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True
    )

    return text
def normalize_url(url):

    parsed = urlparse(url)

    path = parsed.path.rstrip("/")

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{path}"
    )

def recursive_crawler(start_url, max_depth=2, max_pages=50):

    if not start_url.startswith(("http://", "https://")):
        start_url = "https://" + start_url

    visited = set()

    pages = []

    def crawl(url, depth):

        # Stop if we've reached the depth limit
        if depth > max_depth:
            return
        if len(pages) >= max_pages:
            return
        # Avoid visiting the same page twice
        normalized = normalize_url(url)

        if normalized in visited:
            return

        visited.add(normalized)

        print(f"Crawling: {url}")

        html = fetch_page(url)

        if not html:
            return

        text = clean_text(html)

        pages.append(
            {
                "url": url,
                "text": text
            }
        )

        links = extract_links(url, html)

        for link in links:

            crawl(link, depth + 1)

    crawl(start_url, 0)

    return pages


if __name__ == "__main__":

    start_url = input("Enter website URL: ").strip()

    if not start_url:
        print("Please enter a valid URL.")
        exit()

    pages = recursive_crawler(
        start_url,
        max_depth=2,
        max_pages=50
    )

    print(f"\nTotal pages scraped: {len(pages)}\n")

    for page in pages[:5]:

        print(page["url"])

        print(page["text"][:200])

        print()