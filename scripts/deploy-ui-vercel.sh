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

# Configuration
API_URL=${API_URL:-"http://polyglot-rag-prod-alb-1838390148.us-east-1.elb.amazonaws.com"}
LIVEKIT_URL=${LIVEKIT_URL:-"wss://polyglot-rag-assistant-3l6xagej.livekit.cloud"}
VERCEL_TOKEN=${VERCEL_TOKEN:-""}
PROJECT_NAME="polyglot-rag-ui"

# Check for Vercel token
if [ -z "$VERCEL_TOKEN" ]; then
  echo "❌ VERCEL_TOKEN not set. Add to .env or export it."
  exit 1
fi

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
cp web-app/livekit-client.html $DEPLOY_DIR/
cp web-app/styles.css $DEPLOY_DIR/ 2>/dev/null || true

# Copy API routes for Vercel
mkdir -p $DEPLOY_DIR/api
cp -r web-app/api/* $DEPLOY_DIR/api/ 2>/dev/null || true

# Update URLs in the files
# The HTML files have the full URL that needs to be replaced
sed -i.bak "s|wss://polyglot-rag-assistant-3l6xagej.livekit.cloud|${LIVEKIT_URL}|g" $DEPLOY_DIR/*.html
sed -i.bak "s|http://localhost:8000|${API_URL}|g" $DEPLOY_DIR/*.js 2>/dev/null || true

# Clean up backup files
find $DEPLOY_DIR -name "*.bak" -delete

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

# Deploy to Vercel with explicit project name
if [ -f ".vercel/project.json" ]; then
  # Production deployment if project exists
  vercel --prod --token=$VERCEL_TOKEN --yes
else
  # First time deployment with explicit project name
  vercel --name=$PROJECT_NAME --token=$VERCEL_TOKEN --yes
  vercel --prod --token=$VERCEL_TOKEN --yes
fi

# Get the deployment URL from the output
echo ""
echo "✅ UI deployed successfully!"
echo ""
echo "To get your deployment URL:"
echo "1. Check the output above for the production URL"
echo "2. Or visit: https://vercel.com/axel-sirotas-projects/polyglot-rag-ui"

# Clean up
cd ..
rm -rf $DEPLOY_DIR
echo ""
echo "To use custom domain:"
echo "1. Go to https://vercel.com/dashboard"
echo "2. Select your project"
echo "3. Go to Settings → Domains"
echo "4. Add your custom domain"