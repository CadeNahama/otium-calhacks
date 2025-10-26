# Ping - AI-Powered System Administration

Full-stack application for AI-powered Linux system administration with SSH support. Built for hackathons with **session-based in-memory storage** - no database required!

## 🏗️ Project Structure

This is a monorepo containing both frontend and backend:

```
CALHACKS-OTIUM/
├── backend/          # Python FastAPI backend (in-memory storage)
│   └── llm-os-agent/ # Main application code
└── frontend/         # Next.js frontend
```

## 🚀 Quick Start (Automated)

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI API key
- **No Docker needed!** (in-memory storage)

### One-Command Setup

```bash
# 1. Setup backend
cd backend
chmod +x setup_local.sh
./setup_local.sh

# 2. Add your OpenAI API key to backend/.env
# Edit the file and replace: OPENAI_API_KEY=your_openai_api_key_here

# 3. Start backend
cd llm-os-agent
source ../venv/bin/activate
uvicorn api_server_memory:app --reload --host 0.0.0.0 --port 8000

# 4. In a new terminal, setup frontend
cd frontend
npm install
npm run dev
```

## 🔧 Manual Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env

# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Edit .env and add:
# - Your OpenAI API key
# - The generated encryption key

# Start backend server
cd llm-os-agent
uvicorn api_server_memory:app --reload --host 0.0.0.0 --port 8000
```

Backend runs on: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on: `http://localhost:3000`

## 🔑 Environment Variables

### Backend (`backend/.env`)
```bash
OPENAI_API_KEY=your_openai_api_key_here
PING_ENCRYPTION_KEY=your_generated_encryption_key
PORT=8000
HOST=0.0.0.0
```

### Frontend
No environment variables needed for local development. The frontend automatically connects to `http://localhost:8000`.

## 📚 Tech Stack

### Backend
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **In-Memory Storage** - Session-based (no database!)
- **OpenAI** - AI command generation
- **Paramiko** - SSH connections
- **Cryptography** - Encrypted credentials

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Radix UI** - Component library
- **Local Auth** - Simple demo authentication

## 🎯 Features

- ✅ AI-powered command generation (OpenAI)
- ✅ SSH-based system administration
- ✅ Step-by-step command approval
- ✅ Real-time command execution
- ✅ **In-memory session storage** (no database setup!)
- ✅ Encrypted credential storage
- ✅ Audit logging
- ✅ Auto-cleanup on inactivity
- ✅ Local-first development (no external services)

## 🧪 Testing

### Test Backend
```bash
cd backend/llm-os-agent
python3 -m pytest tests/ -v
```

### Test Frontend
```bash
cd frontend
npm run lint
```

## 🛠️ Troubleshooting

### Backend Issues
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# View backend logs (in terminal where uvicorn is running)

# Restart backend to clear all session data
# Just stop (Ctrl+C) and restart uvicorn
```

### Frontend Issues
```bash
# Clear Next.js cache
cd frontend
rm -rf .next
npm run dev
```

### Session Data Issues
```bash
# All data is in-memory - just restart the backend to reset everything
# No database to clean up or reset!
```

## 📝 Development Notes

- **Storage**: In-memory (session-based) - all data lost on restart
- **Authentication**: Auto-login with `demo_user` for hackathon demos
- **Backend**: FastAPI on port 8000
- **Frontend**: Next.js on port 3000
- **No Database**: No Docker, PostgreSQL, or database setup needed!
- **No External Services**: Everything runs locally

## 🎓 For Hackathon Judges

This is a **super simple** local setup requiring:
1. Python 3.8+ (for backend)
2. Node.js 18+ (for frontend)
3. OpenAI API key (for AI features)
4. SSH access to a test server (for demo)

**No Docker, Database, Railway, Vercel, or WorkOS needed!**

Perfect for quick demos - just restart the backend to reset everything!

## 📝 License

MIT
