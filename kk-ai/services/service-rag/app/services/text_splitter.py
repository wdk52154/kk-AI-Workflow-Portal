"""Text splitting utilities for document chunking."""

import logging
import re
from dataclasses import dataclass

import tiktoken

from app.config import get_settings

logger = logging.getLogger("service-rag.text_splitter")


@dataclass
class TextChunk:
    """A text chunk with metadata."""

    text: str
    index: int


class TokenTextSplitter:
    """Split text into chunks by token count."""

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        settings = get_settings()
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def split(self, text: str) -> list[TextChunk]:
        """Split text into overlapping token chunks."""
        tokens = self.encoder.encode(text)
        chunks = []
        start = 0
        index = 0

        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoder.decode(chunk_tokens)
            chunks.append(TextChunk(text=chunk_text, index=index))
            index += 1
            start += self.chunk_size - self.chunk_overlap

        logger.info("Split text into %d chunks (size=%d, overlap=%d)", len(chunks), self.chunk_size, self.chunk_overlap)
        return chunks

    def split_markdown(self, text: str) -> list[TextChunk]:
        """Split markdown by headers (# ## ###). Falls back to token splitting."""
        # Split by headers
        sections = re.split(r'\n(?=#{1,6}\s)', text.strip())
        sections = [s.strip() for s in sections if s.strip()]

        if len(sections) <= 1:
            # No headers found, fall back to token splitting
            return self.split(text)

        # Further split large sections by tokens
        chunks = []
        index = 0
        for section in sections:
            section_tokens = len(self.encoder.encode(section))
            if section_tokens <= self.chunk_size:
                chunks.append(TextChunk(text=section, index=index))
                index += 1
            else:
                # Split large section
                sub_chunks = self.split(section)
                for sc in sub_chunks:
                    sc.index = index
                    chunks.append(sc)
                    index += 1

        logger.info("Split markdown into %d chunks by headers", len(chunks))
        return chunks
