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

### Step 4: Start Frontend (New Terminal)
```bash
cd frontend
npm install
npm run dev
```

You should see:
```
▲ Next.js 15.4.6
- Local:        http://localhost:3000
```

### Step 5: Open Browser
```
http://localhost:3000
```

## ✅ What Should Work

### Without SSH Server
- ✅ Frontend loads
- ✅ Auto-login as `demo_user`
- ✅ UI is functional
- ❌ Can't connect to SSH (need server)
- ❌ Can't execute commands (need SSH)

### With SSH Server
- ✅ Everything above
- ✅ Connect to SSH server
- ✅ Submit tasks
- ✅ AI generates commands
- ✅ Approve/reject steps
- ✅ Execute commands
- ✅ View command history

## 🧪 Test Without SSH Server

You can test the API directly:

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Should return:
{
  "status": "healthy",
  "storage_type": "in-memory (session-based)",
  "stats": {
    "users": 0,
    "connections": 0,
    "commands": 0
  }
}
```

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

### Frontend won't start
```bash
# Check if port 3000 is in use
lsof -i :3000

# Clear cache and retry
cd frontend
rm -rf .next node_modules
npm install
npm run dev
```

### Missing OpenAI Key
```
Error: OPENAI_API_KEY not set
```
Solution: Add your key to `backend/.env`

### Module not found errors
```bash
# Reinstall backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Reinstall frontend dependencies
cd frontend
rm -rf node_modules
npm install
```

## 🎯 Quick Demo Flow

1. **Start both servers** (backend + frontend)
2. **Open http://localhost:3000**
3. **Connect to SSH server** (if you have one)
4. **Submit a task**: "list all files in the home directory"
5. **Review AI-generated commands**
6. **Approve each step**
7. **Watch execution results**
8. **View command history**

## 📝 Notes

- **All data is in-memory** - Restart backend to reset everything
- **Auto-login** - No need to sign up/login
- **Local only** - No external services except OpenAI
- **Perfect for demos** - Quick setup, easy reset

## 🆘 Still Having Issues?

Check:
1. Python version: `python3 --version` (need 3.8+)
2. Node version: `node --version` (need 18+)
3. Backend logs in terminal
4. Frontend logs in terminal
5. Browser console (F12)

## 🎉 Success Indicators

### Backend Running
```
INFO:     Application startup complete.
[MEMORY] Starting in-memory backend
```

### Frontend Running
```
✓ Ready in 2.5s
○ Compiling / ...
✓ Compiled / in 1.2s
```

### Browser Working
- Page loads
- No console errors
- Can see SSH connection form

You're ready to demo! 🚀


