"""Document parser for txt/pdf/md files."""

import io
import logging
from pathlib import Path

from fastapi import UploadFile

logger = logging.getLogger("service-rag.document_parser")


class DocumentParser:
    """Parse uploaded documents into raw text."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}

    def parse(self, file: UploadFile) -> str:
        """Parse a file into text."""
        filename = file.filename or ""
        suffix = Path(filename).suffix.lower()

        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {suffix}. Supported: {self.SUPPORTED_EXTENSIONS}"
            )

        content = file.file.read()
        if not content:
            raise ValueError("Empty file")

        try:
            if suffix == ".txt" or suffix == ".md":
                return content.decode("utf-8")
            elif suffix == ".pdf":
                return self._parse_pdf(content)
        except Exception as exc:
            logger.exception("Failed to parse %s", filename)
            raise ValueError(f"Failed to parse file: {exc}") from exc

        return ""

    def _parse_pdf(self, content: bytes) -> str:
        """Parse PDF content into text."""
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            texts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    texts.append(page_text)
            result = "\n".join(texts)
            if not result.strip():
                logger.warning("PDF parsed to empty text, returning raw placeholder")
                return "[PDF content could not be extracted]"
            return result
        except ImportError:
            logger.warning("PyPDF2 not installed, trying basic extraction")
            return content.decode("utf-8", errors="ignore")[:10000]
