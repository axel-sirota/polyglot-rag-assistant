output "api_url" {
  description = "API endpoint URL"
  value       = "https://${module.alb.alb_dns_name}"
}

output "ui_url" {
  description = "UI CloudFront URL"
  value       = "https://${module.cloudfront.distribution_domain_name}"
}

output "ui_bucket_name" {
  description = "S3 bucket name for UI"
  value       = module.ui_bucket.bucket_id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "api_service_name" {
  description = "API ECS service name"
  value       = module.api_service.service_name
}