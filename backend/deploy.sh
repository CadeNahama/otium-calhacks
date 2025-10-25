#!/bin/bash

echo "🚀 Deploying Otium AI Agent to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

# Check if project is initialized
if [ ! -f ".railway" ]; then
    echo "📁 Initializing Railway project..."
    railway init
fi

# Set environment variables if OPENAI_API_KEY is provided
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "🔑 Setting OpenAI API key..."
    railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
else
    echo "⚠️  OPENAI_API_KEY not set. Please set it manually:"
    echo "   railway variables set OPENAI_API_KEY=your_key_here"
fi

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo "🌐 Check your Railway dashboard for the deployment URL"
