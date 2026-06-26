import asyncio

from src.scraper import WebsiteCrawler
from src.chunker import TextChunker
from src.embedder import Embedder


async def main():

    crawler = WebsiteCrawler()

    pages = await crawler.crawl(
        "https://fastapi.tiangolo.com/"
    )

    print("Pages:", len(pages))

    chunker = TextChunker()

    chunks = chunker.chunk_pages(pages)

    print("Chunks:", len(chunks))

    embedder = Embedder()

    embeddings = embedder.embed_documents(chunks)

    print()

    print("Embedding Shape:")

    print(embeddings.shape)

    print()

    print(chunks[0]["text"][:300])


asyncio.run(main())