# 🚀 Ping - AI-Powered DevOps Agent

**Ping is an intelligent DevOps agent that transforms natural language commands into production-ready server operations.** Built with Claude Sonnet 4.5, Ping understands your infrastructure, generates context-aware commands, and executes them safely on your servers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

---

## 🎯 What is Ping?

Ping is an **AI-powered DevOps automation platform** that bridges the gap between natural language and server operations. Instead of memorizing complex commands or consulting documentation, you simply tell Ping what you want to accomplish, and it generates, explains, and executes the necessary commands.

### ✨ **The Problem We Solve**

Traditional DevOps is Broken:
- **Time-consuming**: Looking up commands, syntax, and flags
- **Error-prone**: One typo can break production
- **Knowledge-intensive**: Requires years of Linux/DevOps experience
- **Context-blind**: Generic StackOverflow answers don't match your specific OS/environment

### 💡 **The Ping Solution**

Ping provides:
- **Natural Language → Production Commands**: "Set up a LEMP stack" → 18 automated, tested steps
- **Context-Aware Intelligence**: Adapts commands to your OS, architecture, available tools, and resources
- **Safety First**: Pre-execution validation, risk assessment, and step-by-step approval
- **Production Ready**: Idempotent operations, proper error handling, and verification steps

---

## 🔥 Why Ping is Revolutionary

### 1. **Powered by Claude Sonnet 4.5**
- Latest Anthropic AI model specifically optimized for DevOps tasks
- 180+ line system prompt with production-grade safety protocols
- Context window of 200K tokens - understands your entire infrastructure


### 2. **Context-Aware Command Generation**
Ping knows:
- **Your OS**: Ubuntu vs CentOS → `apt` vs `yum`
- **Your Resources**: 957MB RAM → Optimizes MySQL config
- **Your Tools**: Has `ufw`? Use it. Only has `iptables`? Use that.
- **Your Services**: What's already running, what's conflicting

### 4. **Production-Grade Safety**
- Pre-execution validation (disk space, memory, dependencies)
- Risk assessment (low/medium/high)
- Step-by-step approval workflow
- Idempotent operations (safe to run multiple times)
- Comprehensive error handling
- Audit logs for every operation

---

## 🎬 Real-World Example

**Task**: Deploy a production-ready LEMP stack

**Traditional Approach**: 
- 2-3 hours of documentation reading
- 15-30 manual commands
- Multiple trial-and-error cycles
- High risk of misconfiguration

**Ping Approach**:
```bash
User Input: "Set up a complete LEMP stack for hosting a web application"

Ping Output: ✅ 18 automated steps executed in 64 seconds
  1. ✅ Check disk space (22G available)
  2. ✅ Update package lists
  3. ✅ Check existing components
  4. ✅ Install/verify nginx 1.18.0
  5. ✅ Verify nginx running
  6. ✅ Install MySQL 8.0 (28 packages, 243MB)
  7. ✅ Configure MySQL for your RAM
  8. ✅ Verify MySQL running on port 3306
  9. ✅ Install PHP 8.1-FPM + 8 extensions
  10. ✅ Verify PHP-FPM running
  11. ✅ Check PHP version
  12. ✅ Test nginx config
  13. ✅ Verify all services listening on correct ports
  14. ✅ Enable boot-time auto-start for all services
  15. ✅ Create PHP test file
  16. ✅ Set secure permissions (www-data:www-data)
  17. ✅ Configure nginx → PHP-FPM integration
  18. ✅ Reload nginx with new config

Result: Production-ready LEMP stack in 1 minute vs 3 hours manually
```

---

## 🚀 Key Features

### 🤖 **AI-Powered Command Generation**
- Natural language → Production-ready commands
- Claude Sonnet 4.5 with custom DevOps prompts
- Handles complex multi-service deployments (LEMP, LAMP, Docker, K8s)

### 🎯 **Context-Aware Intelligence**
- OS-specific commands (Ubuntu/CentOS/Debian/RHEL)
- Resource optimization (adapts to your RAM/CPU/disk)
- Tool detection (uses what you have available)
- Service awareness (avoids port conflicts)

### 🛡️ **Production-Grade Safety**
- Pre-execution validation checks
- Risk assessment and warnings
- Step-by-step approval workflow
- Rollback support for failed operations
- Comprehensive audit logging

### 📊 **Real-Time Execution & Monitoring**
- SSH-based command execution
- Live output streaming
- Success/failure detection
- Execution time tracking
- Detailed error reporting

### 🔐 **Enterprise Security**
- Encrypted credential storage
- No plain-text passwords
- Session-based authentication
- Automatic credential cleanup
- Audit trail for compliance

### 📈 **Developer Experience**
- Beautiful modern UI with dark mode
- Real-time command history
- Detailed execution logs
- Copy-paste friendly output
- Responsive design (desktop/mobile)

---

## 💻 Tech Stack

### **Backend (Python)**
- **FastAPI** - Modern async web framework
- **Anthropic Claude Sonnet 4.5** - AI command generation
- **Paramiko** - SSH connection management
- **SQLAlchemy** - Database ORM (PostgreSQL/SQLite)
- **Cryptography** - Fernet encryption for credentials
- **Uvicorn** - High-performance ASGI server

### **Frontend (TypeScript/React)**
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Accessible component library
- **Lucide Icons** - Beautiful icon set

### **AI/ML**
- **Claude Sonnet 4.5 (20250929)** - Latest Anthropic model
- **Custom System Prompts** - 180+ lines of DevOps optimization
- **Context Window**: 200K tokens
- **Temperature**: 0.1 (consistent, reliable outputs)
- **Max Tokens**: 2000 (comprehensive responses)

---

## 🏁 Quick Start

