"""Milestone 4 — Embedding + Vector Store + Retrieval.

Pipeline position (see planning.md architecture diagram):

    Document Ingestion -> Chunking -> [Embedding + Vector Store -> Retrieval] -> Generation
                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                       this module

Reads the chunks produced by src/ingest.py (data/chunks.json), embeds each one
with all-MiniLM-L6-v2, and stores the vectors in a persistent ChromaDB
collection together with source metadata. `retrieve()` embeds a query the same
way and returns the top-k most similar chunks.

Retrieval Approach (planning.md):
    Embedding model = sentence-transformers/all-MiniLM-L6-v2
    Top-k           = 3

Build the index:   python src/vector_store.py
Try a query:       python src/vector_store.py "what is Sokol's rating?"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# --- Configuration -----------------------------------------------------------

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Starting point: k=5. Too few and the relevant chunk may never make the set;
# too many and loosely-related chunks dilute the context and pull generation
# off-target. Tune down toward 3 (planning.md) if results look noisy.
TOP_K = 5
COLLECTION_NAME = "unofficial_guide"

REPO_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_PATH = REPO_ROOT / "data" / "chunks.json"
CHROMA_DIR = REPO_ROOT / "chroma_db"   # gitignored; created on first build


# --- Model + store helpers ---------------------------------------------------

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load (once) the embedding model used for both indexing and queries."""
    global _model
    if _model is None:
        print(f"Loading embedding model {EMBEDDING_MODEL} ...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_client() -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client backed by chroma_db/."""
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts into normalized vectors.

    Vectors are L2-normalized so cosine similarity == dot product, matching the
    cosine space the collection is built with.
    """
    embeddings = get_model().encode(
        texts, normalize_embeddings=True, show_progress_bar=False
    )
    return embeddings.tolist()


# --- Embedding + storage -----------------------------------------------------

def build_index() -> int:
    """Embed every chunk from data/chunks.json and (re)store it in ChromaDB.

    The collection is dropped and rebuilt each run so re-ingesting documents
    never leaves stale or duplicate vectors behind. Returns the chunk count.
    """
    if not CHUNKS_PATH.exists():
        raise SystemExit(
            f"{CHUNKS_PATH.relative_to(REPO_ROOT)} not found — "
            "run `python src/ingest.py` first."
        )

    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    if not chunks:
        raise SystemExit("chunks.json is empty — nothing to index.")

    client = get_client()
    # Fresh collection every build; cosine space matches normalized embeddings.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # collection didn't exist yet
    collection = client.create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "source": c["source"],
            "chunk_index": c["chunk_index"],
            "token_count": c["token_count"],
        }
        for c in chunks
    ]

    print(f"Embedding {len(documents)} chunks ...")
    embeddings = embed(documents)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"Stored {collection.count()} chunks in ChromaDB collection "
          f"'{COLLECTION_NAME}' at {CHROMA_DIR.relative_to(REPO_ROOT)}/")
    return collection.count()


# --- Retrieval ---------------------------------------------------------------

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Return the top-k chunks most similar to `query`.

    Each result is a dict with the chunk text, its source metadata, and a
    similarity score in [0, 1] (1 = identical), derived from cosine distance.
    """
    collection = get_client().get_collection(COLLECTION_NAME)

    result = collection.query(
        query_embeddings=embed([query]),
        n_results=top_k,
    )

    hits = []
    for doc, meta, dist in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append({
            "text": doc,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "score": round(1 - dist, 4),  # cosine distance -> similarity
        })
    return hits


# --- CLI ---------------------------------------------------------------------

def main() -> None:
    # With a query argument: retrieve. Without: build the index.
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nQuery: {query!r}  (top_k={TOP_K})\n")
        for i, hit in enumerate(retrieve(query), 1):
            preview = " ".join(hit["text"].split())[:160]
            print(f"{i}. [{hit['source']} #{hit['chunk_index']}] "
                  f"score={hit['score']}")
            print(f"   {preview}\n")
    else:
        build_index()


if __name__ == "__main__":
    main()
