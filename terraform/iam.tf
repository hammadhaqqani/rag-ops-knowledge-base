# IAM Role for Application
resource "aws_iam_role" "rag_ops_app_role" {
  name = "rag-ops-app-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "ecs-tasks.amazonaws.com",
            "lambda.amazonaws.com",
            "ec2.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "rag-ops-app-role-${var.environment}"
  }
}

# IAM Policy for OpenSearch Serverless
resource "aws_iam_role_policy" "opensearch_policy" {
  name = "rag-ops-opensearch-policy-${var.environment}"
  role = aws_iam_role.rag_ops_app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = aws_opensearchserverless_collection.rag_ops_kb.arn
      },
      {
        Effect = "Allow"
        Action = [
          "aoss:CreateCollectionItems",
          "aoss:DeleteCollectionItems",
          "aoss:UpdateCollectionItems",
          "aoss:DescribeCollectionItems"
        ]
        Resource = "${aws_opensearchserverless_collection.rag_ops_kb.arn}/*"
      }
    ]
  })
}

# IAM Policy for Bedrock
resource "aws_iam_role_policy" "bedrock_policy" {
  name = "rag-ops-bedrock-policy-${var.environment}"
  role = aws_iam_role.rag_ops_app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_model_id}",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_embedding_model_id}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:ListFoundationModels"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy" "cloudwatch_logs_policy" {
  name = "rag-ops-cloudwatch-logs-policy-${var.environment}"
  role = aws_iam_role.rag_ops_app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/rag-ops-kb/*"
      }
    ]
  })
}

# Attach AWS managed policy for basic execution
resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.rag_ops_app_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
