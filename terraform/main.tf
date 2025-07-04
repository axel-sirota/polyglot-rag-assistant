terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
  
  backend "s3" {
    bucket = "polyglot-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

provider "docker" {
  registry_auth {
    address  = "registry.hub.docker.com"
    username = var.dockerhub_username
    password = var.dockerhub_password
  }
}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
}

# ECS Cluster
module "ecs" {
  source = "./modules/ecs"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnet_ids
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  certificate_arn     = var.certificate_arn
}

# API Service
module "api_service" {
  source = "./modules/ecs_service"
  
  project_name        = var.project_name
  environment         = var.environment
  service_name        = "api"
  cluster_id          = module.ecs.cluster_id
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  target_group_arn    = module.alb.api_target_group_arn
  
  container_image     = "${var.dockerhub_username}/polyglot-api:${var.api_image_tag}"
  container_port      = 8000
  cpu                 = 512
  memory              = 1024
  desired_count       = 2
  
  environment_variables = {
    PORT = "8000"
    HOST = "0.0.0.0"
    AMADEUS_BASE_URL = "api.amadeus.com"
  }
  
  secrets = {
    OPENAI_API_KEY        = aws_secretsmanager_secret.openai_api_key.arn
    AMADEUS_CLIENT_ID     = aws_secretsmanager_secret.amadeus_client_id.arn
    AMADEUS_CLIENT_SECRET = aws_secretsmanager_secret.amadeus_client_secret.arn
    LIVEKIT_API_KEY       = aws_secretsmanager_secret.livekit_api_key.arn
    LIVEKIT_API_SECRET    = aws_secretsmanager_secret.livekit_api_secret.arn
  }
}

# S3 Bucket for Static UI
module "ui_bucket" {
  source = "./modules/s3_static_site"
  
  project_name = var.project_name
  environment  = var.environment
  domain_name  = var.ui_domain_name
}

# CloudFront for UI
module "cloudfront" {
  source = "./modules/cloudfront"
  
  project_name        = var.project_name
  environment         = var.environment
  s3_bucket_domain    = module.ui_bucket.bucket_regional_domain_name
  s3_bucket_id        = module.ui_bucket.bucket_id
  certificate_arn     = var.cloudfront_certificate_arn
  domain_names        = [var.ui_domain_name]
}

# Secrets Manager
resource "aws_secretsmanager_secret" "openai_api_key" {
  name = "${var.project_name}-${var.environment}-openai-api-key"
}

resource "aws_secretsmanager_secret" "amadeus_client_id" {
  name = "${var.project_name}-${var.environment}-amadeus-client-id"
}

resource "aws_secretsmanager_secret" "amadeus_client_secret" {
  name = "${var.project_name}-${var.environment}-amadeus-client-secret"
}

resource "aws_secretsmanager_secret" "livekit_api_key" {
  name = "${var.project_name}-${var.environment}-livekit-api-key"
}

resource "aws_secretsmanager_secret" "livekit_api_secret" {
  name = "${var.project_name}-${var.environment}-livekit-api-secret"
}