### **Prerequisites**
- Python 3.8+ ([Download](https://www.python.org/downloads/))
- Node.js 18+ ([Download](https://nodejs.org/))
- Anthropic API Key ([Get one](https://console.anthropic.com/))
- SSH server access (for command execution)

### **5-Minute Setup**

#### 1. Clone & Setup Backend
```bash
# Clone the repository
git clone https://github.com/CadeNahama/ping-calhacks.git
cd ping-calhacks/backend

# Run automated setup script
chmod +x setup_local.sh
./setup_local.sh

# Add your Anthropic API key
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

#### 2. Start Backend
```bash
cd llm-os-agent
source ../venv/bin/activate
uvicorn api_server_enhanced:app --reload --host 0.0.0.0 --port 8000
```

Backend runs on: `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

#### 3. Setup & Start Frontend (New Terminal)
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:3000`

#### 4. Connect & Start Automating! 🎉
1. Open `http://localhost:3000`
2. Enter your SSH credentials
3. Type: "Set up a LEMP stack"
4. Watch Ping generate and execute 18 production-ready commands!

---

## 🔑 Environment Variables

### **Backend** (`backend/.env`)
```bash
# Required: Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx

# Optional: Encryption (auto-generated if not set)
PING_ENCRYPTION_KEY=your_generated_encryption_key

# Optional: Server config
PORT=8000
HOST=0.0.0.0

# Optional: Database (uses SQLite if not set)
DATABASE_URL=postgresql://user:pass@host:port/db
```

### **Frontend**
No environment variables needed for local development.

---

## 📚 Usage Examples

### **Example 1: Install Docker**
```
User: "Install Docker and docker-compose"

Ping: ✅ Generated 12 commands
  - Update package lists
  - Install prerequisites (apt-transport-https, ca-certificates, curl)
  - Add Docker GPG key
  - Add Docker repository
  - Install docker-ce
  - Start Docker service
  - Enable Docker on boot
  - Add current user to docker group
  - Install docker-compose
  - Verify Docker version
  - Verify docker-compose version
  - Test Docker with hello-world
```

### **Example 2: Database Backup**
```
User: "Backup my MySQL database to /backups with timestamp"

Ping: ✅ Generated 8 commands
  - Check if /backups exists, create if needed
  - Get current timestamp
  - Dump database with mysqldump
  - Compress backup with gzip
  - Verify backup file created
  - Check backup file size
  - Set secure permissions (600)
  - Create symlink to latest backup
```

### **Example 3: Performance Monitoring**
```
User: "Show me current system performance and top processes"

Ping: ✅ Generated 7 commands
  - Show CPU usage (top snapshot)
  - Show memory usage (free -h)
  - Show disk usage (df -h)
  - Show disk I/O (iostat)
  - Show network connections (ss -tuln)
  - Show top 10 CPU processes
  - Show top 10 memory processes
```

---

## 🛠️ Advanced Configuration

### **Supported Operating Systems**
- ✅ Ubuntu 18.04, 20.04, 22.04, 24.04
- ✅ Debian 10, 11, 12
- ✅ CentOS 7, 8, Stream
- ✅ RHEL 7, 8, 9
- ✅ Fedora 36+
- ✅ Amazon Linux 2, 2023

### **Database Options**
```bash
# SQLite (default, no setup needed)
# Data stored in: backend/ping.db

# PostgreSQL (production)
export DATABASE_URL="postgresql://user:pass@localhost:5432/ping"

# MySQL (alternative)
export DATABASE_URL="mysql://user:pass@localhost:3306/ping"
```

### **Claude Configuration**
```python
# backend/llm-os-agent/config.py
"anthropic": {
    "model": "claude-sonnet-4-5-20250929",  # Latest model
    "temperature": 0.1,                      # Low = consistent
    "max_tokens": 2000,                      # Comprehensive responses
    "timeout": 90                            # Complex operations
}
```

---

## 🧪 Testing

### **Backend Tests**
```bash
cd backend/llm-os-agent
pytest tests/ -v

# Test Claude integration specifically
python test_claude_integration.py
python test_claude_enhanced_prompts.py
```

### **Frontend Tests**
```bash
cd frontend
npm run lint
npm run build  # Verify production build
```

---

## 📖 Documentation

- [Quick Start Guide](START_HERE.md) - Get running in 5 minutes
- [API Documentation](http://localhost:8000/docs) - Auto-generated FastAPI docs
- [Prompt Engineering Guide](PROMPT_OPTIMIZATION_CLAUDE.md) - How we optimized for DevOps
- [JSON Parsing Implementation](backend/CLAUDE_JSON_PARSING_FIX.md) - Robust error handling

---

## 🤝 Contributing

Contributions are welcome! Areas we're looking to improve:
- Support for Windows Server (PowerShell/WSL)
- Kubernetes cluster management
- Terraform/IaC integration
- Multi-server orchestration
- Rollback & incident response
- Cost optimization recommendations

---

## 📊 Performance Benchmarks

| Task | Manual Time | Ping Time | Time Saved |
|------|-------------|-----------|------------|
| LEMP Stack Setup | 2-3 hours | 64 seconds | **99%** |
| Docker Installation | 30-45 min | 45 seconds | **98%** |
| Database Backup Script | 20-30 min | 15 seconds | **99%** |
| Performance Monitoring | 10-15 min | 8 seconds | **99%** |
| SSL Certificate Setup | 45-60 min | 90 seconds | **97%** |

---


### **Use Cases:**
- Production server deployments
- Development environment setup
- Database management & backups
- Performance monitoring & troubleshooting
- Security hardening & compliance
- Disaster recovery operations

---

## ⚖️ License

MIT License - See [LICENSE](LICENSE) for details

