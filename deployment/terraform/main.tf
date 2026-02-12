# Cortex Core Enterprise Infrastructure
# AWS Terraform Configuration

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "cortex-core-terraform-state"
    key    = "cortex-core-enterprise.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Configuration
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "cortex-core-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = false

  tags = {
    Environment = var.environment
    Project     = "cortex-core"
  }
}

# Security Groups
resource "aws_security_group" "cortex_core" {
  name_prefix = "cortex-core-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "cortex-core-sg"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "cortex-core-${var.environment}"
  cluster_version = "1.27"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    cortex_core = {
      min_size     = 3
      max_size     = 10
      desired_size = 3

      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"

      tags = {
        Environment = var.environment
        Project     = "cortex-core"
      }
    }
  }

  tags = {
    Environment = var.environment
    Project     = "cortex-core"
  }
}

# RDS Database
resource "aws_db_instance" "cortex_core" {
  identifier             = "cortex-core-${var.environment}"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "15.3"
  username               = "cortex"
  password               = var.db_password
  db_name                = "cortex"
  vpc_security_group_ids = [aws_security_group.cortex_core.id]
  db_subnet_group_name   = aws_db_subnet_group.cortex_core.name
  publicly_accessible    = false
  skip_final_snapshot    = true

  tags = {
    Name        = "cortex-core-db"
    Environment = var.environment
  }
}

resource "aws_db_subnet_group" "cortex_core" {
  name       = "cortex-core-${var.environment}"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name        = "cortex-core-db-subnet"
    Environment = var.environment
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "cortex_core" {
  cluster_id           = "cortex-core-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  security_group_ids   = [aws_security_group.cortex_core.id]
  subnet_group_name    = aws_elasticache_subnet_group.cortex_core.name

  tags = {
    Name        = "cortex-core-redis"
    Environment = var.environment
  }
}

resource "aws_elasticache_subnet_group" "cortex_core" {
  name       = "cortex-core-${var.environment}"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name        = "cortex-core-redis-subnet"
    Environment = var.environment
  }
}

# S3 Bucket for backups
resource "aws_s3_bucket" "cortex_core_backups" {
  bucket = "cortex-core-${var.environment}-backups"

  tags = {
    Name        = "cortex-core-backups"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "cortex_core_backups" {
  bucket = aws_s3_bucket.cortex_core_backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "cortex_core" {
  name              = "/aws/cortex-core/${var.environment}"
  retention_in_days = 30

  tags = {
    Name        = "cortex-core-logs"
    Environment = var.environment
  }
}

# Outputs
output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID for the cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_name" {
  description = "Kubernetes cluster name"
  value       = module.eks.cluster_name
}

output "db_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.cortex_core.endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = aws_elasticache_cluster.cortex_core.cache_nodes[0].address
}

output "s3_backup_bucket" {
  description = "S3 backup bucket name"
  value       = aws_s3_bucket.cortex_core_backups.bucket
}
