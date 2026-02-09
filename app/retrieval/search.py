"""Semantic search implementation."""

import logging
from typing import List, Dict, Any

from app.retrieval.opensearch import OpenSearchClient
from app.ingestion.embeddings import BedrockEmbeddings

logger = logging.getLogger(__name__)


class SemanticSearch:
    """Semantic search using embeddings and vector similarity."""

    def __init__(
        self,
        opensearch_client: OpenSearchClient,
        embeddings: BedrockEmbeddings,
    ):
        """
        Initialize semantic search.

        Args:
            opensearch_client: OpenSearch client instance
            embeddings: Bedrock embeddings instance
        """
        self.opensearch_client = opensearch_client
        self.embeddings = embeddings

    async def search(
        self,
        query: str,
        max_results: int = 5,
        min_score: float = 0.7,
        filter_dict: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search.

        Args:
            query: Natural language query
            max_results: Maximum number of results
            min_score: Minimum similarity score
            filter_dict: Optional filter dictionary

        Returns:
            List of search results with content, score, and metadata
        """
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.embed_text(query)

            # Perform vector search
            results = await self.opensearch_client.search(
                query_embedding=query_embedding,
                max_results=max_results,
                min_score=min_score,
                filter_dict=filter_dict,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "chunk_id": result.get("chunk_id"),
                        "content": result.get("text", ""),
                        "score": result.get("score", 0.0),
                        "document": result.get("document", "unknown"),
                        "metadata": result.get("metadata", {}),
                    }
                )

            logger.info(
                f"Found {len(formatted_results)} results for query: {query[:50]}..."
            )
            return formatted_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}", exc_info=True)
            raise
