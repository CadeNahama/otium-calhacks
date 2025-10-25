#!/usr/bin/env python3
"""
Minimal SSH Manager for Otium AI Agent
Stores SSH connections for the agent to use
"""

import paramiko
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Configuration constants
DEFAULT_SSH_PORT = 22
DEFAULT_CONNECTION_TIMEOUT = 10
DEFAULT_COMMAND_TIMEOUT = 300
DEFAULT_PING_TIMEOUT = 5
DEFAULT_CONNECTION_TEST_COMMAND = 'echo "Connection test"'
DEFAULT_PING_COMMAND = 'echo "ping"'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSHConnectionError(Exception):
    """Custom exception for SSH connection errors"""
    pass


class SSHCommandError(Exception):
    """Custom exception for SSH command execution errors"""
    pass


class SSHManager:
    """Minimal SSH connection manager for the agent"""
    
    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}
        
    def connect_and_store(self, hostname: str, username: str, password: str, port: int = DEFAULT_SSH_PORT) -> Dict[str, Any]:
        """Connect to SSH server and store the connection"""
        try:
            logger.info(f"🔌 Connecting to {username}@{hostname}:{port}")
            
            # Create SSH client
            ssh_client = self._create_ssh_client()
            
            # Connect using password
            self._establish_connection(ssh_client, hostname, port, username, password)
            
            # Test connection
            self._test_connection(ssh_client)
            
            # Generate connection ID and store
            connection_id = str(uuid.uuid4())
            self._store_connection(connection_id, ssh_client, hostname, username, port)
            
            logger.info(f"✅ SSH connection stored: {connection_id}")
            
            return {
                'success': True,
                'connection_id': connection_id,
                'hostname': hostname,
                'username': username,
                'port': port
            }
            
        except paramiko.AuthenticationException:
            error_msg = "Authentication failed. Please check your credentials."
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except paramiko.SSHException as e:
            error_msg = f"SSH error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def _create_ssh_client(self) -> paramiko.SSHClient:
        """Create and configure SSH client"""
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return ssh_client
    
    def _establish_connection(self, ssh_client: paramiko.SSHClient, hostname: str, 
                            port: int, username: str, password: str) -> None:
        """Establish SSH connection with enhanced error handling"""
        ssh_client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            timeout=DEFAULT_CONNECTION_TIMEOUT,
            allow_agent=False,
            look_for_keys=False,
            banner_timeout=30,
            auth_timeout=30
        )
    
    def _test_connection(self, ssh_client: paramiko.SSHClient) -> None:
        """Test SSH connection with a simple command"""
        stdin, stdout, stderr = ssh_client.exec_command(DEFAULT_CONNECTION_TEST_COMMAND, timeout=DEFAULT_PING_TIMEOUT)
        if stdout.channel.recv_exit_status() != 0:
            ssh_client.close()
            raise SSHConnectionError('Connection test failed')
    
    def _store_connection(self, connection_id: str, ssh_client: paramiko.SSHClient, 
                         hostname: str, username: str, port: int) -> None:
        """Store SSH connection in memory"""
        self.connections[connection_id] = {
            'ssh_client': ssh_client,
            'hostname': hostname,
            'username': username,
            'port': port,
            'connected_at': datetime.now().isoformat(),
            'status': 'connected'
        }
    
    def execute_command(self, connection_id: str, command: str) -> Dict[str, Any]:
        """Execute a command on the stored SSH connection"""
        if connection_id not in self.connections:
            raise SSHConnectionError('Connection not found')
        
        connection = self.connections[connection_id]
        ssh_client = connection['ssh_client']
        
        try:
            logger.info(f"🚀 Executing command on {connection_id}: {command}")
            
            # Execute command
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=DEFAULT_COMMAND_TIMEOUT)
            
            # Get output
            stdout_content = stdout.read().decode('utf-8', errors='ignore')
            stderr_content = stderr.read().decode('utf-8', errors='ignore')
            exit_code = stdout.channel.recv_exit_status()
            
            result = {
                'success': exit_code == 0,
                'command': command,
                'exit_code': exit_code,
                'stdout': stdout_content,
                'stderr': stderr_content,
                'executed_at': datetime.now().isoformat()
            }
            
            if exit_code == 0:
                logger.info(f"✅ Command executed successfully: {command}")
            else:
                logger.warning(f"⚠️ Command failed with exit code {exit_code}: {command}")
            
            return result
            
        except Exception as e:
            error_msg = f"Command execution failed: {e}"
            logger.error(f"❌ {error_msg}")
            raise SSHCommandError(error_msg)
    
    def disconnect(self, connection_id: str) -> bool:
        """Close and remove SSH connection"""
        if connection_id not in self.connections:
            return False
        
        try:
            connection = self.connections[connection_id]
            connection['ssh_client'].close()
            
            # Remove connection
            del self.connections[connection_id]
            
            logger.info(f"🔌 Disconnected from {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error disconnecting from {connection_id}: {e}")
            return False
    
    def is_connection_alive(self, connection_id: str) -> bool:
        """Check if SSH connection is still alive"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        try:
            # Try to execute a simple command to test connection
            stdin, stdout, stderr = connection['ssh_client'].exec_command(DEFAULT_PING_COMMAND, timeout=DEFAULT_PING_TIMEOUT)
            exit_code = stdout.channel.recv_exit_status()
            return exit_code == 0
        except Exception:
            return False
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection"""
        if connection_id not in self.connections:
            return None
        
        connection = self.connections[connection_id].copy()
        
        # Don't expose the SSH client object
        if 'ssh_client' in connection:
            del connection['ssh_client']
        
        return connection
    
    def list_connections(self) -> Dict[str, Dict[str, Any]]:
        """List all active connections"""
        connections_info = {}
        
        for conn_id, connection in self.connections.items():
            connections_info[conn_id] = self.get_connection_info(conn_id)
        
        return connections_info
    
    def cleanup_dead_connections(self) -> int:
        """Remove dead connections and return count of cleaned connections"""
        dead_connections = []
        
        for conn_id in list(self.connections.keys()):
            if not self.is_connection_alive(conn_id):
                dead_connections.append(conn_id)
        
        for conn_id in dead_connections:
            self.disconnect(conn_id)
        
        return len(dead_connections)
    
    def __del__(self):
        """Cleanup all connections when object is destroyed"""
        for connection_id in list(self.connections.keys()):
            self.disconnect(connection_id)
