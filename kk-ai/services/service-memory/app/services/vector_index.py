"""In-memory vector index for semantic search."""

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("service-memory.vector_index")


def cosine_similarity(query: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between query and embeddings."""
    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        return np.zeros(len(embeddings))

    emb_norms = np.linalg.norm(embeddings, axis=1)
    emb_norms[emb_norms == 0] = 1

    return np.dot(embeddings, query) / emb_norms / query_norm


def vector_search(
    entries: list[dict[str, Any]],
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Search entries by vector similarity."""
    if not entries:
        return []

    query = np.array(query_embedding, dtype=np.float32)
    valid_entries = []
    embeddings = []

    for entry in entries:
        emb = entry.get("embedding")
        if emb is not None:
            valid_entries.append(entry)
            if isinstance(emb, str):
                import json
                emb = json.loads(emb)
            embeddings.append(emb)

    if not embeddings:
        logger.warning("No embeddings found in entries")
        return []

    embeddings_arr = np.array(embeddings, dtype=np.float32)
    similarities = cosine_similarity(query, embeddings_arr)
    top_k = min(top_k, len(valid_entries))
    top_indices = np.argsort(similarities)[::-1][:top_k]

    return [
        {**valid_entries[i], "score": round(float(similarities[i]), 4)}
        for i in top_indices
    ]
