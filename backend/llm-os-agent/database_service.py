#!/usr/bin/env python3
"""
Database service layer for Ping AI Agent
Provides high-level database operations with business logic
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import threading
from database import User, Connection, Command, CommandApproval, AuditLog, SystemCheckpoint

# Global REENTRANT lock for execution results updates to prevent race conditions
# RLock allows the same thread to acquire the lock multiple times
_execution_results_lock = threading.RLock()

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db
    
    # User management
    def create_or_get_user(self, user_id: str, email: str, first_name: str = None, last_name: str = None) -> User:
        """
        Return an existing user (by id OR email) or create a new one.
        Never update the primary-key once it exists.
        """
        # 1. Exact-id match (normal case)
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            return user

        # 2. Existing user with this email ─ return it unchanged
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"[DEBUG] Found existing user with email {email}, returning user ID {existing_user.id} (no ID change)")
            return existing_user          # ← DON'T change primary key!

        # 3. Create new record
        try:
            user = User(
                id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            print(f"[DEBUG] Created new user with ID {user_id} and email {email}")
            return user
        except Exception as e:
            # Handle any remaining constraint violations gracefully
            self.db.rollback()
            print(f"[DEBUG] Error creating user, trying to get existing: {str(e)}")
            # Try one more time to get existing user by email
            existing_user = self.db.query(User).filter(User.email == email).first()
            if existing_user:
                return existing_user
            raise e
    
    def update_user_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    # Connection management
    def create_connection(self, user_id: str, hostname: str, username: str, 
                         encrypted_credentials: str, port: int = 22) -> Connection:
        """Create new connection record"""
        connection = Connection(
            id=str(uuid.uuid4()),
            user_id=user_id,
            hostname=hostname,
            username=username,
            encrypted_credentials=encrypted_credentials,
            port=port
        )
        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        return connection
    
    def get_user_connections(self, user_id: str) -> List[Connection]:
        """Get all active connections for user"""
        return self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.status == "connected"
        ).all()
    
    def get_user_active_connections(self, user_id: str) -> List[Connection]:
        """Get only active/connected connections for a user"""
        return self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.status == "connected",
            Connection.disconnected_at.is_(None)
        ).all()
    
    def get_connection(self, connection_id: str, user_id: str) -> Optional[Connection]:
        """Get specific connection for user"""
        return self.db.query(Connection).filter(
            Connection.id == connection_id,
            Connection.user_id == user_id
        ).first()
    
    def disconnect_connection(self, connection_id: str):
        """Mark connection as disconnected"""
        connection = self.db.query(Connection).filter(Connection.id == connection_id).first()
        if connection:
            connection.status = "disconnected"
            connection.disconnected_at = datetime.utcnow()
            self.db.commit()
    
    def disconnect_all_user_connections(self, user_id: str):
        """Mark ALL connections for a user as disconnected (for session cleanup)"""
        connections = self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.status == "connected"
        ).all()
        
        for connection in connections:
            connection.status = "disconnected"
            connection.disconnected_at = datetime.utcnow()
        
        if connections:
            self.db.commit()
            print(f"[DEBUG] Disconnected {len(connections)} connections for user {user_id}")
    
    # Command management
    def create_command(self, user_id: str, connection_id: str, request: str, 
                      intent: str, action: str, risk_level: str, priority: str, 
                      generated_commands: dict) -> Command:
        """Create new command record"""
        command = Command(
            id=str(uuid.uuid4()),
            user_id=user_id,
            connection_id=connection_id,
            request=request,
            intent=intent,
            action=action,
            risk_level=risk_level,
            priority=priority,
            generated_commands=generated_commands
        )
        self.db.add(command)
        self.db.commit()
        self.db.refresh(command)
        return command
    
    def get_user_commands(self, user_id: str, limit: int = 50, status: str = None, 
                         connection_id: str = None) -> List[Command]:
        """Get commands for user with optional filtering - session must remain open for serialization"""
        query = self.db.query(Command).filter(Command.user_id == user_id)
        
        if status:
            query = query.filter(Command.status == status)
        if connection_id:
            query = query.filter(Command.connection_id == connection_id)
        
        # Order by newest first and apply limit
        results = query.order_by(Command.created_at.desc()).limit(limit).all()
        
        # Important: Don't close session here - caller must keep it open during serialization
        return results
    
    def get_command(self, command_id: str, user_id: str) -> Optional[Command]:
        """Get specific command for user"""
        return self.db.query(Command).filter(
            Command.id == command_id,
            Command.user_id == user_id
        ).first()
    
    def update_command_status(self, command_id: str, status: str, approved_by: str = None):
        """Update command status"""
        command = self.db.query(Command).filter(Command.id == command_id).first()
        if command:
            command.status = status
            if status == "approved" and approved_by:
                command.approved_at = datetime.utcnow()
                command.approved_by = approved_by
            elif status == "executing":
                command.executed_at = datetime.utcnow()
            elif status in ["completed", "failed"]:
                command.completed_at = datetime.utcnow()
            self.db.commit()
    
    def complete_command(self, command_id: str, execution_results: dict):
        """Mark command as completed with results"""
        command = self.db.query(Command).filter(Command.id == command_id).first()
        if command:
            command.status = "completed"
            command.executed_at = datetime.utcnow()
            command.completed_at = datetime.utcnow()
            command.execution_results = execution_results
            self.db.commit()
    
    def update_command_execution_results(self, command_id: str, execution_results: dict):
        """Update command execution results - the API already aggregates results, just save them"""
        # Use threading lock to prevent race conditions when multiple steps execute concurrently
        with _execution_results_lock:
            command = self.db.query(Command).filter(Command.id == command_id).first()
            if command:
                # The API already built the complete aggregated results, just save them
                command.execution_results = execution_results
                
                # Mark as executed if not already
                if not command.executed_at:
                    command.executed_at = datetime.utcnow()
                self.db.commit()
                self.db.refresh(command)
    
    # Command approval management (step-by-step like Cursor)
    def create_step_approval(self, command_id: str, user_id: str, step_index: int, 
                           approved: bool, reason: str = None) -> CommandApproval:
        """Create approval/rejection for specific command step"""
        approval = CommandApproval(
            id=str(uuid.uuid4()),
            command_id=command_id,
            user_id=user_id,
            step_index=step_index,
            approved=approved,
            approval_reason=reason
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval
    
    def get_command_approvals(self, command_id: str) -> List[CommandApproval]:
        """Get all approvals for a command"""
        return self.db.query(CommandApproval).filter(
            CommandApproval.command_id == command_id
        ).order_by(CommandApproval.step_index).all()
    
    def get_step_approval_status(self, command_id: str) -> Dict[int, Dict[str, Any]]:
        """Get approval status for each step of a command"""
        approvals = self.get_command_approvals(command_id)
        command = self.db.query(Command).filter(Command.id == command_id).first()
        
        if not command or not command.generated_commands:
            return {}
        
        step_status = {}
        total_steps = len(command.generated_commands)
        
        # Initialize all steps as pending
        for i in range(total_steps):
            step_status[i] = {
                "status": "pending",
                "approved": None,
                "approved_by": None,
                "reason": None,
                "approved_at": None
            }
        
        # Update with actual approvals
        for approval in approvals:
            if approval.step_index < total_steps:
                step_status[approval.step_index] = {
                    "status": "approved" if approval.approved else "rejected",
                    "approved": approval.approved,
                    "approved_by": approval.user_id,
                    "reason": approval.approval_reason,
                    "approved_at": approval.approved_at
                }
        
        return step_status
    
    def is_command_fully_approved(self, command_id: str) -> bool:
        """Check if all steps of a command are approved"""
        step_status = self.get_step_approval_status(command_id)
        if not step_status:
            return False
        
        # Check if all steps are approved
        for step_data in step_status.values():
            if step_data["status"] != "approved":
                return False
        
        return True
    
    def get_pending_steps(self, command_id: str) -> List[int]:
        """Get list of step indices that are pending approval"""
        step_status = self.get_step_approval_status(command_id)
        return [step_index for step_index, status in step_status.items() 
                if status["status"] == "pending"]
    
    # Audit logging
    def log_action(self, user_id: str, action: str, details: dict = None, 
                   command_id: str = None, connection_id: str = None,
                   system_state_before: dict = None, system_state_after: dict = None,
                   ip_address: str = None, user_agent: str = None,
                   success: bool = True, error_message: str = None):
        """Log user action for audit trail"""
        audit_log = AuditLog(
            user_id=user_id,
            command_id=command_id,
            connection_id=connection_id,
            action=action,
            details=details,
            system_state_before=system_state_before,
            system_state_after=system_state_after,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        self.db.add(audit_log)
        self.db.commit()
    
    def get_audit_logs(self, user_id: str = None, start_date: datetime = None, 
                      end_date: datetime = None, limit: int = 100) -> List[AuditLog]:
        """Get audit logs with optional filtering"""
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    # System checkpoints
    def create_checkpoint(self, connection_id: str, checkpoint_name: str,
                         system_state: dict, created_by: str, description: str = None) -> SystemCheckpoint:
        """Create system checkpoint"""
        checkpoint = SystemCheckpoint(
            id=str(uuid.uuid4()),
            connection_id=connection_id,
            checkpoint_name=checkpoint_name,
            system_state=system_state,
            created_by=created_by,
            description=description
        )
        self.db.add(checkpoint)
        self.db.commit()
        self.db.refresh(checkpoint)
        return checkpoint
    
    def get_checkpoints(self, connection_id: str) -> List[SystemCheckpoint]:
        """Get all checkpoints for a connection"""
        return self.db.query(SystemCheckpoint).filter(
            SystemCheckpoint.connection_id == connection_id
        ).order_by(SystemCheckpoint.created_at.desc()).all()
