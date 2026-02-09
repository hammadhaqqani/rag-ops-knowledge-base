"""Text chunking strategies for document processing."""

import logging
import re
from typing import Dict, List, Optional

import tiktoken

logger = logging.getLogger(__name__)


class Chunker:
    """Chunks text using various strategies."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        strategy: str = "fixed",
    ):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size for chunks (in tokens for fixed, characters for semantic)
            chunk_overlap: Overlap between chunks
            strategy: Chunking strategy ("fixed" or "semantic")
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy

        # Initialize tokenizer for fixed-size chunking
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to load tokenizer: {e}. Using character-based chunking.")
            self.tokenizer = None

    async def chunk(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> List[Dict[str, any]]:
        """
        Chunk text using the configured strategy.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of chunk dictionaries with 'text' and 'metadata' keys
        """
        if self.strategy == "fixed":
            return await self._chunk_fixed(text, metadata)
        elif self.strategy == "semantic":
            return await self._chunk_semantic(text, metadata)
        else:
            logger.warning(f"Unknown strategy {self.strategy}, using fixed")
            return await self._chunk_fixed(text, metadata)

    async def _chunk_fixed(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """Chunk text into fixed-size chunks."""
        if not text.strip():
            return []

        chunks = []
        metadata = metadata or {}

        if self.tokenizer:
            # Token-based chunking
            tokens = self.tokenizer.encode(text)
            step = self.chunk_size - self.chunk_overlap

            for i in range(0, len(tokens), step):
                chunk_tokens = tokens[i : i + self.chunk_size]
                chunk_text = self.tokenizer.decode(chunk_tokens)
                chunks.append({
                    "text": chunk_text.strip(),
                    "metadata": {**metadata, "chunk_type": "fixed", "chunk_index": len(chunks)},
                })
        else:
            # Character-based chunking (fallback)
            step = self.chunk_size - self.chunk_overlap
            for i in range(0, len(text), step):
                chunk_text = text[i : i + self.chunk_size]
                chunks.append({
                    "text": chunk_text.strip(),
                    "metadata": {**metadata, "chunk_type": "fixed", "chunk_index": len(chunks)},
                })

        return chunks

    async def _chunk_semantic(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """Chunk text using semantic boundaries (sentences, paragraphs)."""
        if not text.strip():
            return []

        chunks = []
        metadata = metadata or {}

        # Split into paragraphs first
        paragraphs = re.split(r"\n\s*\n", text)
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            para_length = len(paragraph)

            # If adding this paragraph would exceed chunk size, finalize current chunk
            if current_length + para_length > self.chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {**metadata, "chunk_type": "semantic", "chunk_index": len(chunks)},
                })
                current_chunk = []
                current_length = 0

            # If paragraph itself is larger than chunk size, split it by sentences
            if para_length > self.chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    sent_length = len(sentence)
                    if current_length + sent_length > self.chunk_size and current_chunk:
                        chunk_text = "\n\n".join(current_chunk)
                        chunks.append({
                            "text": chunk_text,
                            "metadata": {**metadata, "chunk_type": "semantic", "chunk_index": len(chunks)},
                        })
                        current_chunk = []
                        current_length = 0

                    current_chunk.append(sentence)
                    current_length += sent_length + 2  # +2 for "\n\n"
            else:
                current_chunk.append(paragraph)
                current_length += para_length + 2  # +2 for "\n\n"

        # Add remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "metadata": {**metadata, "chunk_type": "semantic", "chunk_index": len(chunks)},
            })

        return chunks
