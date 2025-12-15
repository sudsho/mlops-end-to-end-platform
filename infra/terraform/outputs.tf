output "rds_endpoint" {
  value     = aws_db_instance.platform_pg.endpoint
  sensitive = false
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.platform_redis.cache_nodes[0].address
}

output "s3_artifact_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}

output "ecs_cluster_arn" {
  value = aws_ecs_cluster.orchestrator.arn
}

output "eks_cluster_name" {
  value = aws_eks_cluster.serving.name
}
