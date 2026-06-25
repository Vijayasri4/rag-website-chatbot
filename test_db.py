import chromadb

client = chromadb.PersistentClient(
    path="data/chroma"
)

collection = client.get_collection(
    name="website_data"
)

print("Total records:", collection.count())