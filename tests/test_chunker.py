"""Tests for chunker module."""

import pytest
from app.ingestion.chunker import Chunker


@pytest.mark.asyncio
async def test_fixed_chunking():
    """Test fixed-size chunking."""
    chunker = Chunker(chunk_size=100, chunk_overlap=20, strategy="fixed")
    text = "This is a test document. " * 50  # Create a long text

    chunks = await chunker.chunk(text)

    assert len(chunks) > 0
    assert all("text" in chunk for chunk in chunks)
    assert all("metadata" in chunk for chunk in chunks)


@pytest.mark.asyncio
async def test_semantic_chunking():
    """Test semantic chunking."""
    chunker = Chunker(chunk_size=200, chunk_overlap=50, strategy="semantic")
    text = """
    This is paragraph one. It contains multiple sentences.
    This is paragraph two. It also has multiple sentences.
    This is paragraph three. More content here.
    """ * 10

    chunks = await chunker.chunk(text)

    assert len(chunks) > 0
    assert all("text" in chunk for chunk in chunks)


@pytest.mark.asyncio
async def test_empty_text():
    """Test chunking empty text."""
    chunker = Chunker()
    chunks = await chunker.chunk("")

    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_metadata_preservation():
    """Test that metadata is preserved in chunks."""
    chunker = Chunker()
    metadata = {"document_name": "test.md", "category": "test"}

    chunks = await chunker.chunk("Test text " * 100, metadata=metadata)

    assert len(chunks) > 0
    assert all(chunk["metadata"]["document_name"] == "test.md" for chunk in chunks)
    assert all(chunk["metadata"]["category"] == "test" for chunk in chunks)
