import uuid
import chromadb

client = chromadb.PersistentClient(
    path="data/chroma"
)

collection = client.get_or_create_collection(
    name="website_data"
)


def clear_url_data(url):
    results = collection.get(
        where={"url": url}
    )
    if results["ids"]:
        collection.delete(ids=results["ids"])
        print(f"Cleared old data for: {url}")


def save_embeddings(embedded_chunks, refresh=False):

    urls_in_batch = set(
        chunk["url"] for chunk in embedded_chunks
    )

    if refresh:
        for url in urls_in_batch:
            clear_url_data(url)

    for chunk in embedded_chunks:
        collection.add(
            ids=[str(uuid.uuid4())],
            documents=[chunk["text"]],
            embeddings=[chunk["embedding"].tolist()],
            metadatas=[{"url": chunk["url"]}]
        )

    print(f"Saved {len(embedded_chunks)} chunks successfully.")


def is_url_stored(base_url):
    results = collection.get(
        where={"url": base_url},
        limit=1
    )
    return len(results["ids"]) > 0


if __name__ == "__main__":

    from scraper import recursive_crawler
    from chunker import create_chunks
    from embedder import create_embeddings

    start_url = input("Enter website URL: ").strip()

    if not start_url:
        print("Please enter a valid URL.")
        exit()

    # Check if URL already exists in DB
    already_exists = is_url_stored(start_url)

    if already_exists:
        print(f"\nThis URL already exists in the database!")
        print("Options:")
        print("  1. skip    - Use existing data (faster)")
        print("  2. refresh - Delete old data and re-scrape")
        print("  3. exit    - Cancel and exit")

        choice = input(
            "\nEnter your choice (skip/refresh/exit): "
        ).strip().lower()

        if choice == "skip":
            print("\nUsing existing data from database.")
            print("You can now run the chatbot!")
            exit()

        elif choice == "refresh":
            print("\nRe-scraping website and updating database...")

            pages = recursive_crawler(
                start_url,
                max_depth=2,
                max_pages=20
            )

            if not pages:
                print("No pages scraped. Check the URL and try again.")
                exit()

            chunks = create_chunks(pages)
            embedded_chunks = create_embeddings(chunks)

            if not embedded_chunks:
                print("No embeddings created.")
                exit()

            save_embeddings(embedded_chunks, refresh=True)

        elif choice == "exit":
            print("Exiting. Goodbye!")
            exit()

        else:
            print("Invalid choice. Exiting.")
            exit()

    else:
        # Fresh URL - scrape and save directly
        print(f"\nNew URL detected. Starting scraping...")

        pages = recursive_crawler(
            start_url,
            max_depth=1,
            max_pages=5
        )

        if not pages:
            print("No pages scraped. Check the URL and try again.")
            exit()

        chunks = create_chunks(pages)
        embedded_chunks = create_embeddings(chunks)

        if not embedded_chunks:
            print("No embeddings created.")
            exit()

        save_embeddings(embedded_chunks, refresh=False)
        print("\nDone! You can now run the chatbot.")