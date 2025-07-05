output "api_url" {
  description = "API endpoint URL"
  value       = "http://${module.alb.alb_dns_name}"
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "api_service_name" {
  description = "API ECS service name"
  value       = module.api_service.service_name
}

output "vercel_deployment_note" {
  description = "Instructions for deploying UI"
  value       = "Deploy UI to Vercel using: ./scripts/deploy-ui-vercel.sh"
}