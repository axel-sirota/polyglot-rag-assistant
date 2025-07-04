#!/bin/bash
# Deploy to AWS ECS

echo "🚀 Deploying to AWS ECS"
echo "======================"

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REPO=${ECR_REPO:-your-account.dkr.ecr.us-east-1.amazonaws.com}
CLUSTER_NAME=${CLUSTER_NAME:-polyglot-cluster}
SERVICE_NAME=${SERVICE_NAME:-polyglot-voice-agent}

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Login to ECR
echo "1. Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO

# Build images
echo "2. Building Docker images..."
docker build -t polyglot-agent -f Dockerfile.agent .
docker build -t flight-api -f Dockerfile.api .

# Tag images
echo "3. Tagging images..."
docker tag polyglot-agent:latest $ECR_REPO/polyglot-agent:latest
docker tag flight-api:latest $ECR_REPO/flight-api:latest

# Push to ECR
echo "4. Pushing to ECR..."
docker push $ECR_REPO/polyglot-agent:latest
docker push $ECR_REPO/flight-api:latest

# Create task definition
echo "5. Creating ECS task definition..."
cat > task-definition.json << EOF
{
  "family": "polyglot-voice-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "voice-agent",
      "image": "$ECR_REPO/polyglot-agent:latest",
      "essential": true,
      "environment": [
        {"name": "LIVEKIT_URL", "value": "$LIVEKIT_URL"},
        {"name": "FLIGHT_API_URL", "value": "http://localhost:8765"}
      ],
      "secrets": [
        {
          "name": "LIVEKIT_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT:secret:livekit-api-key"
        },
        {
          "name": "LIVEKIT_API_SECRET",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT:secret:livekit-api-secret"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/polyglot-agent",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "agent"
        }
      }
    },
    {
      "name": "flight-api",
      "image": "$ECR_REPO/flight-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8765,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/polyglot-agent",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "api"
        }
      }
    }
  ]
}
EOF

# Register task definition
echo "6. Registering task definition..."
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region $AWS_REGION

# Create or update service
echo "7. Creating/updating ECS service..."
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --task-definition polyglot-voice-agent \
  --desired-count 2 \
  --force-new-deployment \
  --region $AWS_REGION || \
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition polyglot-voice-agent \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --region $AWS_REGION

# Setup auto-scaling
echo "8. Setting up auto-scaling..."
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/$CLUSTER_NAME/$SERVICE_NAME \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 10 \
  --region $AWS_REGION

aws application-autoscaling put-scaling-policy \
  --policy-name polyglot-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/$CLUSTER_NAME/$SERVICE_NAME \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 60
  }' \
  --region $AWS_REGION

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Check status:"
echo "aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION"
echo ""
echo "View logs:"
echo "aws logs tail /ecs/polyglot-agent --follow --region $AWS_REGION"