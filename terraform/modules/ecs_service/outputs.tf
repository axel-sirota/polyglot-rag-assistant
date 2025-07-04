output "service_name" {
  value = aws_ecs_service.service.name
}

output "service_id" {
  value = aws_ecs_service.service.id
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.service.arn
}