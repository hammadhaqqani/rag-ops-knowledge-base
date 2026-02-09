"""AWS Bedrock embeddings generation."""

import logging
from typing import List

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockEmbeddings:
    """Generate embeddings using AWS Bedrock."""

    def __init__(self, model_id: str = "amazon.titan-embed-text-v1", region: str = "us-east-1"):
        """
        Initialize Bedrock embeddings client.

        Args:
            model_id: Bedrock embedding model ID
            region: AWS region
        """
        self.model_id = model_id
        self.region = region
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of float values representing the embedding vector
        """
        try:
            # Prepare request body based on model
            if "titan" in self.model_id.lower():
                body = {
                    "inputText": text,
                }
            else:
                # Default format for other models
                body = {
                    "inputText": text,
                }

            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=str(body).replace("'", '"'),
                contentType="application/json",
                accept="application/json",
            )

            import json
            response_body = json.loads(response["body"].read())

            # Extract embedding based on model response format
            if "embedding" in response_body:
                return response_body["embedding"]
            elif "embeddings" in response_body and len(response_body["embeddings"]) > 0:
                return response_body["embeddings"][0]
            else:
                raise ValueError(f"Unexpected response format from {self.model_id}")

        except ClientError as e:
            logger.error(f"Bedrock API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for this model."""
        # Titan embeddings are typically 1536 dimensions
        if "titan" in self.model_id.lower():
            return 1536
        # Default fallback
        return 1536
