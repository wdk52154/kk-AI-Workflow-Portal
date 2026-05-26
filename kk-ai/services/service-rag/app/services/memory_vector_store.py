"""Memory-based vector store with cosine similarity search.
API-compatible with ChromaDB for future migration."""

import logging
import threading
import uuid
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger("service-rag.vector_store")


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between vectors."""
    a_norm = np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = np.linalg.norm(b, axis=1, keepdims=True)
    a_norm[a_norm == 0] = 1
    b_norm[b_norm == 0] = 1
    return (a @ b.T) / (a_norm * b_norm.T)


@dataclass
class Chunk:
    """A single document chunk with embedding and metadata."""

    id: str
    text: str
    embedding: list[float]
    metadata: dict = field(default_factory=dict)


class Collection:
    """In-memory collection mimicking ChromaDB Collection API."""

    def __init__(self, name: str):
        self.name = name
        self._chunks: dict[str, Chunk] = {}
        self._lock = threading.RLock()

    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        with self._lock:
            for id_, doc, emb, meta in zip(ids, documents, embeddings, metadatas):
                self._chunks[id_] = Chunk(
                    id=id_, text=doc, embedding=emb, metadata=meta
                )

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 5,
        where: dict | None = None,
    ) -> dict:
        with self._lock:
            if not self._chunks:
                return {
                    "ids": [[]],
                    "documents": [[]],
                    "metadatas": [[]],
                    "distances": [[]],
                }

            # Filter by metadata if where clause provided
            candidates = list(self._chunks.values())
            if where:
                candidates = [c for c in candidates if self._match_filter(c.metadata, where)]

            if not candidates:
                return {
                    "ids": [[]],
                    "documents": [[]],
                    "metadatas": [[]],
                    "distances": [[]],
                }

            # Compute cosine similarity
            query_vec = np.array(query_embeddings)
            chunk_vecs = np.array([c.embedding for c in candidates])
            similarities = _cosine_similarity(query_vec, chunk_vecs)[0]

            # Get top-k indices
            top_k = min(n_results, len(candidates))
            top_indices = np.argsort(similarities)[::-1][:top_k]

            results = {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }
            for idx in top_indices:
                chunk = candidates[idx]
                results["ids"][0].append(chunk.id)
                results["documents"][0].append(chunk.text)
                results["metadatas"][0].append(chunk.metadata)
                # Convert similarity to distance (1 - similarity)
                results["distances"][0].append(float(1 - similarities[idx]))

            return results

    def delete(self, ids: list[str]) -> None:
        with self._lock:
            for id_ in ids:
                self._chunks.pop(id_, None)

    def get(self, where: dict | None = None) -> dict:
        with self._lock:
            chunks = list(self._chunks.values())
            if where:
                chunks = [c for c in chunks if self._match_filter(c.metadata, where)]
            return {
                "ids": [c.id for c in chunks],
                "documents": [c.text for c in chunks],
                "metadatas": [c.metadata for c in chunks],
            }

    def count(self) -> int:
        with self._lock:
            return len(self._chunks)

    @staticmethod
    def _match_filter(metadata: dict, where: dict) -> bool:
        """Simple metadata filter matching."""
        for key, condition in where.items():
            if key not in metadata:
                return False
            value = metadata[key]
            if isinstance(condition, dict):
                # Handle operators: $eq, $ne, $gt, $gte, $lt, $lte, $in
                for op, op_val in condition.items():
                    if op == "$eq" and value != op_val:
                        return False
                    elif op == "$ne" and value == op_val:
                        return False
                    elif op == "$gt" and not (value > op_val):
                        return False
                    elif op == "$gte" and not (value >= op_val):
                        return False
                    elif op == "$lt" and not (value < op_val):
                        return False
                    elif op == "$lte" and not (value <= op_val):
                        return False
                    elif op == "$in" and value not in op_val:
                        return False
            else:
                # Direct equality
                if value != condition:
                    return False
        return True


class VectorStore:
    """Multi-tenant vector store (memory-based, ChromaDB-compatible API)."""

    def __init__(self):
        self._collections: dict[str, Collection] = {}
        self._lock = threading.Lock()

    def get_or_create_collection(self, name: str) -> Collection:
        with self._lock:
            if name not in self._collections:
                self._collections[name] = Collection(name)
                logger.info("Created collection: %s", name)
            return self._collections[name]

    def delete_collection(self, name: str) -> None:
        with self._lock:
            self._collections.pop(name, None)

    def list_collections(self) -> list[str]:
        with self._lock:
            return list(self._collections.keys())


# Global singleton
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create the global VectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
