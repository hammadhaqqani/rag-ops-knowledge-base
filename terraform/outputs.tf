output "opensearch_endpoint" {
  description = "OpenSearch Serverless collection endpoint"
  value       = aws_opensearchserverless_collection.rag_ops_kb.collection_endpoint
}

output "opensearch_collection_id" {
  description = "OpenSearch Serverless collection ID"
  value       = aws_opensearchserverless_collection.rag_ops_kb.id
}

output "opensearch_collection_arn" {
  description = "OpenSearch Serverless collection ARN"
  value       = aws_opensearchserverless_collection.rag_ops_kb.arn
}

output "iam_role_arn" {
  description = "IAM role ARN for application access"
  value       = aws_iam_role.rag_ops_app_role.arn
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "vpc_id" {
  description = "VPC ID (if VPC is enabled)"
  value       = var.enable_vpc ? aws_vpc.rag_ops_vpc[0].id : null
}

output "vpc_endpoint_id" {
  description = "VPC endpoint ID for OpenSearch (if VPC is enabled)"
  value       = var.enable_vpc ? aws_vpc_endpoint.opensearch[0].id : null
}
