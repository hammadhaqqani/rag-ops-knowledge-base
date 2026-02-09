"""Tests for search module."""

import pytest
from unittest.mock import AsyncMock

from app.retrieval.search import SemanticSearch
from app.retrieval.opensearch import OpenSearchClient
from app.ingestion.embeddings import BedrockEmbeddings


@pytest.mark.asyncio
async def test_semantic_search():
    """Test semantic search functionality."""
    # Mock dependencies
    mock_opensearch = AsyncMock(spec=OpenSearchClient)
    mock_embeddings = AsyncMock(spec=BedrockEmbeddings)

    # Mock embedding generation
    mock_embeddings.embed_text = AsyncMock(return_value=[0.1] * 1536)

    # Mock search results
    mock_opensearch.search = AsyncMock(
        return_value=[
            {
                "chunk_id": "chunk_1",
                "text": "Test content 1",
                "score": 0.85,
                "document": "test.md",
                "metadata": {},
            },
            {
                "chunk_id": "chunk_2",
                "text": "Test content 2",
                "score": 0.75,
                "document": "test2.md",
                "metadata": {},
            },
        ]
    )

    # Create search instance
    search = SemanticSearch(
        opensearch_client=mock_opensearch,
        embeddings=mock_embeddings,
    )

    # Perform search
    results = await search.search("test query", max_results=5, min_score=0.7)

    # Verify results
    assert len(results) == 2
    assert results[0]["chunk_id"] == "chunk_1"
    assert results[0]["score"] == 0.85
    assert "content" in results[0]

    # Verify embeddings were called
    mock_embeddings.embed_text.assert_called_once_with("test query")
    mock_opensearch.search.assert_called_once()


@pytest.mark.asyncio
async def test_search_no_results():
    """Test search with no results."""
    mock_opensearch = AsyncMock(spec=OpenSearchClient)
    mock_embeddings = AsyncMock(spec=BedrockEmbeddings)

    mock_embeddings.embed_text = AsyncMock(return_value=[0.1] * 1536)
    mock_opensearch.search = AsyncMock(return_value=[])

    search = SemanticSearch(
        opensearch_client=mock_opensearch,
        embeddings=mock_embeddings,
    )

    results = await search.search("test query")

    assert len(results) == 0
