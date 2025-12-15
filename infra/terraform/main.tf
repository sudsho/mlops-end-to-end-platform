terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "mlops-platform-tfstate"
    key    = "platform/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.region
}

# RDS for Postgres (feast registry + offline + mlflow + prefect)
resource "aws_db_instance" "platform_pg" {
  identifier              = "${var.platform_name}-pg"
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = var.db_instance_class
  allocated_storage       = 50
  storage_encrypted       = true
  db_name                 = "platform"
  username                = var.db_username
  password                = var.db_password
  vpc_security_group_ids  = [aws_security_group.platform_pg.id]
  db_subnet_group_name    = aws_db_subnet_group.platform.name
  backup_retention_period = 7
  deletion_protection     = false
  skip_final_snapshot     = true
  apply_immediately       = true
}

resource "aws_elasticache_cluster" "platform_redis" {
  cluster_id           = "${var.platform_name}-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.platform.name
  security_group_ids   = [aws_security_group.platform_redis.id]
}

resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.platform_name}-artifacts"
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_ecs_cluster" "orchestrator" {
  name = "${var.platform_name}-orchestrator"
}

# EKS cluster handle for KServe (the actual KServe install lives in helm)
resource "aws_eks_cluster" "serving" {
  name     = "${var.platform_name}-serving"
  role_arn = aws_iam_role.eks_role.arn
  version  = "1.31"
  vpc_config {
    subnet_ids = var.private_subnet_ids
  }
}
