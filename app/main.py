"""FastAPI application for RAG Ops Knowledge Base."""

import logging
import time
from contextlib import asynccontextmanager


from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    IngestRequest,
    IngestResponse,
    HealthResponse,
    Source,
)
from app.ingestion.loader import DocumentLoader
from app.ingestion.chunker import Chunker
from app.ingestion.embeddings import BedrockEmbeddings
from app.retrieval.opensearch import OpenSearchClient
from app.retrieval.search import SemanticSearch
from app.generation.bedrock import BedrockLLM

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global clients
opensearch_client: OpenSearchClient = None
bedrock_embeddings: BedrockEmbeddings = None
bedrock_llm: BedrockLLM = None
semantic_search: SemanticSearch = None
document_loader: DocumentLoader = None
chunker: Chunker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global opensearch_client, bedrock_embeddings, bedrock_llm, semantic_search
    global document_loader, chunker

    # Startup
    logger.info("Initializing RAG Ops Knowledge Base API...")
    try:
        # Initialize OpenSearch client
        opensearch_client = OpenSearchClient(
            endpoint=settings.opensearch_url,
            index_name=settings.opensearch_index_name,
            region=settings.aws_region,
        )
        await opensearch_client.initialize()

        # Initialize Bedrock embeddings
        bedrock_embeddings = BedrockEmbeddings(
            model_id=settings.bedrock_embedding_model_id,
            region=settings.aws_region,
        )

        # Initialize Bedrock LLM
        bedrock_llm = BedrockLLM(
            model_id=settings.bedrock_model_id,
            region=settings.aws_region,
            max_tokens=settings.bedrock_max_tokens,
            temperature=settings.bedrock_temperature,
        )

        # Initialize semantic search
        semantic_search = SemanticSearch(
            opensearch_client=opensearch_client,
            embeddings=bedrock_embeddings,
        )

        # Initialize document loader and chunker
        document_loader = DocumentLoader()
        chunker = Chunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            strategy=settings.chunk_strategy,
        )

        logger.info("API initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAG Ops Knowledge Base API...")
    if opensearch_client:
        await opensearch_client.close()


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "RAG Ops Knowledge Base API",
        "version": settings.api_version,
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        opensearch_status = False
        bedrock_status = False

        if opensearch_client:
            opensearch_status = await opensearch_client.health_check()

        if bedrock_llm:
            bedrock_status = await bedrock_llm.check_availability()

        return HealthResponse(
            status="healthy" if (opensearch_status and bedrock_status) else "degraded",
            opensearch_connected=opensearch_status,
            bedrock_available=bedrock_status,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            opensearch_connected=False,
            bedrock_available=False,
        )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base with natural language."""
    if not semantic_search or not bedrock_llm:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized",
        )

    start_time = time.time()

    try:
        # Perform semantic search
        search_results = await semantic_search.search(
            query=request.query,
            max_results=request.max_results or settings.max_search_results,
            min_score=request.min_score or settings.min_similarity_score,
        )

        if not search_results:
            return QueryResponse(
                answer="I couldn't find any relevant information in the knowledge base for your query.",
                sources=[],
                query_time_ms=(time.time() - start_time) * 1000,
                total_results=0,
            )

        # Prepare context from search results
        context = "\n\n".join([result["content"] for result in search_results])

        # Generate answer using Bedrock LLM
        answer = await bedrock_llm.generate(
            prompt=f"""You are a helpful DevOps assistant. Answer the following question using only the provided context from the knowledge base.

Context:
{context}

Question: {request.query}

Answer:""",
        )

        # Format sources
        sources = [
            Source(
                document=result.get("document", "unknown"),
                chunk_id=result.get("chunk_id", ""),
                score=result.get("score", 0.0),
                content=(
                    result.get("content", "")[:500] + "..."
                    if len(result.get("content", "")) > 500
                    else result.get("content", "")
                ),
                metadata=result.get("metadata"),
            )
            for result in search_results
        ]

        query_time_ms = (time.time() - start_time) * 1000

        return QueryResponse(
            answer=answer,
            sources=sources,
            query_time_ms=round(query_time_ms, 2),
            total_results=len(search_results),
        )

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        )


@app.post("/ingest", response_model=IngestResponse, tags=["Ingest"])
async def ingest_document(request: IngestRequest):
    """Ingest a document into the knowledge base."""
    if (
        not document_loader
        or not chunker
        or not bedrock_embeddings
        or not opensearch_client
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized",
        )

    try:
        # Load document
        document_content = await document_loader.load(request.document_path)
        if not document_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load document: {request.document_path}",
            )

        # Chunk document
        chunks = await chunker.chunk(
            text=document_content["content"],
            metadata={
                "document_name": document_content.get("name", request.document_path),
                **(request.metadata or {}),
            },
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No chunks created from document",
            )

        # Generate embeddings and index chunks
        chunks_indexed = 0
        document_id = f"doc_{int(time.time())}"

        for idx, chunk in enumerate(chunks):
            # Generate embedding
            embedding = await bedrock_embeddings.embed_text(chunk["text"])

            # Index in OpenSearch
            chunk_id = f"{document_id}_chunk_{idx}"
            await opensearch_client.index_document(
                document_id=chunk_id,
                text=chunk["text"],
                embedding=embedding,
                metadata={
                    "document_id": document_id,
                    "chunk_index": idx,
                    "document_name": chunk.get("metadata", {}).get(
                        "document_name", request.document_path
                    ),
                    **(chunk.get("metadata", {})),
                },
            )
            chunks_indexed += 1

        return IngestResponse(
            status="success",
            document_id=document_id,
            chunks_created=chunks_indexed,
            message=f"Successfully ingested {chunks_indexed} chunks from {request.document_path}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
