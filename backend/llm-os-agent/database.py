#!/usr/bin/env python3
"""
Database models and configuration for Otium AI Agent
Uses SQLAlchemy with PostgreSQL for enterprise-grade persistence
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(String, default="operator")  # admin, operator, viewer
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")
    commands = relationship("Command", back_populates="user")
    connections = relationship("Connection", back_populates="user")
    command_approvals = relationship("CommandApproval", back_populates="user")

class Connection(Base):
    __tablename__ = "connections"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    hostname = Column(String, nullable=False)
    username = Column(String, nullable=False)
    port = Column(Integer, default=22)
    encrypted_credentials = Column(Text, nullable=False)  # Encrypted SSH credentials
    connected_at = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime)
    status = Column(String, default="connected")  # connected, disconnected, error
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="connections")
    commands = relationship("Command", back_populates="connection")
    checkpoints = relationship("SystemCheckpoint", back_populates="connection")

class Command(Base):
    __tablename__ = "commands"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    connection_id = Column(String, ForeignKey("connections.id"), nullable=False)
    request = Column(Text, nullable=False)
    intent = Column(String)
    action = Column(String)
    risk_level = Column(String, default="medium")  # low, medium, high, critical
    priority = Column(String, default="normal")  # low, normal, high, urgent
    status = Column(String, default="pending_approval")  # pending_approval, approved, executing, completed, failed, rejected
    generated_commands = Column(JSON)  # Array of command steps (legacy)
    execution_results = Column(JSON)  # Results from execution
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    executed_at = Column(DateTime)
    completed_at = Column(DateTime)
    approved_by = Column(String)  # User ID who approved
    
    # New state-aware execution fields
    current_step_index = Column(Integer, default=0)
    requires_state_evaluation = Column(Boolean, default=True)
    adaptive_mode = Column(Boolean, default=False)
    baseline_system_state = Column(JSON)
    last_state_evaluation = Column(DateTime)
    state_evaluation_count = Column(Integer, default=0)
    adaptive_steps_generated = Column(Integer, default=0)
    corrective_steps_generated = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="commands")
    connection = relationship("Connection", back_populates="commands")
    audit_logs = relationship("AuditLog", back_populates="command")
    approvals = relationship("CommandApproval", back_populates="command")
    steps = relationship("CommandStep", back_populates="command_ref")
    state_snapshots = relationship("SystemStateSnapshot", back_populates="command_ref")
    messages = relationship("CommandMessage", back_populates="command_ref")

class CommandApproval(Base):
    __tablename__ = "command_approvals"
    
    id = Column(String, primary_key=True)
    command_id = Column(String, ForeignKey("commands.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    step_index = Column(Integer, nullable=False)  # Which step is being approved
    approved = Column(Boolean, nullable=False)  # True for approve, False for reject
    approval_reason = Column(Text)  # Optional reason for approval/rejection
    approved_at = Column(DateTime, default=datetime.utcnow)
    
    # New state-aware approval fields
    step_id = Column(String, ForeignKey("command_steps.id"))  # Direct reference to specific step
    state_context = Column(JSON)  # System state when approved
    approval_reasoning = Column(Text)  # Human-readable reasoning for approval
    expected_impact = Column(JSON)  # Expected system changes
    
    # Relationships
    command = relationship("Command", back_populates="approvals")
    user = relationship("User", back_populates="command_approvals")
    step = relationship("CommandStep", back_populates="approvals")

class CommandMessage(Base):
    __tablename__ = "command_messages"
    
    id = Column(String, primary_key=True)
    command_id = Column(String, ForeignKey("commands.id"), nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'ai'
    message = Column(Text, nullable=False)
    message_type = Column(String, default="chat")  # 'chat', 'system', 'command_update'
    message_metadata = Column(JSON)  # Additional context (e.g., which step was discussed)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    command_ref = relationship("Command", back_populates="messages")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    command_id = Column(String, ForeignKey("commands.id"))
    connection_id = Column(String)
    action = Column(String, nullable=False)  # connect, disconnect, submit_command, approve_command, execute_command, etc.
    details = Column(JSON)  # Additional context
    system_state_before = Column(JSON)  # System state before action
    system_state_after = Column(JSON)  # System state after action
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    user_agent = Column(String)
    success = Column(Boolean)
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    command = relationship("Command", back_populates="audit_logs")

class SystemCheckpoint(Base):
    __tablename__ = "system_checkpoints"
    
    id = Column(String, primary_key=True)
    connection_id = Column(String, ForeignKey("connections.id"), nullable=False)
    checkpoint_name = Column(String, nullable=False)
    system_state = Column(JSON, nullable=False)  # Complete system state snapshot
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=False)  # User ID
    description = Column(Text)
    
    # Relationships
    connection = relationship("Connection", back_populates="checkpoints")

class CommandStep(Base):
    __tablename__ = "command_steps"
    
    id = Column(String, primary_key=True)
    command_id = Column(String, ForeignKey("commands.id"), nullable=False)
    step_index = Column(Integer, nullable=False)
    step_type = Column(String, default="generated")  # 'generated', 'adaptive', 'corrective'
    command = Column(Text, nullable=False)
    explanation = Column(Text)
    risk_level = Column(String, default="medium")
    status = Column(String, default="pending")  # 'pending', 'approved', 'executing', 'completed', 'failed', 'skipped'
    execution_result = Column(JSON)  # Results from step execution
    system_state_before = Column(JSON)  # System state before step execution
    system_state_after = Column(JSON)  # System state after step execution
    expected_outcome = Column(Text)  # What this step should achieve
    generated_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    command_ref = relationship("Command", back_populates="steps")
    evaluations = relationship("StepEvaluation", back_populates="step")
    state_snapshots = relationship("SystemStateSnapshot", back_populates="step")
    approvals = relationship("CommandApproval", back_populates="step")

class SystemStateSnapshot(Base):
    __tablename__ = "system_state_snapshots"
    
    id = Column(String, primary_key=True)
    command_id = Column(String, ForeignKey("commands.id"), nullable=False)
    step_id = Column(String, ForeignKey("command_steps.id"))
    snapshot_type = Column(String, nullable=False)  # 'before_step', 'after_step', 'baseline'
    system_info = Column(JSON, nullable=False)  # Complete system state
    services_status = Column(JSON)  # Running/stopped services
    packages_installed = Column(JSON)  # Installed packages
    network_connections = Column(JSON)  # Network state
    file_system_state = Column(JSON)  # File system changes
    process_list = Column(JSON)  # Running processes
    resource_usage = Column(JSON)  # CPU, memory, disk usage
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    command_ref = relationship("Command", back_populates="state_snapshots")
    step = relationship("CommandStep", back_populates="state_snapshots")

class StepEvaluation(Base):
    __tablename__ = "step_evaluations"
    
    id = Column(String, primary_key=True)
    step_id = Column(String, ForeignKey("command_steps.id"), nullable=False)
    evaluation_type = Column(String, nullable=False)  # 'success', 'failure', 'partial', 'unexpected'
    success_indicators = Column(JSON)  # What indicates success
    failure_indicators = Column(JSON)  # What indicates failure
    state_changes = Column(JSON)  # Detected changes in system state
    recommendations = Column(JSON)  # Suggested next actions
    confidence_score = Column(DECIMAL(3, 2))  # 0.00 to 1.00 confidence in evaluation
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    step = relationship("CommandStep", back_populates="evaluations")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # For development, use SQLite
    DATABASE_URL = "sqlite:///./otium.db"
    print("⚠️  DATABASE_URL not set, using SQLite for development")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with tables"""
    create_tables()
    print("✅ Database tables created successfully")
