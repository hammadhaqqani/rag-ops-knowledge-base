# OpenSearch Serverless Collection
resource "aws_opensearchserverless_collection" "rag_ops_kb" {
  name = "rag-ops-kb-${var.environment}"

  type = "VECTORSEARCH"

  tags = {
    Name = "rag-ops-kb-${var.environment}"
  }
}

# OpenSearch Serverless Access Policy
resource "aws_opensearchserverless_access_policy" "rag_ops_access" {
  name        = "rag-ops-access-${var.environment}"
  type        = "data"
  description = "Access policy for RAG Ops Knowledge Base"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${aws_opensearchserverless_collection.rag_ops_kb.name}"
          ]
          ResourceType = "collection"
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
        },
        {
          Resource = [
            "index/${var.opensearch_index_name}/*"
          ]
          ResourceType = "index"
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ]
      Principal = [
        aws_iam_role.rag_ops_app_role.arn
      ]
    }
  ])
}

# OpenSearch Serverless Network Policy (if VPC is enabled)
resource "aws_opensearchserverless_security_policy" "rag_ops_network" {
  name        = "rag-ops-network-${var.environment}"
  type        = "network"
  description = "Network policy for RAG Ops Knowledge Base"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource = [
            "collection/${aws_opensearchserverless_collection.rag_ops_kb.name}"
          ]
        }
      ]
      AllowFromPublic = var.enable_vpc ? false : true
    }
  ])
}

# OpenSearch Serverless Encryption Policy
resource "aws_opensearchserverless_security_policy" "rag_ops_encryption" {
  name        = "rag-ops-encryption-${var.environment}"
  type        = "encryption"
  description = "Encryption policy for RAG Ops Knowledge Base"

  policy = jsonencode({
    AWSOwnedKey = true
  })
}
