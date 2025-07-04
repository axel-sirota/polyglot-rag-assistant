# Polyglot RAG Assistant - Complete Deployment Guide

## Prerequisites

1. **Accounts & CLI Tools**
   - AWS Account with CLI configured (`aws configure`)
   - Docker Hub account
   - LiveKit Cloud account
   - Terraform installed (v1.0+)
   - Docker installed
   - Node.js/npm (for UI if needed)

2. **Environment Variables**
   ```bash
   # Copy and update .env file
   cp .env.example .env
   # Edit with your values:
   # - DOCKER_USERNAME
   # - DOCKER_PASSWORD
   # - LIVEKIT_API_KEY
   # - LIVEKIT_API_SECRET
   # - AMADEUS_CLIENT_ID
   # - AMADEUS_CLIENT_SECRET
   # - OPENAI_API_KEY
   # - ANTHROPIC_API_KEY
   ```

## Step 1: Deploy LiveKit Agent

### Using LiveKit Dashboard (Recommended)
1. Go to https://cloud.livekit.io
2. Navigate to "Agents" → "Deploy New Agent"
3. Upload the livekit-agent directory
4. Configure environment variables
5. Deploy and note the WebSocket URL

### Using CLI (Alternative)
```bash
cd livekit-agent

# Create app using template
lk app create --template voice-pipeline-agent-python polyglot-rag-assistant

# Deploy
lk app deploy --app polyglot-rag-assistant
```

## Step 2: Deploy API to Docker Hub

```bash
# Make script executable
chmod +x scripts/deploy-api-docker.sh

# Deploy with tag
./scripts/deploy-api-docker.sh v1.0.0

# Or just latest
./scripts/deploy-api-docker.sh
```

## Step 3: Deploy Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="dockerhub_username=$DOCKER_USERNAME"

# Deploy everything
terraform apply -var="dockerhub_username=$DOCKER_USERNAME" -auto-approve
```

This creates:
- VPC with public/private subnets
- ECS Fargate cluster for API
- Application Load Balancer
- S3 bucket for UI hosting
- CloudFront distribution
- Secrets Manager for API keys

## Step 4: Update Configuration

After Terraform completes, get the outputs:
```bash
# Get API URL
API_URL=$(terraform output -raw api_url)

# Get CloudFront URL
CLOUDFRONT_URL=$(terraform output -raw cloudfront_url)

# Get S3 bucket name
S3_BUCKET=$(terraform output -raw ui_bucket_name)

# Get CloudFront distribution ID
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
```

## Step 5: Deploy UI to S3/CloudFront

```bash
# Update deployment script with your values
export S3_BUCKET=$S3_BUCKET
export CLOUDFRONT_DISTRIBUTION_ID=$CLOUDFRONT_ID
export API_URL=$API_URL
export LIVEKIT_URL="wss://your-app.livekit.cloud"  # From Step 1

# Make script executable
chmod +x scripts/deploy-ui-s3.sh

# Deploy UI
./scripts/deploy-ui-s3.sh
```

## Step 6: Verify Deployment

1. **Check API Health**
   ```bash
   curl $API_URL/health
   ```

2. **Test Token Generation**
   ```bash
   curl -X POST $API_URL/token \
     -H "Content-Type: application/json" \
     -d '{"identity": "test-user", "room_name": "test-room"}'
   ```

3. **Access UI**
   - Open CloudFront URL in browser: `https://$CLOUDFRONT_URL`
   - Or use custom domain if configured

4. **Check LiveKit Logs**
   ```bash
   lk cloud logs -f
   ```

## Quick Deploy Script

Create `deploy-all.sh`:
```bash
#!/bin/bash
set -e

echo "🚀 Starting complete deployment..."

# 1. Deploy API to Docker Hub
echo "📦 Building and pushing API..."
./scripts/deploy-api-docker.sh v1.0.0

# 2. Deploy infrastructure
echo "🏗️ Deploying infrastructure..."
cd terraform
terraform apply -var="dockerhub_username=$DOCKER_USERNAME" -auto-approve

# 3. Get outputs
API_URL=$(terraform output -raw api_url)
S3_BUCKET=$(terraform output -raw ui_bucket_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
CLOUDFRONT_URL=$(terraform output -raw cloudfront_url)

# 4. Deploy UI
echo "🎨 Deploying UI..."
cd ..
export S3_BUCKET API_URL CLOUDFRONT_DISTRIBUTION_ID=$CLOUDFRONT_ID
./scripts/deploy-ui-s3.sh

echo "✅ Deployment complete!"
echo "🌐 UI: https://$CLOUDFRONT_URL"
echo "🔧 API: $API_URL"
echo "📱 LiveKit: Check dashboard for agent status"
```

## Monitoring & Debugging

### Check ECS Logs
```bash
# List services
aws ecs list-services --cluster polyglot-rag-prod

# Get task ARN
TASK_ARN=$(aws ecs list-tasks --cluster polyglot-rag-prod --service-name polyglot-rag-prod-api | jq -r '.taskArns[0]')

# View logs
aws logs tail /ecs/polyglot-rag-prod/api --follow
```

### LiveKit Debugging
```bash
# View agent logs
lk cloud logs -f

# Test connection
lk room create test-room
lk room join test-room
```

### CloudFront Cache
```bash
# Invalidate cache after UI update
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_ID \
  --paths "/*"
```

## Rollback

If something goes wrong:
```bash
# Destroy infrastructure
cd terraform
terraform destroy -auto-approve

# Remove Docker images
docker rmi ${DOCKER_USERNAME}/polyglot-api:latest
```

## Cost Optimization

- ECS Fargate: ~$0.04/hour per task
- ALB: ~$0.025/hour + data transfer
- S3: ~$0.023/GB storage
- CloudFront: ~$0.085/GB transfer
- LiveKit: Check cloud.livekit.io for pricing

To reduce costs:
- Set `desired_count = 1` in terraform for dev
- Use t4g.nano for bastion host
- Enable S3 lifecycle policies

## Custom Domain (Optional)

1. Request ACM certificate in us-east-1:
   ```bash
   aws acm request-certificate \
     --domain-name polyglot-rag.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. Update Terraform variables:
   ```hcl
   domain_names = ["polyglot-rag.com"]
   certificate_arn = "arn:aws:acm:us-east-1:..."
   ```

3. Update Route53 after deployment

## Troubleshooting

### API Not Responding
- Check ECS task health
- Verify security groups allow ALB traffic
- Check Secrets Manager permissions

### UI Not Loading
- Verify S3 bucket policy
- Check CloudFront distribution status
- Clear browser cache

### LiveKit Connection Issues
- Verify API keys in agent environment
- Check CORS settings in API
- Ensure WebSocket traffic allowed

### Docker Push Fails
- Run `docker login` manually
- Check Docker Hub rate limits
- Verify repository exists

## Support

- LiveKit: https://docs.livekit.io
- AWS ECS: https://docs.aws.amazon.com/ecs/
- Issues: Create in GitHub repo