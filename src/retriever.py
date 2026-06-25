import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(
    path="data/chroma"
)

collection = client.get_or_create_collection(
    name="website_data"
)


def retrieve(query, top_k=3, threshold=0.7):

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    filtered = []

    for i in range(len(results["ids"][0])):

        distance = results["distances"][0][i]

        # Only return results below threshold
        if distance < threshold:

            filtered.append({
                "text": results["documents"][0][i],
                "url": results["metadatas"][0][i]["url"],
                "distance": distance
            })

    if not filtered:
        print("No relevant results found for this question.")
        return []

    return filtered


if __name__ == "__main__":

    query = input("Ask a question: ").strip()

    if not query:
        print("Please enter a question.")
        exit()

    results = retrieve(query)

    if not results:
        exit()

    print(f"\nTop Results:\n")

    for i, result in enumerate(results, start=1):

        print(f"Result {i}")
        print(f"Distance: {result['distance']}")
        print(f"Source: {result['url']}")
        print(result["text"][:300])
        print("-" * 50)