# Polyglot RAG Assistant - Complete Deployment Guide

## Prerequisites

1. **Accounts & CLI Tools**
   - AWS Account with CLI configured (`aws configure`)
   - Docker Hub account
   - LiveKit Cloud account
   - Vercel account
   - Terraform installed (v1.0+)
   - Docker installed
   - Node.js/npm (for Vercel CLI)

2. **Environment Variables**
   ```bash
   # Copy and update .env file
   cp .env.example .env
   # Edit with your values:
   # - DOCKER_USERNAME
   # - DOCKER_PASSWORD
   # - LIVEKIT_API_KEY
   # - LIVEKIT_API_SECRET
   # - LIVEKIT_URL
   # - AMADEUS_CLIENT_ID
   # - AMADEUS_CLIENT_SECRET
   # - OPENAI_API_KEY
   # - ANTHROPIC_API_KEY
   # - VERCEL_TOKEN
   ```

## Step 1: Deploy LiveKit Agent

### Using LiveKit Cloud
```bash
cd livekit-agent

# Deploy to LiveKit Cloud
lk cloud agent deploy

# Note the WebSocket URL (e.g., wss://polyglot-rag-assistant-3l6xagej.livekit.cloud)
```

## Step 2: Build and Push API Docker Image

```bash
# Test Docker image locally first
docker build -t polyglot-api:test .
docker run -p 8000:8000 --env-file .env polyglot-api:test

# When ready, push to Docker Hub from your deployment instance
# (Not from local machine for security)
```

## Step 3: Deploy Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform (only first time)
terraform init

# Generate terraform.auto.tfvars from .env
../scripts/generate-tfvars.sh

# Plan deployment
terraform plan

# Deploy everything
terraform apply -auto-approve
```

This creates:
- VPC with public/private subnets
- ECS Fargate cluster for API
- Application Load Balancer
- All necessary networking and security groups

## Step 4: Deploy UI to Vercel

```bash
# Deploy UI with automatic configuration
./scripts/deploy-ui-vercel.sh
```

Your UI will be deployed to:
- Production URL: `https://polyglot-rag-[hash]-axel-sirotas-projects.vercel.app`
- Project Dashboard: `https://vercel.com/axel-sirotas-projects/polyglot-rag-ui`

## Step 5: Verify Deployment

1. **Check API Health**
   ```bash
   # Get API URL from Terraform output
   API_URL=$(cd terraform && terraform output -raw api_url)
   curl $API_URL/health
   ```

2. **Test Token Generation**
   ```bash
   curl -X POST $API_URL/token \
     -H "Content-Type: application/json" \
     -d '{"identity": "test-user", "room_name": "test-room"}'
   ```

3. **Access UI**
   - Open the Vercel URL from Step 4
   - Test voice interaction

4. **Monitor LiveKit Agent**
   ```bash
   lk cloud logs -f
   ```

## Current Deployment Status

As of latest deployment:
- **API**: Running at `http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com`
- **UI**: Deployed to Vercel at `https://polyglot-rag-bcauxftd3-axel-sirotas-projects.vercel.app`
- **LiveKit**: Agent deployed to `wss://polyglot-rag-assistant-3l6xagej.livekit.cloud`
- **ECS**: Cluster `polyglot-rag-prod` with service `polyglot-rag-prod-api`

## Monitoring & Debugging

### Check ECS Logs
```bash
# View API logs
aws logs tail /ecs/polyglot-rag-prod/api --follow

# Check task status
aws ecs describe-services \
  --cluster polyglot-rag-prod \
  --services polyglot-rag-prod-api
```

### LiveKit Debugging
```bash
# View agent logs
lk cloud logs -f

# Test room creation
lk room create test-room
```

### Vercel Deployment
```bash
# Check deployment status
vercel ls

# View logs
vercel logs
```

## Update Deployments

### Update API
```bash
# Build and push new Docker image
# Then update ECS service
aws ecs update-service \
  --cluster polyglot-rag-prod \
  --service polyglot-rag-prod-api \
  --force-new-deployment
```

### Update UI
```bash
# Simply run the deployment script again
./scripts/deploy-ui-vercel.sh
```

### Update LiveKit Agent
```bash
cd livekit-agent
lk cloud agent deploy
```

## Infrastructure Management

### View Current State
```bash
cd terraform
terraform show
```

### Destroy Infrastructure
```bash
cd terraform
terraform destroy -auto-approve
```

## Cost Optimization

- ECS Fargate: ~$0.04/hour per task
- ALB: ~$0.025/hour + data transfer  
- Vercel: Free tier includes 100GB bandwidth
- LiveKit: Check cloud.livekit.io for pricing

To reduce costs:
- Set `desired_count = 1` in Terraform for dev
- Use Vercel's free tier for UI hosting
- Stop ECS tasks when not in use

## Troubleshooting

### API Not Responding
- Check ALB target health in AWS Console
- Verify ECS task is running
- Check security groups allow traffic on port 8000

### UI Connection Issues  
- Verify API_URL and LIVEKIT_URL in deployment script
- Check browser console for CORS errors
- Ensure WebSocket connections are allowed

### LiveKit Connection Issues
- Verify API keys match between services
- Check agent deployment status: `lk cloud agent list`
- Ensure room tokens are being generated correctly

### Terraform State Issues
- Never delete .terraform directory or terraform.tfstate
- Use `terraform refresh` if state is out of sync
- Keep backups of terraform.tfstate

## Quick Reference

```bash
# API URL
http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com

# UI URL  
https://polyglot-rag-bcauxftd3-axel-sirotas-projects.vercel.app

# LiveKit WebSocket
wss://polyglot-rag-assistant-3l6xagej.livekit.cloud

# View all outputs
cd terraform && terraform output
```

## Support

- LiveKit: https://docs.livekit.io
- AWS ECS: https://docs.aws.amazon.com/ecs/
- Vercel: https://vercel.com/docs
- Issues: Create in GitHub repo