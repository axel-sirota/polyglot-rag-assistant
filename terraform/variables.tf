variable "project_name" {
  description = "Project name"
  type        = string
  default     = "polyglot-rag"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "dockerhub_username" {
  description = "Docker Hub username"
  type        = string
}

variable "dockerhub_password" {
  description = "Docker Hub password (optional if images are public)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "api_image_tag" {
  description = "Docker image tag for API"
  type        = string
  default     = "latest"
}

variable "agent_image_tag" {
  description = "Docker image tag for LiveKit Agent"
  type        = string
  default     = "latest"
}

variable "livekit_url" {
  description = "LiveKit WebSocket URL"
  type        = string
  default     = "wss://polyglot-rag-assistant-3l6xagej.livekit.cloud"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for ALB (optional - leave empty for HTTP only)"
  type        = string
  default     = ""
}

variable "cloudfront_certificate_arn" {
  description = "ACM certificate ARN for CloudFront (optional - leave empty for CloudFront domain)"
  type        = string
  default     = ""
}

variable "ui_domain_name" {
  description = "Domain name for UI"
  type        = string
  default     = "app.polyglot-rag.com"
}

# API Keys for services
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "amadeus_client_id" {
  description = "Amadeus API client ID"
  type        = string
  sensitive   = true
}

variable "amadeus_client_secret" {
  description = "Amadeus API client secret"
  type        = string
  sensitive   = true
}

variable "livekit_api_key" {
  description = "LiveKit API key"
  type        = string
  sensitive   = true
}

variable "livekit_api_secret" {
  description = "LiveKit API secret"
  type        = string
  sensitive   = true
}