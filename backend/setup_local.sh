#!/bin/bash

echo "🚀 Setting up Ping Backend for Local Development (In-Memory)"
echo "=============================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo ""
echo "📦 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Generate encryption key if not exists
if [ ! -f ".env" ]; then
    echo ""
    echo "🔐 Generating encryption key..."
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    echo "📝 Creating .env file..."
    cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Encryption Key
PING_ENCRYPTION_KEY=$ENCRYPTION_KEY

# Server Configuration
PORT=8000
HOST=0.0.0.0
EOF
    
    echo "✅ .env file created with encryption key"
    echo "⚠️  Please edit backend/.env and add your OPENAI_API_KEY"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env and add your OPENAI_API_KEY"
echo "2. Start the backend server:"
echo "   cd backend/llm-os-agent"
echo "   source ../venv/bin/activate"
echo "   uvicorn api_server_memory:app --reload"
echo ""
echo "🌐 Backend will be available at: http://localhost:8000"
echo "📚 API documentation: http://localhost:8000/docs"
echo ""
echo "⚠️  NOTE: This version uses IN-MEMORY storage"
echo "   All data (connections, commands, history) will be LOST on backend restart"
echo "   Perfect for hackathon demos and local development!"

