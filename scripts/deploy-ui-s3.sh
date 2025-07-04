#!/bin/bash
# Deploy UI to S3/CloudFront

set -e

# Configuration
BUCKET_NAME=${S3_BUCKET:-"polyglot-rag-prod-ui"}
CLOUDFRONT_ID=${CLOUDFRONT_DISTRIBUTION_ID:-""}
API_URL=${API_URL:-"https://api.polyglot-rag.com"}
LIVEKIT_URL=${LIVEKIT_URL:-"wss://polyglot-rag-assistant-3l6xagej.livekit.cloud"}

echo "🔧 Updating configuration..."
# Update API URL in HTML files
find web-app -name "*.html" -exec sed -i.bak "s|http://localhost:8000|${API_URL}|g" {} \;
find web-app -name "*.js" -exec sed -i.bak "s|http://localhost:8000|${API_URL}|g" {} \;
find web-app -name "*.js" -exec sed -i.bak "s|wss://polyglot-rag.livekit.cloud|${LIVEKIT_URL}|g" {} \;

# Clean up backup files
find web-app -name "*.bak" -delete

echo "📦 Building UI..."
# If you have a build process, run it here
# For now, we'll just copy the files

echo "🚀 Deploying to S3..."
aws s3 sync web-app/ s3://${BUCKET_NAME}/ \
  --exclude "*.bak" \
  --exclude ".DS_Store" \
  --exclude "node_modules/*" \
  --delete

echo "🔄 Setting cache headers..."
# HTML files - no cache
aws s3 cp s3://${BUCKET_NAME}/ s3://${BUCKET_NAME}/ \
  --exclude "*" \
  --include "*.html" \
  --recursive \
  --metadata-directive REPLACE \
  --cache-control "no-cache, no-store, must-revalidate" \
  --content-type "text/html"

# JS/CSS files - 1 year cache
aws s3 cp s3://${BUCKET_NAME}/ s3://${BUCKET_NAME}/ \
  --exclude "*" \
  --include "*.js" \
  --include "*.css" \
  --recursive \
  --metadata-directive REPLACE \
  --cache-control "public, max-age=31536000"

if [ -n "${CLOUDFRONT_ID}" ]; then
  echo "🌐 Invalidating CloudFront cache..."
  aws cloudfront create-invalidation \
    --distribution-id ${CLOUDFRONT_ID} \
    --paths "/*"
fi

echo "✅ UI deployed successfully!"