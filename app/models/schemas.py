"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Source document information."""

    document: str = Field(..., description="Document name or path")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    content: str = Field(..., description="Chunk content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class QueryRequest(BaseModel):
    """Request model for querying the knowledge base."""

    query: str = Field(..., min_length=1, description="Natural language query")
    max_results: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of results")
    min_score: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    include_metadata: Optional[bool] = Field(True, description="Include metadata in response")


class QueryResponse(BaseModel):
    """Response model for query results."""

    answer: str = Field(..., description="Generated answer from the knowledge base")
    sources: List[Source] = Field(..., description="Source documents used for the answer")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
    total_results: int = Field(..., description="Total number of results found")


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""

    document_id: str
    chunk_index: int
    document_name: str
    category: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    tags: Optional[List[str]] = None


class IngestRequest(BaseModel):
    """Request model for ingesting documents."""

    document_path: str = Field(..., description="Path to the document file")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the document")
    chunk_strategy: Optional[str] = Field("fixed", description="Chunking strategy: 'fixed' or 'semantic'")


class IngestResponse(BaseModel):
    """Response model for ingestion results."""

    status: str = Field(..., description="Ingestion status")
    document_id: str = Field(..., description="Unique document identifier")
    chunks_created: int = Field(..., ge=0, description="Number of chunks created")
    message: Optional[str] = Field(None, description="Additional message")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    opensearch_connected: bool = Field(..., description="OpenSearch connection status")
    bedrock_available: bool = Field(..., description="Bedrock availability status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
