import chromadb
from typing import List

# from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class ContextService:
    def __init__(self):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        # Persistent DB
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="presentation_context"
        )

    def embed(self, texts):
        return self.embedding_model.encode(texts).tolist()

    def add_documents(self, documents: list, metadata: list, ids: list):
        embeddings = self.embed(documents)

        self.collection.add(
            documents=documents, metadatas=metadata, ids=ids, embeddings=embeddings
        )

    def retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        query_embedding = self.embed([query])[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        documents = results.get("documents", [])

        if not documents:
            return []

        return documents[0]


context_service = ContextService()


def retrieve_context(query: str, top_k: int = 3):
    return context_service.retrieve_context(query, top_k)
