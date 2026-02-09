# VPC for OpenSearch Serverless (optional)
resource "aws_vpc" "rag_ops_vpc" {
  count = var.enable_vpc ? 1 : 0

  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "rag-ops-vpc-${var.environment}"
  }
}

resource "aws_subnet" "rag_ops_subnet" {
  count = var.enable_vpc ? 2 : 0

  vpc_id            = aws_vpc.rag_ops_vpc[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "rag-ops-subnet-${count.index + 1}-${var.environment}"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_internet_gateway" "rag_ops_igw" {
  count = var.enable_vpc ? 1 : 0

  vpc_id = aws_vpc.rag_ops_vpc[0].id

  tags = {
    Name = "rag-ops-igw-${var.environment}"
  }
}

resource "aws_route_table" "rag_ops_rt" {
  count = var.enable_vpc ? 1 : 0

  vpc_id = aws_vpc.rag_ops_vpc[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.rag_ops_igw[0].id
  }

  tags = {
    Name = "rag-ops-rt-${var.environment}"
  }
}

resource "aws_route_table_association" "rag_ops_rta" {
  count = var.enable_vpc ? 2 : 0

  subnet_id      = aws_subnet.rag_ops_subnet[count.index].id
  route_table_id = aws_route_table.rag_ops_rt[0].id
}

resource "aws_vpc_endpoint" "opensearch" {
  count = var.enable_vpc ? 1 : 0

  vpc_id              = aws_vpc.rag_ops_vpc[0].id
  service_name        = "com.amazonaws.${var.aws_region}.aoss"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.rag_ops_subnet[*].id
  security_group_ids  = [aws_security_group.opensearch_endpoint[0].id]
  private_dns_enabled = true

  tags = {
    Name = "rag-ops-opensearch-endpoint-${var.environment}"
  }
}

resource "aws_security_group" "opensearch_endpoint" {
  count = var.enable_vpc ? 1 : 0

  name        = "rag-ops-opensearch-endpoint-${var.environment}"
  description = "Security group for OpenSearch Serverless VPC endpoint"
  vpc_id      = aws_vpc.rag_ops_vpc[0].id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rag-ops-opensearch-endpoint-sg-${var.environment}"
  }
}
