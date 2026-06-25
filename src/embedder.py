from sentence_transformers import SentenceTransformer


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def create_embeddings(chunks):

    texts = [

        chunk["text"]

        for chunk in chunks

    ]

    embeddings = model.encode(

        texts,

        show_progress_bar=True

    )

    embedded_chunks = []

    for chunk, embedding in zip(

        chunks,

        embeddings

    ):

        embedded_chunks.append(

            {

                "url": chunk["url"],

                "text": chunk["text"],

                "embedding": embedding

            }

        )

    return embedded_chunks
if __name__ == "__main__":

    from scraper import recursive_crawler

    from chunker import create_chunks

    start_url = input(
        "Enter website URL: "
    ).strip()

    pages = recursive_crawler(
        start_url,

        max_depth=1,

        max_pages=5
    )

    chunks = create_chunks(
        pages
    )

    embedded_chunks = create_embeddings(chunks)

    if not embedded_chunks:
        
        print("No embeddings created.")

        exit()
    else:
        print(f"Total embeddings: {len(embedded_chunks)}")
        print(f"Vector dimension: {len(embedded_chunks[0]['embedding'])}")
        print(embedded_chunks[0]["url"])
        print(embedded_chunks[0]["text"][:200])