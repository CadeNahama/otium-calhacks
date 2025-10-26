# 🗄️ Database Management Guide for Ping AI Agent

This guide shows you how to set up, manage, and view all the databases and features I just built.

## 🚀 Quick Setup

### 1. **Add PostgreSQL to Railway**
```bash
# Navigate to your backend directory
cd /Users/cadenahama/CALHACKS-PING/backend

# Add PostgreSQL database
railway add --database postgres

# Check if it was added
railway variables
```

### 2. **Get Database URL**
```bash
# Get the DATABASE_URL that Railway created
railway variables get DATABASE_URL

# It should look like:
# postgresql://postgres:password@host:port/railway
```

### 3. **Initialize Database**
```bash
# Run the database setup script
python setup_database.py

# This will:
# ✅ Test database connection
# ✅ Create all tables
# ✅ Set up initial data structure
```

## 📊 **Database Tables Overview**

I created 6 main tables for enterprise functionality:

### **1. Users Table**
```sql
-- Stores user accounts and roles
users (
  id VARCHAR PRIMARY KEY,           -- User ID from your auth system
  email VARCHAR UNIQUE,             -- User email
  first_name VARCHAR,               -- First name
  last_name VARCHAR,                -- Last name
  role VARCHAR DEFAULT 'operator',  -- admin, operator, viewer
  created_at TIMESTAMP,             -- Account creation time
  last_login TIMESTAMP,             -- Last login time
  is_active BOOLEAN DEFAULT true    -- Account status
)
```

### **2. Connections Table**
```sql
-- Stores SSH connections with encrypted credentials
connections (
  id VARCHAR PRIMARY KEY,                    -- Connection ID
  user_id VARCHAR REFERENCES users(id),      -- Owner user
  hostname VARCHAR,                          -- Server hostname
  username VARCHAR,                          -- SSH username
  port INTEGER DEFAULT 22,                   -- SSH port
  encrypted_credentials TEXT,                -- 🔐 ENCRYPTED SSH credentials
  connected_at TIMESTAMP,                    -- Connection time
  disconnected_at TIMESTAMP,                 -- Disconnection time
  status VARCHAR DEFAULT 'connected',        -- connected, disconnected, error
  last_activity TIMESTAMP                    -- Last activity time
)
```

### **3. Commands Table**
```sql
-- Stores AI-generated commands
commands (
  id VARCHAR PRIMARY KEY,                           -- Command ID
  user_id VARCHAR REFERENCES users(id),             -- Owner user
  connection_id VARCHAR REFERENCES connections(id), -- Target connection
  request TEXT,                                     -- Original user request
  intent VARCHAR,                                   -- AI-detected intent
  action VARCHAR,                                   -- AI-detected action
  risk_level VARCHAR DEFAULT 'medium',              -- low, medium, high, critical
  priority VARCHAR DEFAULT 'normal',                -- low, normal, high, urgent
  status VARCHAR DEFAULT 'pending_approval',        -- Command status
  generated_commands JSON,                          -- Array of command steps
  execution_results JSON,                           -- Execution results
  created_at TIMESTAMP,                             -- Creation time
  approved_at TIMESTAMP,                            -- Approval time
  executed_at TIMESTAMP,                            -- Execution time
  completed_at TIMESTAMP,                           -- Completion time
  approved_by VARCHAR                               -- Who approved it
)
```

### **4. Command Approvals Table** (🎯 **Cursor-Style Approval**)
```sql
-- Stores step-by-step approvals (like Cursor)
command_approvals (
  id VARCHAR PRIMARY KEY,                    -- Approval ID
  command_id VARCHAR REFERENCES commands(id), -- Parent command
  user_id VARCHAR REFERENCES users(id),      -- Who approved/rejected
  step_index INTEGER,                        -- Which step (0, 1, 2, etc.)
  approved BOOLEAN,                          -- true = approved, false = rejected
  approval_reason TEXT,                      -- Reason for approval/rejection
  approved_at TIMESTAMP                      -- When it was approved/rejected
)
```

### **5. Audit Logs Table**
```sql
-- Complete audit trail for compliance
audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,     -- Log ID
  user_id VARCHAR REFERENCES users(id),     -- Who performed action
  command_id VARCHAR REFERENCES commands(id), -- Related command
  connection_id VARCHAR,                     -- Related connection
  action VARCHAR,                           -- Action performed
  details JSON,                             -- Additional context
  system_state_before JSON,                 -- System state before action
  system_state_after JSON,                  -- System state after action
  timestamp TIMESTAMP,                      -- When action occurred
  ip_address VARCHAR,                       -- User's IP address
  user_agent VARCHAR,                       -- User's browser/agent
  success BOOLEAN,                          -- Did action succeed?
  error_message TEXT                        -- Error details if failed
)
```

### **6. System Checkpoints Table**
```sql
-- System state snapshots for rollback capability
system_checkpoints (
  id VARCHAR PRIMARY KEY,                           -- Checkpoint ID
  connection_id VARCHAR REFERENCES connections(id), -- Target connection
  checkpoint_name VARCHAR,                          -- Checkpoint name
  system_state JSON,                                -- Complete system state
  created_at TIMESTAMP,                             -- Creation time
  created_by VARCHAR,                               -- Who created it
  description TEXT                                  -- Checkpoint description
)
```

