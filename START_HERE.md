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
# Anthropic Claude API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-IeM54B0vQ5CkahsvSMvukqAO...

# Optional: Auto-generated if not set
PING_ENCRYPTION_KEY=2SWxBjiI2Ozw4q9MBy8n_u1jOLXN3s87z4UYwEcraGQ=

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

## 🎓 Understanding Ping's Architecture

### **How It Works**

1. **User Input** (Natural Language)
   ```
   "Set up a LEMP stack"
   ```

2. **System Detection** (Via SSH)
   - Detects OS: Ubuntu 22.04
   - Checks RAM: 957MB available
   - Finds tools: apt, systemctl, ufw, etc.
   - Identifies architecture: x86_64

3. **AI Analysis** (Claude Sonnet 4.5)
   - Receives system context
   - Analyzes user request
   - Generates OS-specific commands
   - Adds safety checks
   - Calculates risk level

4. **Command Presentation**
   - Shows all commands to user
   - Explains each step
   - Displays expected outcomes
   - Allows step-by-step approval

5. **Execution** (Via SSH)
   - Runs each approved command
   - Streams real-time output
   - Tracks success/failure
   - Logs execution time

6. **Verification**
   - Validates installation
   - Checks services running
   - Tests configurations
   - Reports final status

---

## 📚 Key Concepts

### **Context-Aware Commands**

Ping generates different commands based on your system:

| System | Package Manager | Service Manager | Command |
|--------|----------------|-----------------|---------|
| Ubuntu 22.04 | `apt` | `systemctl` | `apt install nginx` |
| CentOS 8 | `dnf` | `systemctl` | `dnf install nginx` |
| CentOS 7 | `yum` | `service` | `yum install nginx` |

### **Risk Levels**

| Risk | Description | Examples |
|------|-------------|----------|
| 🟢 **Low** | Read-only, non-destructive | `ps aux`, `df -h`, `cat /etc/os-release` |
| 🟡 **Medium** | Installs software, modifies config | `apt install nginx`, edit config files |
| 🔴 **High** | Destructive, irreversible | `rm -rf`, database drops, user deletion |

### **Idempotent Operations**

Ping generates commands that are safe to run multiple times:
- Installing already-installed packages: Skips or updates
- Creating existing directories: Checks first with `mkdir -p`
- Starting running services: Uses `systemctl restart` instead of `start`

---

## 🔐 Security Best Practices

1. **Never run Ping as root** unless absolutely necessary
2. **Review commands** before approving (especially high-risk)
3. **Use SSH keys** instead of passwords when possible
4. **Rotate credentials** regularly
5. **Keep audit logs** for compliance
6. **Test on dev servers** before production

---

## 💡 Pro Tips

1. **Be Specific**: "Install nginx 1.18" is better than "install nginx"
2. **Mention OS**: "On Ubuntu 22.04, install..." (though Ping auto-detects)
3. **Include Context**: "For a WordPress site with high traffic..."
4. **Ask Questions**: "What's the difference between nginx and apache for my use case?"
5. **Learn as You Go**: Ping shows best practices - study the generated commands!

---

## 📊 Performance Tips

### **For Faster Response Times**
- Use specific requests ("Install nginx" vs "Setup web server")
- Stay connected (SSH connection stays alive)
- Run backend with more workers: `uvicorn app:app --workers 4`

### **For Complex Tasks**
- Break into smaller steps
- Approve in batches
- Monitor system resources during execution

---

## 🎉 Success!

You now have Ping running! 

**Next Steps:**
1. Read the [full README](README.md) for advanced features
2. Check out [prompt optimization](PROMPT_OPTIMIZATION_CLAUDE.md) to understand the AI
3. Explore the [API docs](http://localhost:8000/docs) for integration
4. Join our community (coming soon!) to share tips

---

<div align="center">

**Need Help?**

[📖 Full Documentation](README.md) • [🐛 Report Issue](https://github.com/CadeNahama/ping-calhacks/issues) • [⭐ Star on GitHub](https://github.com/CadeNahama/ping-calhacks)

**Happy Automating! 🚀**

</div>
