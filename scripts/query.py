#!/usr/bin/env python3
"""CLI script to query the RAG Ops Knowledge Base."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.ingestion.embeddings import BedrockEmbeddings
from app.retrieval.opensearch import OpenSearchClient
from app.retrieval.search import SemanticSearch
from app.generation.bedrock import BedrockLLM

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def query_knowledge_base(
    query: str,
    max_results: int = 5,
    min_score: float = 0.7,
    generate_answer: bool = True,
):
    """Query the knowledge base."""
    try:
        # Initialize components
        opensearch_client = OpenSearchClient(
            endpoint=settings.opensearch_url,
            index_name=settings.opensearch_index_name,
            region=settings.aws_region,
        )
        embeddings = BedrockEmbeddings(
            model_id=settings.bedrock_embedding_model_id,
            region=settings.aws_region,
        )
        semantic_search = SemanticSearch(
            opensearch_client=opensearch_client,
            embeddings=embeddings,
        )

        # Perform search
        logger.info(f"Searching for: {query}")
        results = await semantic_search.search(
            query=query,
            max_results=max_results,
            min_score=min_score,
        )

        if not results:
            print("No results found.")
            return

        # Display results
        print(f"\nFound {len(results)} results:\n")
        print("=" * 80)

        for idx, result in enumerate(results, 1):
            print(f"\nResult {idx}:")
            print(f"Document: {result['document']}")
            print(f"Score: {result['score']:.3f}")
            print(f"Content: {result['content'][:200]}...")
            print("-" * 80)

        # Generate answer if requested
        if generate_answer and results:
            logger.info("Generating answer using Bedrock LLM...")
            bedrock_llm = BedrockLLM(
                model_id=settings.bedrock_model_id,
                region=settings.aws_region,
            )

            context = "\n\n".join([r["content"] for r in results])
            prompt = f"""You are a helpful DevOps assistant. Answer the following question using only the provided context from the knowledge base.

Context:
{context}

Question: {query}

Answer:"""

            answer = await bedrock_llm.generate(prompt)

            print("\n" + "=" * 80)
            print("GENERATED ANSWER:")
            print("=" * 80)
            print(answer)
            print("=" * 80)

    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}", exc_info=True)
        raise


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query RAG Ops Knowledge Base")
    parser.add_argument(
        "query",
        type=str,
        help="Natural language query",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of results (default: 5)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.7,
        help="Minimum similarity score (default: 0.7)",
    )
    parser.add_argument(
        "--no-answer",
        action="store_true",
        help="Don't generate LLM answer, only show search results",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    try:
        results = await query_knowledge_base(
            query=args.query,
            max_results=args.max_results,
            min_score=args.min_score,
            generate_answer=not args.no_answer,
        )

        if args.json:
            # This would require modifying the function to return results
            print(json.dumps(results, indent=2))

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
