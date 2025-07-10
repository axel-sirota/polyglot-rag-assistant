#!/bin/bash
# Generate terraform.auto.tfvars from .env file

set -e

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Source .env file
source .env

# Generate terraform.auto.tfvars
cat > terraform/terraform.auto.tfvars <<EOF
# Auto-generated from .env - DO NOT COMMIT
# This file is automatically loaded by Terraform
# Generated on: $(date)

# Docker Hub
dockerhub_username = "${DOCKER_USERNAME}"

# API Keys from .env file
openai_api_key        = "${OPENAI_API_KEY}"
anthropic_api_key     = "${ANTHROPIC_API_KEY}"
deepgram_api_key      = "${DEEPGRAM_API_KEY}"
cartesia_api_key      = "${CARTESIA_API_KEY}"
amadeus_client_id     = "${AMADEUS_CLIENT_ID}"
amadeus_client_secret = "${AMADEUS_CLIENT_SECRET}"
amadeus_base_url      = "${AMADEUS_BASE_URL}"
serper_api_key        = "${SERPER_API_KEY}"
serpapi_api_key       = "${SERPAPI_API_KEY}"
livekit_url           = "${LIVEKIT_URL}"
livekit_api_key       = "${LIVEKIT_API_KEY}"
livekit_api_secret    = "${LIVEKIT_API_SECRET}"
EOF

echo "✅ Generated terraform/terraform.auto.tfvars from .env"
echo "📝 This file is gitignored and will be loaded automatically by Terraform"