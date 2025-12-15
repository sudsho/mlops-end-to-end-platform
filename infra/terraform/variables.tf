variable "region" {
  type    = string
  default = "us-east-1"
}

variable "platform_name" {
  type    = string
  default = "mlops-platform"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.medium"
}

variable "db_username" {
  type    = string
  default = "platform"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.small"
}

variable "private_subnet_ids" {
  type    = list(string)
  default = []
}
