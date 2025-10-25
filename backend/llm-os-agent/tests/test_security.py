#!/usr/bin/env python3
"""
Unit tests for security validation and sanitization
"""

import pytest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security import SecurityValidator, SecurityLevel

def test_validate_hostname():
    """Test hostname validation"""
    # Valid hostnames
    assert SecurityValidator.validate_hostname("example.com") == True
    assert SecurityValidator.validate_hostname("server1.example.com") == True
    assert SecurityValidator.validate_hostname("192.168.1.1") == True
    assert SecurityValidator.validate_hostname("localhost") == True
    
    # Invalid hostnames
    assert SecurityValidator.validate_hostname("") == False
    assert SecurityValidator.validate_hostname("a" * 256) == False  # Too long
    assert SecurityValidator.validate_hostname(".example.com") == False  # Starts with dot
    assert SecurityValidator.validate_hostname("example.com.") == False  # Ends with dot

def test_validate_port():
    """Test port validation"""
    # Valid ports
    assert SecurityValidator.validate_port(22) == True
    assert SecurityValidator.validate_port(80) == True
    assert SecurityValidator.validate_port(443) == True
    assert SecurityValidator.validate_port(65535) == True
    assert SecurityValidator.validate_port(1) == True
    
    # Invalid ports
    assert SecurityValidator.validate_port(0) == False
    assert SecurityValidator.validate_port(-1) == False
    assert SecurityValidator.validate_port(65536) == False

def test_sanitize_command():
    """Test command sanitization"""
    # Test dangerous characters removal
    command = "ls -la; rm -rf /"
    sanitized = SecurityValidator.sanitize_command(command)
    assert ";" not in sanitized
    assert "rm -rf /" not in sanitized
    
    # Test HTML escaping
    command = "<script>alert('xss')</script>"
    sanitized = SecurityValidator.sanitize_command(command)
    assert "<" not in sanitized
    assert ">" not in sanitized

def test_validate_task_request():
    """Test task request validation"""
    # Valid requests
    assert SecurityValidator.validate_task_request("Check system status") == True
    assert SecurityValidator.validate_task_request("List files in directory") == True
    assert SecurityValidator.validate_task_request("Install nginx") == True
    
    # Invalid requests
    assert SecurityValidator.validate_task_request("") == False
    assert SecurityValidator.validate_task_request("   ") == False
    assert SecurityValidator.validate_task_request("a" * 1001) == False  # Too long
    
    # Malicious requests
    assert SecurityValidator.validate_task_request("rm -rf /") == False
    assert SecurityValidator.validate_task_request("dd if=/dev/zero of=/dev/sda") == False
    assert SecurityValidator.validate_task_request(":(){ :|:& };:") == False  # Fork bomb

def test_assess_command_risk():
    """Test command risk assessment"""
    # Low risk commands
    assert SecurityValidator.assess_command_risk("ls -la") == SecurityLevel.LOW
    assert SecurityValidator.assess_command_risk("pwd") == SecurityLevel.LOW
    assert SecurityValidator.assess_command_risk("whoami") == SecurityLevel.LOW
    assert SecurityValidator.assess_command_risk("df -h") == SecurityLevel.LOW
    
    # Medium risk commands
    assert SecurityValidator.assess_command_risk("systemctl start nginx") == SecurityLevel.MEDIUM
    assert SecurityValidator.assess_command_risk("chmod 755 file.txt") == SecurityLevel.MEDIUM
    assert SecurityValidator.assess_command_risk("apt install package") == SecurityLevel.MEDIUM
    
    # High risk commands
    assert SecurityValidator.assess_command_risk("systemctl stop nginx") == SecurityLevel.HIGH
    assert SecurityValidator.assess_command_risk("chmod 777 /") == SecurityLevel.HIGH
    assert SecurityValidator.assess_command_risk("useradd newuser") == SecurityLevel.HIGH
    
    # Critical risk commands
    assert SecurityValidator.assess_command_risk("rm -rf /") == SecurityLevel.CRITICAL
    assert SecurityValidator.assess_command_risk("dd if=/dev/zero of=/dev/sda") == SecurityLevel.CRITICAL
    assert SecurityValidator.assess_command_risk("sudo rm -rf /") == SecurityLevel.CRITICAL

def test_validate_user_input():
    """Test general user input validation"""
    # Valid inputs
    assert SecurityValidator.validate_user_input("Hello world") == True
    assert SecurityValidator.validate_user_input("Check system status") == True
    
    # Invalid inputs
    assert SecurityValidator.validate_user_input("") == False
    assert SecurityValidator.validate_user_input("a" * 1001) == False  # Too long
    
    # SQL injection attempts
    assert SecurityValidator.validate_user_input("'; DROP TABLE users; --") == False
    assert SecurityValidator.validate_user_input("1 OR 1=1") == False
    assert SecurityValidator.validate_user_input("SELECT * FROM users") == False

def test_validate_email():
    """Test email validation"""
    # Valid emails
    assert SecurityValidator.validate_email("test@example.com") == True
    assert SecurityValidator.validate_email("user.name@domain.co.uk") == True
    assert SecurityValidator.validate_email("admin@company.org") == True
    
    # Invalid emails
    assert SecurityValidator.validate_email("") == False
    assert SecurityValidator.validate_email("invalid-email") == False
    assert SecurityValidator.validate_email("@example.com") == False
    assert SecurityValidator.validate_email("test@") == False

def test_validate_user_id():
    """Test user ID validation"""
    # Valid user IDs
    assert SecurityValidator.validate_user_id("user123") == True
    assert SecurityValidator.validate_user_id("admin_user") == True
    assert SecurityValidator.validate_user_id("user-123") == True
    
    # Invalid user IDs
    assert SecurityValidator.validate_user_id("") == False
    assert SecurityValidator.validate_user_id("ab") == False  # Too short
    assert SecurityValidator.validate_user_id("a" * 51) == False  # Too long
    assert SecurityValidator.validate_user_id("user@123") == False  # Invalid character

def test_check_command_whitelist():
    """Test command whitelist checking"""
    whitelist = ["ls", "pwd", "whoami", "df"]
    
    # Allowed commands
    assert SecurityValidator.check_command_whitelist("ls -la", whitelist) == True
    assert SecurityValidator.check_command_whitelist("pwd", whitelist) == True
    
    # Not allowed commands
    assert SecurityValidator.check_command_whitelist("rm -rf /", whitelist) == False
    assert SecurityValidator.check_command_whitelist("unknown_command", whitelist) == False

def test_check_command_blacklist():
    """Test command blacklist checking"""
    blacklist = ["rm", "dd", "mkfs", "fdisk"]
    
    # Safe commands
    assert SecurityValidator.check_command_blacklist("ls -la", blacklist) == True
    assert SecurityValidator.check_command_blacklist("pwd", blacklist) == True
    
    # Blocked commands
    assert SecurityValidator.check_command_blacklist("rm -rf /", blacklist) == False
    assert SecurityValidator.check_command_blacklist("dd if=/dev/zero", blacklist) == False

if __name__ == "__main__":
    pytest.main([__file__])
