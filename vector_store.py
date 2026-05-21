"""
vector_store.py
---------------
ChromaDB layer for meetings.

We store each meeting as ONE document (whole notes text) tagged with
metadata: meeting_id, title, date. For RAG search we then retrieve
the most relevant meetings by similarity.

For VERY long meetings we could chunk them, but typical meeting notes
are short enough to keep as a single document for simplicity.
"""

from typing import List, Dict, Any
from datetime import datetime

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config import EMBEDDING_MODEL, CHROMA_PERSIST_DIR

# Embedding model (sentence-transformers, runs locally on CPU)
_embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

COLLECTION_NAME = "meetings"


def _get_store() -> Chroma:
    """Return the persistent ChromaDB instance."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )


def store_meeting(meeting_id: str, title: str, notes: str) -> None:
    """Save a meeting's full notes in ChromaDB with metadata."""
    store = _get_store()

    # If we already have this meeting_id, delete the old one (idempotent)
    try:
        store.delete(where={"meeting_id": meeting_id})
    except Exception:
        pass

    doc = Document(
        page_content=notes,
        metadata={
            "meeting_id": meeting_id,
            "title": title,
            "date": datetime.utcnow().isoformat(),
        },
    )
    store.add_documents([doc])


def get_meeting(meeting_id: str) -> str:
    """Return the notes of a single meeting (empty string if not found)."""
    store = _get_store()
    result = store.get(where={"meeting_id": meeting_id})
    docs = result.get("documents", [])
    return docs[0] if docs else ""


def list_meetings() -> List[Dict[str, Any]]:
    """Return a list of meeting summaries (id, title, date)."""
    store = _get_store()
    result = store.get()
    items = []
    metadatas = result.get("metadatas") or []
    for md in metadatas:
        items.append({
            "meeting_id": md.get("meeting_id"),
            "title": md.get("title"),
            "date": md.get("date"),
        })
    # Newest first
    items.sort(key=lambda x: x.get("date") or "", reverse=True)
    return items


def search_meetings(query: str, k: int = 4) -> List[Dict[str, Any]]:
    """
    Semantic search across all meetings.
    Returns up to k matching meetings, each with a text snippet.
    """
    store = _get_store()
    docs = store.similarity_search(query, k=k)

    results = []
    for d in docs:
        snippet = d.page_content[:400] + ("..." if len(d.page_content) > 400 else "")
        results.append({
            "meeting_id": d.metadata.get("meeting_id"),
            "title": d.metadata.get("title"),
            "date": d.metadata.get("date"),
            "snippet": snippet,
            "full_text": d.page_content,
        })
    return results
