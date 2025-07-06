#!/bin/bash
# Deploy LiveKit Agent to ECS

set -e

echo "🚀 Deploying LiveKit Agent to ECS"
echo "================================="

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="polyglot-agent"
CLUSTER_NAME="polyglot-rag-cluster"
SERVICE_NAME="polyglot-agent-service"
TASK_FAMILY="polyglot-agent"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo "📦 Building Docker image..."
cd polyglot-flight-agent
docker build -t ${ECR_REPOSITORY}:latest .

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

# Create repository if it doesn't exist
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} || \
    aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${AWS_REGION}

echo "📤 Pushing image to ECR..."
docker tag ${ECR_REPOSITORY}:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

echo "📝 Updating task definition..."
# Update the task definition with the correct account ID and ECR URI
sed -e "s/YOUR_ACCOUNT_ID/${AWS_ACCOUNT_ID}/g" \
    -e "s|YOUR_ECR_URI|${ECR_URI}|g" \
    ../ecs-agent-task-definition.json > /tmp/agent-task-def.json

# Register the task definition
TASK_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/agent-task-def.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "✅ Task definition registered: ${TASK_ARN}"

# Check if service exists
if aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${SERVICE_NAME} --query 'services[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
    echo "🔄 Updating existing service..."
    aws ecs update-service \
        --cluster ${CLUSTER_NAME} \
        --service ${SERVICE_NAME} \
        --task-definition ${TASK_FAMILY} \
        --force-new-deployment
else
    echo "🆕 Creating new service..."
    # Get subnet IDs from the existing cluster
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters "Name=tag:Name,Values=*polyglot-rag*" \
        --query 'Subnets[*].SubnetId' \
        --output text | tr '\t' ',')
    
    # Get security group
    SECURITY_GROUP=$(aws ec2 describe-security-groups \
        --filters "Name=tag:Name,Values=*polyglot-rag*" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
    
    aws ecs create-service \
        --cluster ${CLUSTER_NAME} \
        --service-name ${SERVICE_NAME} \
        --task-definition ${TASK_FAMILY} \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_IDS}],securityGroups=[${SECURITY_GROUP}],assignPublicIp=ENABLED}"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Monitor deployment:"
echo "aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${SERVICE_NAME}"
echo ""
echo "📋 View logs:"
echo "aws logs tail /ecs/polyglot-agent --follow"