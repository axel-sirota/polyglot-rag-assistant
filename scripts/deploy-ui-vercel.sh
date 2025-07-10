#!/bin/bash
# Deploy UI to Vercel

set -e
# Load environment variables from .env file
if [ -f .env ]; then
  echo "📝 Loading environment variables from .env file..."
  set -a
  source .env
  set +a
else
  echo "⚠️ No .env file found in project root. Using default environment variables."
fi

# Check required environment variables
if [ -z "$API_URL" ]; then
  echo "❌ ERROR: API_URL not set in .env file"
  echo "Add API_URL=your-api-url to .env"
  exit 1
fi

if [ -z "$LIVEKIT_URL" ]; then
  echo "❌ ERROR: LIVEKIT_URL not set in .env file"
  echo "Add LIVEKIT_URL=your-livekit-url to .env"
  exit 1
fi

if [ -z "$VERCEL_TOKEN" ]; then
  echo "❌ ERROR: VERCEL_TOKEN not set in .env file"
  echo "Add VERCEL_TOKEN=your-vercel-token to .env"
  exit 1
fi

# Configuration
PROJECT_NAME="polyglot-rag-ui"

# Install Vercel CLI if not installed
if ! command -v vercel &> /dev/null; then
  echo "📦 Installing Vercel CLI..."
  npm i -g vercel
fi

echo "🔧 Updating configuration..."
# Create temporary directory for deployment
DEPLOY_DIR=$(mktemp -d)
# Copy the web app files
cp web-app/livekit-voice-chat.html $DEPLOY_DIR/index.html
cp web-app/styles.css $DEPLOY_DIR/ 2>/dev/null || true

# Copy API routes for Vercel
mkdir -p $DEPLOY_DIR/api
cp -r web-app/api/* $DEPLOY_DIR/api/ 2>/dev/null || true

# Ensure config.js is included
cp web-app/api/config.js $DEPLOY_DIR/api/ 2>/dev/null || true

# No need to update URLs in files anymore - they use the config API

# Create vercel.json for configuration
cat > $DEPLOY_DIR/vercel.json <<EOF
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"
        },
        {
          "key": "Access-Control-Allow-Methods",
          "value": "GET, POST, PUT, DELETE, OPTIONS"
        },
        {
          "key": "Access-Control-Allow-Headers",
          "value": "X-Requested-With, Content-Type, Authorization"
        }
      ]
    }
  ]
}
EOF

echo "🚀 Deploying to Vercel..."
cd $DEPLOY_DIR

# Deploy to Vercel with explicit project name and environment variables
if [ -f ".vercel/project.json" ]; then
  # Production deployment if project exists
  vercel --prod --token=$VERCEL_TOKEN --yes -e ENVIRONMENT=production
else
  # First time deployment with explicit project name
  vercel --name=$PROJECT_NAME --token=$VERCEL_TOKEN --yes -e ENVIRONMENT=production
  vercel --prod --token=$VERCEL_TOKEN --yes -e ENVIRONMENT=production
fi

# Get the deployment URL from the output
echo ""
echo "✅ UI deployed successfully!"
echo ""
echo "To get your deployment URL:"
echo "1. Check the output above for the production URL"
echo "2. Or visit: https://vercel.com/dashboard"

# Clean up
cd ..
rm -rf $DEPLOY_DIR
echo ""
echo "To use custom domain:"
echo "1. Go to https://vercel.com/dashboard"
echo "2. Select your project"
echo "3. Go to Settings → Domains"
echo "4. Add your custom domain"