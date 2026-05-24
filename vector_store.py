import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="./chroma_db")

embedding_fn = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="football_context",
    embedding_function=embedding_fn
)

def add_documents(docs: list[dict]):
    collection.add(
        documents=[d["text"] for d in docs],
        ids=[d["id"] for d in docs]
    )

def retrieve(query: str, n_results: int = 3) -> list[str]:
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results["documents"][0]