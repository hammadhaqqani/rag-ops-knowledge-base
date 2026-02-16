# RAG Ops Knowledge Base

[![CI](https://github.com/hammadhaqqani/rag-ops-knowledge-base/actions/workflows/ci.yml/badge.svg)](https://github.com/hammadhaqqani/rag-ops-knowledge-base/actions/workflows/ci.yml)
[![GitHub Pages](https://github.com/hammadhaqqani/rag-ops-knowledge-base/actions/workflows/pages.yml/badge.svg)](https://hammadhaqqani.github.io/rag-ops-knowledge-base/)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)

A Retrieval-Augmented Generation (RAG) system for DevOps knowledge management. Ingest runbooks, incident playbooks, and documentation, then query them using natural language via a FastAPI endpoint.

## Architecture

```
┌─────────────┐
│  Documents  │ (Markdown, PDF, Text)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Chunker   │ (Fixed-size, Semantic)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Bedrock    │ (Titan Embeddings)
│ Embeddings  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ OpenSearch       │ (Vector Store)
│ Serverless       │
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│    Query    │ (Natural Language)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Bedrock   │ (Claude LLM)
│     LLM     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Response   │ (Contextual Answer)
└─────────────┘
```

## Features

- **Document Ingestion**: Support for Markdown, PDF, and plain text documents
- **Intelligent Chunking**: Fixed-size and semantic chunking strategies
- **Vector Search**: AWS Bedrock Titan embeddings with OpenSearch Serverless
- **Natural Language Queries**: FastAPI endpoint for conversational queries
- **LLM Integration**: AWS Bedrock Claude models for response generation
- **Infrastructure as Code**: Complete Terraform configuration for AWS resources
- **Docker Support**: Containerized deployment with docker-compose
- **CLI Tools**: Command-line scripts for ingestion and querying

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Docker and Docker Compose installed
- Python 3.11 or higher
- Terraform 1.5+ (for infrastructure deployment)

## Quick Start

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/hammadhaqqani/rag-ops-knowledge-base.git
   cd rag-ops-knowledge-base
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**:
   ```bash
   export AWS_REGION=us-east-1
   export OPENSEARCH_COLLECTION_ENDPOINT=https://your-collection.us-east-1.aoss.amazonaws.com
   export BEDROCK_MODEL_ID=anthropic.claude-v2
   ```

4. **Run the FastAPI application**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Ingest sample runbooks**:
   ```bash
   python scripts/ingest.py --directory data/sample-runbooks
   ```

6. **Query the knowledge base**:
   ```bash
   python scripts/query.py "How do I recover an EC2 instance?"
   ```

### AWS Deployment

1. **Deploy infrastructure**:
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

2. **Get outputs**:
   ```bash
   terraform output opensearch_endpoint
   terraform output iam_role_arn
   ```

3. **Configure environment**:
   ```bash
   export OPENSEARCH_COLLECTION_ENDPOINT=$(terraform output -raw opensearch_endpoint)
   export AWS_REGION=$(terraform output -raw aws_region)
   ```

4. **Deploy application** (ECS, Lambda, or EC2):
   ```bash
   docker build -t rag-ops-kb .
   docker push <your-ecr-repo>/rag-ops-kb:latest
   ```

## API Documentation

### Endpoints

#### `POST /query`
Query the knowledge base with natural language.

**Request Body**:
```json
{
  "query": "How do I troubleshoot high CPU usage?",
  "max_results": 5,
  "min_score": 0.7
}
```

**Response**:
```json
{
  "answer": "To troubleshoot high CPU usage, first identify the process...",
  "sources": [
    {
      "document": "high-cpu-troubleshooting.md",
      "chunk_id": "chunk_123",
      "score": 0.89,
      "content": "Check top processes using 'top' or 'htop'..."
    }
  ],
  "query_time_ms": 245
}
```

#### `POST /ingest`
Ingest a document into the knowledge base.

**Request Body**:
```json
{
  "document_path": "/path/to/runbook.md",
  "metadata": {
    "category": "incident-response",
    "author": "ops-team"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "chunks_created": 15,
  "document_id": "doc_abc123"
}
```

#### `GET /health`
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "opensearch_connected": true,
  "bedrock_available": true
}
```

## Configuration

The application uses environment variables for configuration:

- `AWS_REGION`: AWS region (default: `us-east-1`)
- `OPENSEARCH_COLLECTION_ENDPOINT`: OpenSearch Serverless collection endpoint
- `OPENSEARCH_INDEX_NAME`: Index name (default: `rag-ops-kb`)
- `BEDROCK_MODEL_ID`: Bedrock model ID (default: `anthropic.claude-v2`)
- `BEDROCK_EMBEDDING_MODEL_ID`: Embedding model ID (default: `amazon.titan-embed-text-v1`)
- `CHUNK_SIZE`: Chunk size for text splitting (default: `1000`)
- `CHUNK_OVERLAP`: Overlap between chunks (default: `200`)
- `MAX_SEARCH_RESULTS`: Maximum search results (default: `5`)
- `MIN_SIMILARITY_SCORE`: Minimum similarity score threshold (default: `0.7`)

## Sample Queries

- "How do I recover a failed EC2 instance?"
- "What's the procedure for RDS failover?"
- "How do I troubleshoot Kubernetes pod crash loops?"
- "What are the steps to resolve high CPU issues?"
- "Show me the incident response playbook for database outages"

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- AWS Bedrock for LLM and embedding capabilities
- OpenSearch Serverless for vector search
- FastAPI for the web framework
- The DevOps community for inspiration
---

## Support

If you find this useful, consider buying me a coffee!

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/hammadhaqqani)
