#!/usr/bin/env python3
"""
Unit tests for database models and services
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, User, Connection, Command, CommandApproval, AuditLog, SystemCheckpoint
from database_service import DatabaseService

@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def db_service(db_session):
    """Create database service instance"""
    return DatabaseService(db_session)

def test_create_user(db_service):
    """Test user creation"""
    user = db_service.create_or_get_user(
        user_id="test_user",
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )
    
    assert user.id == "test_user"
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.role == "operator"  # Default role
    assert user.is_active == True

def test_create_connection(db_service):
    """Test connection creation"""
    # First create user
    user = db_service.create_or_get_user("test_user", "test@example.com")
    
    connection = db_service.create_connection(
        user_id="test_user",
        hostname="test.example.com",
        username="testuser",
        encrypted_credentials="encrypted_data",
        port=22
    )
    
    assert connection.user_id == "test_user"
    assert connection.hostname == "test.example.com"
    assert connection.username == "testuser"
    assert connection.port == 22
    assert connection.status == "connected"
    assert connection.encrypted_credentials == "encrypted_data"

def test_create_command(db_service):
    """Test command creation"""
    # Create user and connection first
    user = db_service.create_or_get_user("test_user", "test@example.com")
    connection = db_service.create_connection(
        user_id="test_user",
        hostname="test.example.com",
        username="testuser",
        encrypted_credentials="encrypted_data"
    )
    
    generated_commands = [
        {"command": "ls -la", "explanation": "List files", "risk_level": "low"},
        {"command": "df -h", "explanation": "Check disk usage", "risk_level": "low"}
    ]
    
    command = db_service.create_command(
        user_id="test_user",
        connection_id=connection.id,
        request="Check system status",
        intent="System monitoring",
        action="List files and check disk",
        risk_level="low",
        priority="normal",
        generated_commands=generated_commands
    )
    
    assert command.user_id == "test_user"
    assert command.connection_id == connection.id
    assert command.request == "Check system status"
    assert command.risk_level == "low"
    assert command.status == "pending_approval"
    assert len(command.generated_commands) == 2

def test_step_approval(db_service):
    """Test step-by-step approval"""
    # Create user, connection, and command
    user = db_service.create_or_get_user("test_user", "test@example.com")
    connection = db_service.create_connection(
        user_id="test_user",
        hostname="test.example.com",
        username="testuser",
        encrypted_credentials="encrypted_data"
    )
    
    generated_commands = [
        {"command": "ls -la", "explanation": "List files", "risk_level": "low"},
        {"command": "df -h", "explanation": "Check disk usage", "risk_level": "low"}
    ]
    
    command = db_service.create_command(
        user_id="test_user",
        connection_id=connection.id,
        request="Check system status",
        intent="System monitoring",
        action="List files and check disk",
        risk_level="low",
        priority="normal",
        generated_commands=generated_commands
    )
    
    # Approve first step
    approval1 = db_service.create_step_approval(
        command_id=command.id,
        user_id="test_user",
        step_index=0,
        approved=True,
        reason="Safe command"
    )
    
    # Reject second step
    approval2 = db_service.create_step_approval(
        command_id=command.id,
        user_id="test_user",
        step_index=1,
        approved=False,
        reason="Not needed"
    )
    
    # Check approval status
    step_status = db_service.get_step_approval_status(command.id)
    
    assert len(step_status) == 2
    assert step_status[0]["status"] == "approved"
    assert step_status[1]["status"] == "rejected"
    assert not db_service.is_command_fully_approved(command.id)

def test_audit_logging(db_service):
    """Test audit logging"""
    # Create user first
    user = db_service.create_or_get_user("test_user", "test@example.com")
    
    # Log an action
    db_service.log_action(
        user_id="test_user",
        action="test_action",
        details={"test": "data"},
        success=True
    )
    
    # Get audit logs
    logs = db_service.get_audit_logs(user_id="test_user", limit=10)
    
    assert len(logs) == 1
    assert logs[0].user_id == "test_user"
    assert logs[0].action == "test_action"
    assert logs[0].success == True
    assert logs[0].details == {"test": "data"}

def test_user_connections(db_service):
    """Test getting user connections"""
    # Create user and multiple connections
    user = db_service.create_or_get_user("test_user", "test@example.com")
    
    conn1 = db_service.create_connection(
        user_id="test_user",
        hostname="server1.example.com",
        username="user1",
        encrypted_credentials="encrypted_data1"
    )
    
    conn2 = db_service.create_connection(
        user_id="test_user",
        hostname="server2.example.com",
        username="user2",
        encrypted_credentials="encrypted_data2"
    )
    
    # Get user connections
    connections = db_service.get_user_connections("test_user")
    
    assert len(connections) == 2
    assert connections[0].hostname in ["server1.example.com", "server2.example.com"]
    assert connections[1].hostname in ["server1.example.com", "server2.example.com"]

if __name__ == "__main__":
    pytest.main([__file__])
