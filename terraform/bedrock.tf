# Note: Bedrock models don't require explicit resources in Terraform
# Access is controlled via IAM policies
# This file documents the Bedrock configuration

# Data source to verify Bedrock model access
data "aws_bedrock_foundation_models" "available" {
  by_provider = "Anthropic"
}

# Output available models for reference
output "available_bedrock_models" {
  description = "Available Bedrock foundation models"
  value       = data.aws_bedrock_foundation_models.available.model_summaries[*].model_id
}
