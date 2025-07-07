variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "service_name" {
  description = "Service name"
  type        = string
}

variable "cluster_id" {
  description = "ECS cluster ID"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for service"
  type        = list(string)
}

variable "target_group_arn" {
  description = "Target group ARN (optional - set to null for services without ALB)"
  type        = string
  default     = null
}

variable "container_image" {
  description = "Container image"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
}

variable "cpu" {
  description = "CPU units"
  type        = number
}

variable "memory" {
  description = "Memory in MB"
  type        = number
}

variable "desired_count" {
  description = "Desired task count"
  type        = number
}

variable "environment_variables" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

