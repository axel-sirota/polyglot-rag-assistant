terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
}

provider "aws" {
  region = var.aws_region
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
    PORT                  = "8000"
    HOST                  = "0.0.0.0"
    AMADEUS_BASE_URL     = "api.amadeus.com"
    OPENAI_API_KEY       = var.openai_api_key
    AMADEUS_CLIENT_ID    = var.amadeus_client_id
    AMADEUS_CLIENT_SECRET = var.amadeus_client_secret
    LIVEKIT_API_KEY      = var.livekit_api_key
    LIVEKIT_API_SECRET   = var.livekit_api_secret
  }
}

# LiveKit Agent Service
module "agent_service" {
  source = "./modules/ecs_service"
  
  project_name        = var.project_name
  environment         = var.environment
  service_name        = "livekit-agent"
  cluster_id          = module.ecs.cluster_id
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  target_group_arn    = null  # No ALB needed for agent
  
  container_image     = "${var.dockerhub_username}/polyglot-agent:${var.agent_image_tag}"
  container_port      = 8081  # Health check port
  cpu                 = 1024
  memory              = 2048
  desired_count       = 2
  
  environment_variables = {
    LIVEKIT_URL          = var.livekit_url
    LIVEKIT_API_KEY      = var.livekit_api_key
    LIVEKIT_API_SECRET   = var.livekit_api_secret
    OPENAI_API_KEY       = var.openai_api_key
    API_SERVER_URL       = "http://${module.alb.alb_dns_name}"
  }
}

# Note: UI deployment handled by Vercel - see scripts/deploy-ui-vercel.sh