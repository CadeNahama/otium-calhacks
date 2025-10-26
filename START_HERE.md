# 🚀 Quick Start Guide

## What You Need

1. **OpenAI API Key** - Get from https://platform.openai.com/api-keys
2. **Python 3.8+** - Check with `python3 --version`
3. **Node.js 18+** - Check with `node --version`
4. **(Optional) SSH Server** - For actual command execution demo

## 🏃 Run the Platform (5 Steps)

### Step 1: Setup Backend
```bash
cd backend
./setup_local.sh
```

### Step 2: Add Your OpenAI API Key
```bash
# Edit backend/.env
nano backend/.env
# or
code backend/.env

# Replace this line:
OPENAI_API_KEY=your_openai_api_key_here
# With your actual key:
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

### Step 3: Start Backend
```bash
cd backend/llm-os-agent
source ../venv/bin/activate
uvicorn api_server_memory:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
[MEMORY] Starting in-memory backend
[MEMORY] All data will be lost on restart
```

### **Step 4: Setup Frontend** (NEW Terminal 2)

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies
npm install

# Start the frontend server
npm run dev
```

You should see:
```