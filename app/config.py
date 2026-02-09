"""Configuration management for the RAG Ops Knowledge Base."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # OpenSearch Configuration
    opensearch_collection_endpoint: str
    opensearch_index_name: str = "rag-ops-kb"
    opensearch_timeout: int = 30

    # Bedrock Configuration
    bedrock_model_id: str = "anthropic.claude-v2"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v1"
    bedrock_max_tokens: int = 4096
    bedrock_temperature: float = 0.7

    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunk_strategy: str = "fixed"  # "fixed" or "semantic"

    # Search Configuration
    max_search_results: int = 5
    min_similarity_score: float = 0.7

    # Application Configuration
    log_level: str = "INFO"
    api_title: str = "RAG Ops Knowledge Base API"
    api_version: str = "0.1.0"
    api_description: str = "RAG-powered DevOps knowledge base API"

    @property
    def opensearch_url(self) -> str:
        """Get the full OpenSearch URL."""
        if not self.opensearch_collection_endpoint.startswith("https://"):
            return f"https://{self.opensearch_collection_endpoint}"
        return self.opensearch_collection_endpoint

    def get_aws_credentials(self) -> dict:
        """Get AWS credentials dictionary."""
        creds = {}
        if self.aws_access_key_id:
            creds["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            creds["aws_secret_access_key"] = self.aws_secret_access_key
        return creds


# Global settings instance
settings = Settings()
