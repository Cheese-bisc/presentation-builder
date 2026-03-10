"""
context_service.py  —  app/services/context_service.py

Session-scoped ChromaDB collections. Each session gets its own isolated
collection that is deleted when the session is cleared.
No cross-session context bleed.
"""

from sentence_transformers import SentenceTransformer
import chromadb

_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
_client = chromadb.PersistentClient(path="./chroma_db")


def _embed(texts: list) -> list:
    return _embedding_model.encode(texts).tolist()


def _collection_name(session_id: str) -> str:
    # ChromaDB collection names must be 3-63 chars, alphanumeric + hyphens
    return f"session-{session_id}"


# ---------------------------------------------------------------------------
# Called from /upload — store chunks scoped to a session
# ---------------------------------------------------------------------------


def add_documents(session_id: str, documents: list, metadata: list, ids: list):
    collection = _client.get_or_create_collection(_collection_name(session_id))
    embeddings = _embed(documents)
    collection.add(
        documents=documents,
        metadatas=metadata,
        ids=ids,
        embeddings=embeddings,
    )


# ---------------------------------------------------------------------------
# Called from /generate and /edit — retrieve only from this session's docs
# ---------------------------------------------------------------------------


def retrieve_context(session_id: str, query: str, top_k: int = 3) -> list[str]:
    name = _collection_name(session_id)

    # If no docs were uploaded for this session, return empty immediately
    try:
        collection = _client.get_collection(name)
    except Exception:
        return []

    if collection.count() == 0:
        return []

    query_embedding = _embed([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )
    docs = results.get("documents", [])
    return docs[0] if docs else []


# ---------------------------------------------------------------------------
# Called when session is deleted (start over) — cleans up ChromaDB collection
# ---------------------------------------------------------------------------


def delete_session_context(session_id: str):
    name = _collection_name(session_id)
    try:
        _client.delete_collection(name)
    except Exception:
        pass  # collection may not exist if no file was uploaded
