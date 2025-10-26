#!/bin/bash

echo "🚀 Setting up Ping Frontend for Local Development"
echo "=================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

echo "✅ npm found: $(npm --version)"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure the backend is running on http://localhost:8000"
echo "2. Start the frontend development server:"
echo "   npm run dev"
echo ""
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔐 Authentication: Auto-login as 'demo_user'"


