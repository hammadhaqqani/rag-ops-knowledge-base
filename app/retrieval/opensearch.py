"""OpenSearch Serverless client for vector storage and retrieval."""

import logging
from typing import Dict, List, Optional, Any
import json

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger(__name__)


class OpenSearchClient:
    """Client for interacting with OpenSearch Serverless."""

    def __init__(
        self,
        endpoint: str,
        index_name: str,
        region: str = "us-east-1",
    ):
        """
        Initialize OpenSearch client.

        Args:
            endpoint: OpenSearch Serverless collection endpoint
            index_name: Name of the index
            region: AWS region
        """
        self.endpoint = endpoint
        self.index_name = index_name
        self.region = region

        # Get AWS credentials
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "aoss",
            session_token=credentials.token,
        )

        # Create OpenSearch client
        self.client = OpenSearch(
            hosts=[{"host": endpoint.replace("https://", ""), "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30,
        )

    async def initialize(self):
        """Initialize the index if it doesn't exist."""
        if not await self._index_exists():
            await self._create_index()

    async def _index_exists(self) -> bool:
        """Check if the index exists."""
        try:
            return self.client.indices.exists(index=self.index_name)
        except Exception as e:
            logger.error(f"Error checking index existence: {e}", exc_info=True)
            return False

    async def _create_index(self):
        """Create the index with vector mapping."""
        try:
            index_body = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100,
                    }
                },
                "mappings": {
                    "properties": {
                        "text": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,  # Titan embedding dimension
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                            },
                        },
                        "metadata": {
                            "type": "object",
                            "enabled": True,
                        },
                    }
                },
            }

            self.client.indices.create(index=self.index_name, body=index_body)
            logger.info(f"Created index: {self.index_name}")

        except Exception as e:
            logger.error(f"Error creating index: {e}", exc_info=True)
            raise

    async def index_document(
        self,
        document_id: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Index a document with its embedding.

        Args:
            document_id: Unique document identifier
            text: Document text content
            embedding: Embedding vector
            metadata: Optional metadata dictionary
        """
        try:
            document = {
                "text": text,
                "embedding": embedding,
                "metadata": metadata or {},
            }

            self.client.index(
                index=self.index_name,
                id=document_id,
                body=document,
            )
            logger.debug(f"Indexed document: {document_id}")

        except Exception as e:
            logger.error(f"Error indexing document {document_id}: {e}", exc_info=True)
            raise

    async def search(
        self,
        query_embedding: List[float],
        max_results: int = 5,
        min_score: float = 0.7,
        filter_dict: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.

        Args:
            query_embedding: Query embedding vector
            max_results: Maximum number of results
            min_score: Minimum similarity score
            filter_dict: Optional filter dictionary

        Returns:
            List of search results with text, score, and metadata
        """
        try:
            query = {
                "size": max_results,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding,
                            "k": max_results,
                        }
                    }
                },
                "_source": ["text", "metadata"],
            }

            if filter_dict:
                query["query"]["knn"]["embedding"]["filter"] = filter_dict

            response = self.client.search(index=self.index_name, body=query)

            results = []
            for hit in response.get("hits", {}).get("hits", []):
                score = hit.get("_score", 0.0)
                if score >= min_score:
                    results.append(
                        {
                            "chunk_id": hit.get("_id"),
                            "text": hit.get("_source", {}).get("text", ""),
                            "score": float(score),
                            "metadata": hit.get("_source", {}).get("metadata", {}),
                            "document": hit.get("_source", {})
                            .get("metadata", {})
                            .get("document_name", "unknown"),
                        }
                    )

            return results

        except Exception as e:
            logger.error(f"Error performing search: {e}", exc_info=True)
            raise

    async def delete_document(self, document_id: str):
        """Delete a document from the index."""
        try:
            self.client.delete(index=self.index_name, id=document_id)
            logger.info(f"Deleted document: {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}", exc_info=True)
            raise

    async def health_check(self) -> bool:
        """Check if OpenSearch is accessible."""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return False

    async def close(self):
        """Close the OpenSearch client connection."""
        # OpenSearch client doesn't have an explicit close method
        # Connection is managed by requests library
        pass
