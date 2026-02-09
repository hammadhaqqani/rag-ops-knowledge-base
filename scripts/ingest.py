#!/usr/bin/env python3
"""CLI script to ingest documents into the RAG Ops Knowledge Base."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.ingestion.loader import DocumentLoader
from app.ingestion.chunker import Chunker
from app.ingestion.embeddings import BedrockEmbeddings
from app.retrieval.opensearch import OpenSearchClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def ingest_document(
    file_path: str,
    metadata: dict = None,
    chunk_strategy: str = "fixed",
):
    """Ingest a single document."""
    try:
        # Initialize components
        loader = DocumentLoader()
        chunker = Chunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            strategy=chunk_strategy,
        )
        embeddings = BedrockEmbeddings(
            model_id=settings.bedrock_embedding_model_id,
            region=settings.aws_region,
        )
        opensearch_client = OpenSearchClient(
            endpoint=settings.opensearch_url,
            index_name=settings.opensearch_index_name,
            region=settings.aws_region,
        )

        await opensearch_client.initialize()

        # Load document
        logger.info(f"Loading document: {file_path}")
        document = await loader.load(file_path)
        if not document:
            logger.error(f"Failed to load document: {file_path}")
            return False

        # Chunk document
        logger.info("Chunking document...")
        chunks = await chunker.chunk(
            text=document["content"],
            metadata={
                "document_name": document["name"],
                **(metadata or {}),
            },
        )
        logger.info(f"Created {len(chunks)} chunks")

        # Generate embeddings and index
        logger.info("Generating embeddings and indexing...")
        chunks_indexed = 0
        import time

        document_id = f"doc_{int(time.time())}"

        for idx, chunk in enumerate(chunks):
            try:
                embedding = await embeddings.embed_text(chunk["text"])
                chunk_id = f"{document_id}_chunk_{idx}"
                await opensearch_client.index_document(
                    document_id=chunk_id,
                    text=chunk["text"],
                    embedding=embedding,
                    metadata={
                        "document_id": document_id,
                        "chunk_index": idx,
                        "document_name": document["name"],
                        **(chunk.get("metadata", {})),
                    },
                )
                chunks_indexed += 1
                if (idx + 1) % 10 == 0:
                    logger.info(f"Indexed {idx + 1}/{len(chunks)} chunks...")
            except Exception as e:
                logger.error(f"Error indexing chunk {idx}: {e}", exc_info=True)

        logger.info(f"Successfully ingested {chunks_indexed} chunks from {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error ingesting document: {e}", exc_info=True)
        return False


async def ingest_directory(directory_path: str, chunk_strategy: str = "fixed"):
    """Ingest all documents from a directory."""
    loader = DocumentLoader()
    documents = await loader.load_directory(directory_path)

    if not documents:
        logger.warning(f"No documents found in {directory_path}")
        return

    logger.info(f"Found {len(documents)} documents to ingest")

    success_count = 0
    for doc in documents:
        success = await ingest_document(
            file_path=doc["path"],
            metadata={"source_directory": directory_path},
            chunk_strategy=chunk_strategy,
        )
        if success:
            success_count += 1

    logger.info(f"Successfully ingested {success_count}/{len(documents)} documents")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest documents into RAG Ops Knowledge Base"
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to document file or directory",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["fixed", "semantic"],
        default="fixed",
        help="Chunking strategy (default: fixed)",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Category metadata for documents",
    )

    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        logger.error(f"Path does not exist: {args.path}")
        sys.exit(1)

    if path.is_file():
        metadata = {}
        if args.category:
            metadata["category"] = args.category
        success = await ingest_document(
            file_path=str(path),
            metadata=metadata if metadata else None,
            chunk_strategy=args.strategy,
        )
        sys.exit(0 if success else 1)
    elif path.is_dir():
        await ingest_directory(str(path), chunk_strategy=args.strategy)
    else:
        logger.error(f"Invalid path: {args.path}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
