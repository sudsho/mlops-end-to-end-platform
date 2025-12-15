resource "aws_db_subnet_group" "platform" {
  name       = "${var.platform_name}-db-subnets"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_subnet_group" "platform" {
  name       = "${var.platform_name}-redis-subnets"
  subnet_ids = var.private_subnet_ids
}

resource "aws_security_group" "platform_pg" {
  name        = "${var.platform_name}-pg"
  description = "platform postgres"
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "platform_redis" {
  name        = "${var.platform_name}-redis"
  description = "platform redis"
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "eks_role" {
  name = "${var.platform_name}-eks-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}