## 🔍 **How to View & Manage Your Data**

### **Option 1: Railway Dashboard (Recommended)**
```bash
# Open Railway dashboard in browser
railway open

# Navigate to:
# 1. Your project → Database service
# 2. Click "Data" tab
# 3. Browse tables and run SQL queries
```

### **Option 2: Command Line Database Access**
```bash
# Connect to your Railway PostgreSQL database
railway connect postgres

# Or use psql directly
psql $DATABASE_URL

# Useful queries:
SELECT * FROM users;                    -- View all users
SELECT * FROM connections;              -- View all connections
SELECT * FROM commands ORDER BY created_at DESC LIMIT 10;  -- Recent commands
SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 20; -- Recent activity
```

### **Option 3: Database Management Script**
```bash
# Show database information
python setup_database.py info

# Show Railway-specific help
python setup_database.py railway
```

## 🔐 **Security Features**

### **Encrypted Credentials**
- All SSH passwords are encrypted using Fernet encryption
- Encryption key stored in `PING_ENCRYPTION_KEY` environment variable
- Credentials are never stored in plain text

### **Audit Trail**
- Every action is logged with full context
- Includes user, timestamp, IP address, success/failure
- Perfect for compliance and debugging

### **Role-Based Access**
- **Admin**: Full access to everything
- **Operator**: Can connect, submit commands, execute approved commands
- **Viewer**: Can only view audit logs and command history

## 🎯 **Step-by-Step Approval Workflow**

### **How It Works (Cursor-Style)**
1. User submits task: "Check system status"
2. AI generates commands:
   - Step 1: `ls -la` (auto-approved - safe command)
   - Step 2: `systemctl status nginx` (requires approval)
   - Step 3: `netstat -tlnp` (auto-approved - safe command)
3. User sees each step individually
4. User approves/rejects each step that needs approval
5. Only when ALL steps are approved can the command execute
6. Each approval is logged in `command_approvals` table

### **View Approval Status**
```sql
-- See all pending approvals
SELECT c.id, c.request, COUNT(ca.step_index) as pending_steps
FROM commands c
LEFT JOIN command_approvals ca ON c.id = ca.command_id AND ca.approved = false
WHERE c.status = 'pending_approval'
GROUP BY c.id, c.request;

-- See step-by-step approval details
SELECT 
  c.request,
  c.generated_commands->ca.step_index->>'command' as step_command,
  ca.approved,
  ca.approval_reason,
  ca.approved_at
FROM commands c
JOIN command_approvals ca ON c.id = ca.command_id
ORDER BY c.created_at DESC, ca.step_index;
```

## 🚀 **Deployment Commands**

### **Deploy Everything**
```bash
# Make deployment script executable
chmod +x deploy_phase1.sh

# Run deployment (this will):
# ✅ Add PostgreSQL to Railway
# ✅ Set up encryption keys
# ✅ Initialize database tables
# ✅ Deploy enhanced API server
./deploy_phase1.sh
```

### **Manual Deployment Steps**
```bash
# 1. Add PostgreSQL
railway add --database postgres

# 2. Set encryption key
railway variables set PING_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# 3. Initialize database
python setup_database.py

# 4. Deploy
railway up
```

## 📱 **Frontend Integration**

### **Update Your Frontend**
1. Replace `TaskSubmissionCard` with `TaskSubmissionCardEnhanced`
2. The new component shows each command step individually
3. Users can approve/reject each step with visual indicators
4. Real-time approval status updates

### **New API Endpoints**
- `POST /api/commands/{id}/approve-step` - Approve/reject individual step
- `GET /api/commands/{id}/approval-status` - Get step approval status
- `POST /api/commands/{id}/execute` - Execute fully approved command

## 🎉 **What You Now Have**

✅ **Production-ready database** with PostgreSQL  
✅ **Encrypted credential storage** - SSH passwords never stored in plain text  
✅ **Cursor-style approval** - Each command step approved individually  
✅ **Complete audit trail** - Every action logged for compliance  
✅ **Role-based security** - Admin/Operator/Viewer permissions  
✅ **Rate limiting** - Prevents abuse (5 connections/min, 10 commands/min)  
✅ **Input validation** - Blocks malicious commands  
✅ **Database persistence** - All data survives restarts  

## 🔧 **Troubleshooting**

### **Database Connection Issues**
```bash
# Check if DATABASE_URL is set
echo $DATABASE_URL

# Test database connection
python setup_database.py info

# Check Railway variables
railway variables
```

### **Missing Tables**
```bash
# Recreate all tables
python setup_database.py

# Or manually
cd llm-os-agent
python -c "from database import init_database; init_database()"
```

### **Permission Issues**
- Make sure your user has the correct role in the `users` table
- Check `audit_logs` table for permission-related errors

---

**🎯 Ready to deploy? Run `./deploy_phase1.sh` to get everything set up!**
