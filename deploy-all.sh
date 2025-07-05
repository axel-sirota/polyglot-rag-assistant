#!/bin/bash
# Complete deployment script for Polyglot RAG Assistant
# Deploys LiveKit agent, API to Docker Hub/ECS, and UI to S3/CloudFront

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check for required commands
    for cmd in docker terraform aws jq; do
        if ! command -v $cmd &> /dev/null; then
            print_error "$cmd is not installed"
            exit 1
        fi
    done
    
    # Check environment variables
    if [ -z "$DOCKER_USERNAME" ]; then
        print_error "DOCKER_USERNAME not set"
        exit 1
    fi
    
    if [ -z "$DOCKER_PASSWORD" ]; then
        print_error "DOCKER_PASSWORD not set"
        exit 1
    fi
    
    print_status "Prerequisites checked ✓"
}

# Deploy API to Docker Hub
deploy_api() {
    print_status "Building and pushing API to Docker Hub..."
    
    if [ -f "scripts/deploy-api-docker.sh" ]; then
        chmod +x scripts/deploy-api-docker.sh
        ./scripts/deploy-api-docker.sh v1.0.0
    else
        print_error "API deployment script not found"
        exit 1
    fi
    
    print_status "API deployed to Docker Hub ✓"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    print_status "Deploying AWS infrastructure with Terraform..."
    
    # Generate terraform.auto.tfvars from .env
    print_status "Generating Terraform variables from .env..."
    ./scripts/generate-tfvars.sh
    
    cd terraform
    
    # Initialize Terraform
    terraform init
    
    # Apply Terraform (no need to pass vars - auto.tfvars loads automatically)
    terraform apply -auto-approve
    
    # Get outputs
    export API_URL=$(terraform output -raw api_url)
    
    cd ..
    
    print_status "Infrastructure deployed ✓"
    print_status "API URL: $API_URL"
}

# Deploy UI to Vercel
deploy_ui() {
    print_status "Deploying UI to Vercel..."
    
    # Get LiveKit URL from user or use default
    if [ -z "$LIVEKIT_URL" ]; then
        print_warning "LIVEKIT_URL not set. Using placeholder."
        export LIVEKIT_URL="wss://polyglot-rag-assistant.livekit.cloud"
    fi
    
    # Load Vercel token from .env
    source .env
    export VERCEL_TOKEN
    
    if [ -f "scripts/deploy-ui-vercel.sh" ]; then
        chmod +x scripts/deploy-ui-vercel.sh
        ./scripts/deploy-ui-vercel.sh
    else
        print_error "UI deployment script not found"
        exit 1
    fi
    
    print_status "UI deployed ✓"
}

# Main deployment flow
main() {
    echo "🚀 Polyglot RAG Assistant - Complete Deployment"
    echo "=============================================="
    
    check_prerequisites
    
    # Deploy API to Docker Hub
    deploy_api
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Deploy UI
    deploy_ui
    
    echo ""
    echo "✅ Deployment Complete!"
    echo "======================"
    echo "🌐 UI: Check Vercel dashboard for URL"
    echo "🔧 API: $API_URL"
    echo "📱 LiveKit: Deploy agent via dashboard at https://cloud.livekit.io"
    echo ""
    echo "Next steps:"
    echo "1. Deploy LiveKit agent using the dashboard"
    echo "2. Update LIVEKIT_URL in your environment"
    echo "3. Redeploy UI with: ./scripts/deploy-ui-vercel.sh"
    echo ""
    echo "To monitor:"
    echo "- ECS logs: aws logs tail /ecs/polyglot-rag-prod/api --follow"
    echo "- LiveKit logs: lk cloud logs -f"
}

# Run main function
main