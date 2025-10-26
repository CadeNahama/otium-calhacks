#!/usr/bin/env python3
"""
Authentication and authorization service for Ping AI Agent
Handles user roles, permissions, and access control
"""

from enum import Enum
from typing import List, Optional
from functools import wraps
from fastapi import HTTPException, Header, Request
from .security import SecurityLevel

class UserRole(Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class Permission(Enum):
    CONNECT_SERVER = "connect_server"
    DISCONNECT_SERVER = "disconnect_server"
    SUBMIT_COMMANDS = "submit_commands"
    APPROVE_COMMANDS = "approve_commands"
    EXECUTE_COMMANDS = "execute_commands"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_USERS = "manage_users"
    VIEW_COMMANDS = "view_commands"
    MANAGE_CONNECTIONS = "manage_connections"

class AuthService:
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            Permission.CONNECT_SERVER,
            Permission.DISCONNECT_SERVER,
            Permission.SUBMIT_COMMANDS,
            Permission.APPROVE_COMMANDS,
            Permission.EXECUTE_COMMANDS,
            Permission.VIEW_AUDIT_LOGS,
            Permission.MANAGE_USERS,
            Permission.VIEW_COMMANDS,
            Permission.MANAGE_CONNECTIONS,
        ],
        UserRole.OPERATOR: [
            Permission.CONNECT_SERVER,
            Permission.DISCONNECT_SERVER,
            Permission.SUBMIT_COMMANDS,
            Permission.EXECUTE_COMMANDS,
            Permission.VIEW_AUDIT_LOGS,
            Permission.VIEW_COMMANDS,
            Permission.MANAGE_CONNECTIONS,
        ],
        UserRole.VIEWER: [
            Permission.VIEW_AUDIT_LOGS,
            Permission.VIEW_COMMANDS,
        ]
    }
    
    @classmethod
    def has_permission(cls, user_role: str, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        try:
            role = UserRole(user_role)
            return permission in cls.ROLE_PERMISSIONS.get(role, [])
        except ValueError:
            return False
    
    @classmethod
    def get_required_role_for_command(cls, risk_level: str) -> UserRole:
        """Get required role for command based on risk level"""
        risk_requirements = {
            "low": UserRole.OPERATOR,
            "medium": UserRole.OPERATOR,
            "high": UserRole.ADMIN,
            "critical": UserRole.ADMIN,
        }
        return risk_requirements.get(risk_level, UserRole.ADMIN)
    
    @classmethod
    def get_required_role_for_approval(cls, risk_level: str) -> UserRole:
        """Get required role for approving commands based on risk level"""
        approval_requirements = {
            "low": UserRole.OPERATOR,
            "medium": UserRole.OPERATOR,
            "high": UserRole.ADMIN,
            "critical": UserRole.ADMIN,
        }
        return approval_requirements.get(risk_level, UserRole.ADMIN)
    
    @classmethod
    def can_user_approve_command(cls, user_role: str, command_risk_level: str) -> bool:
        """Check if user can approve a command based on risk level"""
        required_role = cls.get_required_role_for_approval(command_risk_level)
        user_role_enum = UserRole(user_role)
        
        # Define role hierarchy
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.OPERATOR: 2,
            UserRole.ADMIN: 3,
        }
        
        return role_hierarchy.get(user_role_enum, 0) >= role_hierarchy.get(required_role, 0)
    
    @classmethod
    def get_user_permissions(cls, user_role: str) -> List[Permission]:
        """Get all permissions for a user role"""
        try:
            role = UserRole(user_role)
            return cls.ROLE_PERMISSIONS.get(role, [])
        except ValueError:
            return []

def require_permission(permission: Permission):
    """Decorator to require specific permission for endpoint access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs or headers
            user_id = kwargs.get('user_id')
            if not user_id:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get user role from database
from database_service import DatabaseService
from database import get_db
            
            db = next(get_db())
            db_service = DatabaseService(db)
            user = db_service.get_user(user_id)
            
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            if not AuthService.has_permission(user.role, permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            db.close()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(minimum_role: UserRole):
    """Decorator to require minimum role level for endpoint access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs or headers
            user_id = kwargs.get('user_id')
            if not user_id:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get user role from database
from database_service import DatabaseService
from database import get_db
            
            db = next(get_db())
            db_service = DatabaseService(db)
            user = db_service.get_user(user_id)
            
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            # Check role hierarchy
            role_hierarchy = {
                UserRole.VIEWER: 1,
                UserRole.OPERATOR: 2,
                UserRole.ADMIN: 3,
            }
            
            user_role_enum = UserRole(user.role)
            user_level = role_hierarchy.get(user_role_enum, 0)
            required_level = role_hierarchy.get(minimum_role, 0)
            
            if user_level < required_level:
                raise HTTPException(status_code=403, detail="Insufficient role level")
            
            db.close()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_user_access(user_id: str, resource_owner_id: str = None) -> bool:
    """Validate if user can access a resource"""
    if not user_id:
        return False
    
    # Users can always access their own resources
    if resource_owner_id and user_id == resource_owner_id:
        return True
    
    # Check if user is admin (admins can access all resources)
from database_service import DatabaseService
from database import get_db
    
    db = next(get_db())
    db_service = DatabaseService(db)
    user = db_service.get_user(user_id)
    
    if user and user.role == UserRole.ADMIN.value:
        db.close()
        return True
    
    db.close()
    return False

class SecurityContext:
    """Security context for request processing"""
    
    def __init__(self, user_id: str, user_role: str, ip_address: str = None, user_agent: str = None):
        self.user_id = user_id
        self.user_role = user_role
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.permissions = AuthService.get_user_permissions(user_role)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if context has specific permission"""
        return permission in self.permissions
    
    def can_approve_command(self, command_risk_level: str) -> bool:
        """Check if context can approve command"""
        return AuthService.can_user_approve_command(self.user_role, command_risk_level)
    
    def get_required_approvers(self, command_risk_level: str) -> List[str]:
        """Get list of user IDs who can approve this command"""
        required_role = AuthService.get_required_role_for_approval(command_risk_level)
        
        # Get all users with required role or higher
from database_service import DatabaseService
from database import get_db
        
        db = next(get_db())
        db_service = DatabaseService(db)
        
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.OPERATOR: 2,
            UserRole.ADMIN: 3,
        }
        
        required_level = role_hierarchy.get(required_role, 0)
        approvers = []
        
        # This would need to be implemented with a proper user query
        # For now, return empty list
        db.close()
        return approvers
