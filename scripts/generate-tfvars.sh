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
dockerhub_username = "axelsirota"

# API Keys from .env file
openai_api_key        = "${OPENAI_API_KEY}"
amadeus_client_id     = "${AMADEUS_CLIENT_ID}"
amadeus_client_secret = "${AMADEUS_CLIENT_SECRET}"
livekit_api_key       = "${LIVEKIT_API_KEY}"
livekit_api_secret    = "${LIVEKIT_API_SECRET}"
EOF

echo "✅ Generated terraform/terraform.auto.tfvars from .env"
echo "📝 This file is gitignored and will be loaded automatically by Terraform"