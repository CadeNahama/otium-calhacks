#!/usr/bin/env python3
"""
Security validation and sanitization for Otium AI Agent
Provides input validation, sanitization, and security checks
"""

import re
import html
from typing import List
from enum import Enum

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityValidator:
    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """Validate hostname format"""
        if not hostname or len(hostname) > 255:
            return False
        
        # Basic hostname validation
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, hostname))
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """Validate port number"""
        return 1 <= port <= 65535
    
    @staticmethod
    def sanitize_command(command: str) -> str:
        """Sanitize command input"""
        # Remove potentially dangerous characters
        dangerous_chars = ['`', '$', ';', '|', '&', '&&', '||']
        for char in dangerous_chars:
            command = command.replace(char, '')
        
        # HTML escape
        command = html.escape(command)
        
        return command.strip()
    
    @staticmethod
    def validate_task_request(request: str) -> bool:
        """Validate task request"""
        if not request or len(request.strip()) == 0:
            return False
        
        if len(request) > 1000:  # Reasonable limit
            return False
        
        # Check for potentially malicious content
        malicious_patterns = [
            r'rm\s+-rf\s+/',
            r'dd\s+if=/dev/',
            r'mkfs',
            r':\(\)\s*\{\s*:\|:\&\s*\};\s*:',  # Fork bomb
            r'>\s*/dev/sd[a-z]',  # Direct disk writing
            r'chmod\s+777\s+/',
            r'passwd\s+\w+',  # Password changes
            r'useradd\s+\w+',  # User creation
            r'groupadd\s+\w+',  # Group creation
            r'sudo\s+rm\s+-rf',  # Sudo destructive commands
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, request, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def assess_command_risk(command: str) -> SecurityLevel:
        """Assess risk level of a command"""
        command_lower = command.lower()
        
        # Critical risk commands
        critical_patterns = [
            r'rm\s+-rf\s+/',
            r'dd\s+if=/dev/',
            r'mkfs',
            r'fdisk',
            r'parted',
            r'sudo\s+rm\s+-rf',
            r'sudo\s+chmod\s+777',
            r'sudo\s+passwd',
            r'sudo\s+useradd',
            r'sudo\s+groupadd',
        ]
        
        for pattern in critical_patterns:
            if re.search(pattern, command_lower):
                return SecurityLevel.CRITICAL
        
        # High risk commands
        high_patterns = [
            r'chmod\s+777',
            r'chown\s+-R',
            r'systemctl\s+(stop|disable)',
            r'service\s+\w+\s+(stop|disable)',
            r'iptables\s+-F',
            r'ufw\s+--force\s+reset',
            r'crontab\s+-r',
            r'passwd\s+\w+',
            r'useradd\s+\w+',
            r'groupadd\s+\w+',
        ]
        
        for pattern in high_patterns:
            if re.search(pattern, command_lower):
                return SecurityLevel.HIGH
        
        # Medium risk commands
        medium_patterns = [
            r'systemctl\s+(start|restart|reload)',
            r'service\s+\w+\s+(start|restart|reload)',
            r'chmod\s+[0-7]{3,4}',
            r'chown\s+\w+:\w+',
            r'crontab\s+-e',
            r'iptables\s+-\w+',
            r'ufw\s+(allow|deny)',
            r'apt\s+(install|remove|purge)',
            r'yum\s+(install|remove)',
            r'dnf\s+(install|remove)',
        ]
        
        for pattern in medium_patterns:
            if re.search(pattern, command_lower):
                return SecurityLevel.MEDIUM
        
        # Default to low risk for read-only or safe commands
        return SecurityLevel.LOW
    
    @staticmethod
    def validate_user_input(text: str, max_length: int = 1000) -> bool:
        """General user input validation"""
        if not text or len(text.strip()) == 0:
            return False
        
        if len(text) > max_length:
            return False
        
        # Check for SQL injection patterns
        sql_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
            r'(--|\#|\/\*|\*\/)',
            r'(\b(script|javascript|vbscript|onload|onerror)\b)',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Sanitize user input"""
        # HTML escape
        text = html.escape(text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID format"""
        if not user_id or len(user_id) < 3 or len(user_id) > 50:
            return False
        
        # Allow alphanumeric, underscore, hyphen
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, user_id))
    
    @staticmethod
    def check_command_whitelist(command: str, whitelist: List[str] = None) -> bool:
        """Check if command is in whitelist (if provided)"""
        if not whitelist:
            return True
        
        command_lower = command.lower().strip()
        return any(allowed_cmd.lower() in command_lower for allowed_cmd in whitelist)
    
    @staticmethod
    def check_command_blacklist(command: str, blacklist: List[str] = None) -> bool:
        """Check if command is in blacklist"""
        if not blacklist:
            return True
        
        command_lower = command.lower().strip()
        return not any(blocked_cmd.lower() in command_lower for blocked_cmd in blacklist)
