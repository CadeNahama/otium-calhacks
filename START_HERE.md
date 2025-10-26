# 🚀 Ping Quick Start Guide

**Get your AI DevOps Agent running in 5 minutes!**

---

## ✅ What You'll Need

Before starting, make sure you have:

| Requirement | Check Command | Get It |
|------------|---------------|---------|
| **Python 3.8+** | `python3 --version` | [Download](https://www.python.org/downloads/) |
| **Node.js 18+** | `node --version` | [Download](https://nodejs.org/) |
| **Anthropic API Key** | - | [Get Key](https://console.anthropic.com/) |
| **SSH Server** (optional) | - | For actual command execution demo |

---

## 🏃 5-Step Setup

### **Step 1️⃣: Setup Backend**

```bash
# Navigate to backend directory
cd backend

# Run automated setup (creates venv, installs dependencies)
chmod +x setup_local.sh
./setup_local.sh
```

**Expected Output:**
```
✅ Virtual environment created
✅ Dependencies installed
✅ Environment file created
⚠️  Please add your ANTHROPIC_API_KEY to backend/.env
```

---

### **Step 2️⃣: Add Your API Key**

Open `backend/.env` and add your Anthropic API key:

```bash
# Option A: Edit with nano
nano backend/.env

# Option B: Edit with VS Code
code backend/.env

# Option C: Add directly
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" >> backend/.env
```

**Your `.env` should look like:**
```bash
# Anthropic Claude API Configuration (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here

# Optional: Auto-generated if not set
PING_ENCRYPTION_KEY=auto-generated-on-first-run

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

---

### **Step 3️⃣: Start Backend**

```bash
# Navigate to backend application directory
cd backend/llm-os-agent

# Activate virtual environment
source ../venv/bin/activate

# Start the FastAPI server
uvicorn api_server_enhanced:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/backend/llm-os-agent']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
✅ Loaded environment variables from .env file
✅ Database tables created successfully
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Backend is running!**
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

---

### **Step 4️⃣: Setup Frontend** (Open New Terminal)

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies
npm install

# Start the Next.js development server
npm run dev
```

**Expected Output:**
```
> ping-web-test@0.1.0 dev
> next dev --turbopack

  ▲ Next.js 15.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local

 ✓ Starting...
 ✓ Ready in 1.2s
```

**✅ Frontend is running!**
- Open: `http://localhost:3000`

---

### **Step 5️⃣: Start Using Ping!** 🎉

1. **Open Browser**: Navigate to `http://localhost:3000`

2. **Connect to Server**: 
   - Enter your SSH credentials (hostname, username, password/key)
   - Click "Connect"

3. **Try Your First Command**:
   ```
   "Set up a LEMP stack for hosting a web application"
   ```

4. **Watch the Magic**:
   - Ping analyzes your server (OS, resources, tools)
   - Generates 18 production-ready commands
   - Presents them for your approval
   - Executes each step with real-time feedback
   - Verifies successful installation

**Result**: Full LEMP stack (Linux + Nginx + MySQL + PHP) in ~60 seconds! 🚀

---

## 🎯 What to Try Next

### **Beginner Tasks**
```
"Show me system information"
"Check disk usage"
"List running processes"
"Show memory usage"
```

### **Intermediate Tasks**
```
"Install Docker and docker-compose"
"Install Node.js 18 LTS"
"Setup Nginx as a reverse proxy on port 80"
"Create a system backup script"
```

### **Advanced Tasks**
```
"Set up a LEMP stack for hosting a web application"
"Configure PostgreSQL with optimized settings for 4GB RAM"
"Setup SSL with Let's Encrypt for my domain"
"Install and configure Redis for caching"
```

---

## 🐛 Troubleshooting

### **Backend Won't Start**

**Problem**: `ModuleNotFoundError` or import errors
```bash
# Solution: Reinstall dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Problem**: `ANTHROPIC_API_KEY is required`
```bash
# Solution: Check your .env file
cat backend/.env | grep ANTHROPIC_API_KEY

# Should show: ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
# If empty, add your key:
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key" >> backend/.env
```

**Problem**: Port 8000 already in use
```bash
# Solution: Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn api_server_enhanced:app --reload --port 8001
```

---

### **Frontend Won't Start**

**Problem**: Port 3000 already in use
```bash
# Solution: Kill existing process
lsof -ti:3000 | xargs kill -9

# Or Next.js will auto-assign next available port
```

**Problem**: `npm install` fails
```bash
# Solution: Clear cache and retry
rm -rf node_modules package-lock.json
npm install
```

**Problem**: Can't connect to backend
```bash
# Solution: Check backend is running
curl http://localhost:8000/api/health

# Should return: {"status":"healthy","version":"1.0.0"}
```

---

### **SSH Connection Issues**

**Problem**: "Connection refused"
```
✅ Check: SSH server is running on target
✅ Check: Port 22 is open (or your custom port)
✅ Check: Firewall allows SSH connections
```

**Problem**: "Authentication failed"
```
✅ Check: Username is correct
✅ Check: Password/key is correct
✅ Try: Using SSH key instead of password
```

**Problem**: "Permission denied"
```
✅ Check: User has sudo privileges
✅ Try: Running commands as root user
✅ Check: SSH key permissions (chmod 600 ~/.ssh/id_rsa)
```

---

## 🎉 Success!

You now have Ping running! 

