#!/usr/bin/env python3
"""
In-Memory Storage Service for Ping AI Agent
Session-based storage that persists only while backend is running
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

class InMemoryStorage:
    """
    Session-based in-memory storage for all application data.
    Data persists only while the backend is running.
    """
    
    def __init__(self):
        # Storage dictionaries
        self.users: Dict[str, Dict] = {}
        self.connections: Dict[str, Dict] = {}
        self.commands: Dict[str, Dict] = {}
        self.command_approvals: Dict[str, List[Dict]] = {}  # command_id -> list of approvals
        self.audit_logs: List[Dict] = []
        
        print("[MEMORY] In-memory storage initialized")
    
    # User Management
    def create_or_get_user(self, user_id: str, email: str = None) -> Dict:
        """Create or get user"""
        if user_id not in self.users:
            self.users[user_id] = {
                "id": user_id,
                "email": email or f"{user_id}@otium.local",
                "role": "operator",
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "is_active": True
            }
            print(f"[MEMORY] Created new user: {user_id}")
        else:
            # Update last login
            self.users[user_id]["last_login"] = datetime.utcnow()
            print(f"[MEMORY] User {user_id} logged in")
        
        return self.users[user_id]
    
    def update_user_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        if user_id in self.users:
            self.users[user_id]["last_login"] = datetime.utcnow()
    
    # Connection Management
    def create_connection(self, user_id: str, hostname: str, username: str, 
                         encrypted_credentials: str, port: int = 22, connection_id: str = None) -> str:
        """Create new connection record"""
        if connection_id is None:
            connection_id = str(uuid.uuid4())
        self.connections[connection_id] = {
            "id": connection_id,
            "user_id": user_id,
            "hostname": hostname,
            "username": username,
            "port": port,
            "encrypted_credentials": encrypted_credentials,
            "connected_at": datetime.utcnow(),
            "disconnected_at": None,
            "status": "connected",
            "last_activity": datetime.utcnow()
        }
        print(f"[MEMORY] Created connection {connection_id} for user {user_id}")
        return connection_id
    
    def get_connection(self, connection_id: str, user_id: str) -> Optional[Dict]:
        """Get connection by ID"""
        conn = self.connections.get(connection_id)
        if conn and conn["user_id"] == user_id:
            return conn
        return None
    
    def get_user_active_connections(self, user_id: str) -> List[Dict]:
        """Get all active connections for a user"""
        return [
            conn for conn in self.connections.values()
            if conn["user_id"] == user_id and conn["status"] == "connected"
        ]
    
    def disconnect_connection(self, connection_id: str):
        """Mark connection as disconnected"""
        if connection_id in self.connections:
            self.connections[connection_id]["status"] = "disconnected"
            self.connections[connection_id]["disconnected_at"] = datetime.utcnow()
            print(f"[MEMORY] Disconnected connection {connection_id}")
    
    def disconnect_all_user_connections(self, user_id: str):
        """Disconnect all connections for a user"""
        count = 0
        for conn in self.connections.values():
            if conn["user_id"] == user_id and conn["status"] == "connected":
                conn["status"] = "disconnected"
                conn["disconnected_at"] = datetime.utcnow()
                count += 1
        print(f"[MEMORY] Disconnected {count} connections for user {user_id}")
    
    # Command Management
    def create_command(self, user_id: str, connection_id: str, request: str,
                      intent: str, action: str, risk_level: str, priority: str,
                      generated_commands: List[Dict]) -> Dict:
        """Create new command record"""
        command_id = str(uuid.uuid4())
        command = {
            "id": command_id,
            "user_id": user_id,
            "connection_id": connection_id,
            "request": request,
            "intent": intent,
            "action": action,
            "risk_level": risk_level,
            "priority": priority,
            "status": "pending_approval",
            "generated_commands": generated_commands,
            "execution_results": None,
            "created_at": datetime.utcnow(),
            "approved_at": None,
            "executed_at": None,
            "completed_at": None,
            "approved_by": None
        }
        self.commands[command_id] = command
        self.command_approvals[command_id] = []  # Initialize empty approvals list
        print(f"[MEMORY] Created command {command_id} for user {user_id}")
        return command
    
    def get_command(self, command_id: str, user_id: str) -> Optional[Dict]:
        """Get command by ID"""
        cmd = self.commands.get(command_id)
        if cmd and cmd["user_id"] == user_id:
            return cmd
        return None
    
    def get_user_commands(self, user_id: str, limit: int = 50, 
                         status: str = None, connection_id: str = None) -> List[Dict]:
        """Get commands for a user with optional filters"""
        commands = [
            cmd for cmd in self.commands.values()
            if cmd["user_id"] == user_id
        ]
        
        # Apply filters
        if status:
            commands = [cmd for cmd in commands if cmd["status"] == status]
        if connection_id:
            commands = [cmd for cmd in commands if cmd["connection_id"] == connection_id]
        
        # Sort by created_at descending
        commands.sort(key=lambda x: x["created_at"], reverse=True)
        
        return commands[:limit]
    
    def update_command_status(self, command_id: str, status: str, user_id: str = None):
        """Update command status"""
        if command_id in self.commands:
            self.commands[command_id]["status"] = status
            
            if status == "approved":
                self.commands[command_id]["approved_at"] = datetime.utcnow()
                if user_id:
                    self.commands[command_id]["approved_by"] = user_id
            elif status == "executing":
                self.commands[command_id]["executed_at"] = datetime.utcnow()
            elif status in ["completed", "failed"]:
                self.commands[command_id]["completed_at"] = datetime.utcnow()
            
            print(f"[MEMORY] Updated command {command_id} status to {status}")
    
    def update_command_execution_results(self, command_id: str, results: Dict):
        """Update command execution results"""
        if command_id in self.commands:
            self.commands[command_id]["execution_results"] = results
            print(f"[MEMORY] Updated execution results for command {command_id}")
    
    def complete_command(self, command_id: str, execution_results: Dict):
        """Mark command as completed with results"""
        if command_id in self.commands:
            self.commands[command_id]["execution_results"] = execution_results
            self.commands[command_id]["status"] = "completed"
            self.commands[command_id]["completed_at"] = datetime.utcnow()
            print(f"[MEMORY] Completed command {command_id}")
    
    # Command Approval Management
    def create_step_approval(self, command_id: str, user_id: str, step_index: int,
                           approved: bool, reason: str = None) -> Dict:
        """Create step approval record"""
        approval = {
            "id": str(uuid.uuid4()),
            "command_id": command_id,
            "user_id": user_id,
            "step_index": step_index,
            "approved": approved,
            "approval_reason": reason,
            "approved_at": datetime.utcnow()
        }
        
        if command_id not in self.command_approvals:
            self.command_approvals[command_id] = []
        
        self.command_approvals[command_id].append(approval)
        print(f"[MEMORY] Created approval for command {command_id}, step {step_index}: {approved}")
        return approval
    
    def get_command_approvals(self, command_id: str) -> List[Dict]:
        """Get all approvals for a command"""
        return self.command_approvals.get(command_id, [])
    
    def is_command_fully_approved(self, command_id: str) -> bool:
        """Check if all steps of a command are approved"""
        if command_id not in self.commands:
            return False
        
        command = self.commands[command_id]
        total_steps = len(command.get("generated_commands", []))
        approvals = self.command_approvals.get(command_id, [])
        
        # Check if we have approvals for all steps and all are approved
        approved_steps = [a for a in approvals if a["approved"]]
        return len(approved_steps) == total_steps
    
    # Audit Logging
    def log_action(self, user_id: str, action: str, details: Dict = None,
                  command_id: str = None, connection_id: str = None,
                  ip_address: str = None, user_agent: str = None, success: bool = True):
        """Log an action"""
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "command_id": command_id,
            "connection_id": connection_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "timestamp": datetime.utcnow()
        }
        self.audit_logs.append(log_entry)
        print(f"[MEMORY] Logged action: {action} by user {user_id}")
    
    def get_audit_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Get audit logs with optional user filter"""
        logs = self.audit_logs
        
        if user_id:
            logs = [log for log in logs if log["user_id"] == user_id]
        
        # Sort by timestamp descending
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return logs[:limit]
    
    # Utility Methods
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        return {
            "users": len(self.users),
            "connections": len(self.connections),
            "active_connections": len([c for c in self.connections.values() if c["status"] == "connected"]),
            "commands": len(self.commands),
            "audit_logs": len(self.audit_logs)
        }
    
    def clear_all(self):
        """Clear all data (for testing)"""
        self.users.clear()
        self.connections.clear()
        self.commands.clear()
        self.command_approvals.clear()
        self.audit_logs.clear()
        print("[MEMORY] Cleared all data")

# Global in-memory storage instance
memory_storage = InMemoryStorage()


