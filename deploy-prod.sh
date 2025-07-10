#!/bin/bash
# Deploy all components to production
# This script deploys API, Agent, UI, and applies Terraform

set -e

echo "🚀 Polyglot RAG Assistant - Production Deployment"
echo "================================================="
echo ""

# Check if we're in the project root
if [ ! -f "README.md" ] || [ ! -d "scripts" ]; then
    echo "❌ ERROR: This script must be run from the project root directory"
    exit 1
fi

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env file..."
    set -a
    source .env
    set +a
else
    echo "❌ ERROR: .env file not found in project root"
    echo "Please create .env file with required variables:"
    echo ""
    echo "# Docker Hub"
    echo "DOCKER_USERNAME=your-docker-hub-username"
    echo ""
    echo "# API Keys"
    echo "OPENAI_API_KEY=sk-..."
    echo "ANTHROPIC_API_KEY=sk-ant-..."
    echo "DEEPGRAM_API_KEY=..."
    echo "CARTESIA_API_KEY=..."
    echo "LIVEKIT_API_KEY=..."
    echo "LIVEKIT_API_SECRET=..."
    echo ""
    echo "# URLs"
    echo "API_URL=http://your-api-alb.amazonaws.com"
    echo "LIVEKIT_URL=wss://your-app.livekit.cloud"
    echo ""
    echo "# Deployment"
    echo "VERCEL_TOKEN=..."
    echo "AWS_REGION=us-east-1"
    echo ""
    exit 1
fi

# Validate all required environment variables
echo "🔍 Validating environment variables..."

required_vars=(
    "DOCKER_USERNAME"
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "DEEPGRAM_API_KEY"
    "CARTESIA_API_KEY"
    "LIVEKIT_API_KEY"
    "LIVEKIT_API_SECRET"
    "API_URL"
    "LIVEKIT_URL"
    "VERCEL_TOKEN"
    "AWS_REGION"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=($var)
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ ERROR: Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please add these to your .env file"
    exit 1
fi

echo "✅ All required environment variables found"
echo ""

# Function to handle errors
handle_error() {
    echo ""
    echo "❌ ERROR: Deployment failed at step: $1"
    echo "Please check the error messages above and try again"
    exit 1
}

# Deploy API Docker image
echo "1️⃣  Deploying API Docker image..."
echo "================================"
./scripts/deploy-api-docker.sh || handle_error "API Docker deployment"
echo ""

# Deploy Agent Docker image  
echo "2️⃣  Deploying Agent Docker image..."
echo "==================================="
./scripts/deploy-agent-docker.sh || handle_error "Agent Docker deployment"
echo ""

# Deploy UI to Vercel
echo "3️⃣  Deploying UI to Vercel..."
echo "=============================="
./scripts/deploy-ui-vercel.sh || handle_error "UI Vercel deployment"
echo ""

# Apply Terraform
echo "4️⃣  Applying Terraform changes..."
echo "================================="

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ ERROR: Terraform is not installed"
    echo "Please install Terraform: https://www.terraform.io/downloads"
    exit 1
fi

# Generate terraform.tfvars if it doesn't exist
if [ ! -f "terraform/terraform.tfvars" ]; then
    echo "📝 Generating terraform.tfvars..."
    ./scripts/generate-tfvars.sh || handle_error "Terraform tfvars generation"
fi

# Apply Terraform
cd terraform
echo "🔧 Initializing Terraform..."
terraform init || handle_error "Terraform init"

echo "📋 Planning Terraform changes..."
terraform plan || handle_error "Terraform plan"

echo ""
echo "⚠️  About to apply Terraform changes to AWS infrastructure"
echo "This will modify your production environment!"
echo ""
read -p "Do you want to continue? (yes/no): " -r
echo ""

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "🚀 Applying Terraform..."
    terraform apply -auto-approve || handle_error "Terraform apply"
else
    echo "⏭️  Skipping Terraform apply"
fi

cd ..

# Summary
echo ""
echo "✅ Production deployment complete!"
echo "=================================="
echo ""
echo "📊 Deployment Summary:"
echo "  - API Docker image: ${DOCKER_USERNAME}/polyglot-api:latest"
echo "  - Agent Docker image: ${DOCKER_USERNAME}/polyglot-agent:latest"
echo "  - UI URL: Check Vercel output above for production URL"
echo "  - API URL: ${API_URL}"
echo "  - LiveKit URL: ${LIVEKIT_URL}"
echo ""
echo "🔍 Next steps:"
echo "  1. Verify the UI is accessible at the Vercel URL"
echo "  2. Test the voice assistant connection"
echo "  3. Monitor ECS task logs in AWS Console"
echo "  4. Check LiveKit Cloud dashboard for agent connections"
echo ""
echo "📚 Troubleshooting:"
echo "  - API logs: aws logs tail /ecs/polyglot-rag-prod/api --follow"
echo "  - Agent logs: aws logs tail /ecs/polyglot-rag-prod/livekit-agent --follow"
echo "  - LiveKit logs: https://cloud.livekit.io/projects"
echo ""