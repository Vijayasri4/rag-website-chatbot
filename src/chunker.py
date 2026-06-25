from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_chunks(

    pages,

    chunk_size=500,

    chunk_overlap=100

):

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=chunk_size,

        chunk_overlap=chunk_overlap

    )

    chunks = []

    for page in pages:

        page_chunks = splitter.split_text(

            page["text"]

        )

        for chunk in page_chunks:

            chunks.append(

                {

                    "url": page["url"],

                    "text": chunk

                }

            )

    return chunks

if __name__ == "__main__":

    from scraper import recursive_crawler

    start_url = input("Enter website URL: ").strip()

    pages = recursive_crawler(
        start_url,
        max_depth=1,
        max_pages=5
    )

    chunks = create_chunks(pages)

    print(f"\nTotal chunks: {len(chunks)}\n")

    if not chunks:
        print("No chunks were created. Please check the URL and try again.")
    else:
        for i, chunk in enumerate(chunks[:3], start=1):

            print(f"Chunk {i}")

            print(f"Source: {chunk['url']}")

            print(f"Length: {len(chunk['text'])}")

            print(chunk["text"][:250])

            print("\n-----------------\n")

    