#!/usr/bin/env python3
"""
Command Executor for Otium AI Agent - Phase 1 Simplified
Handles command execution and basic safety checks via SSH
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class CommandExecutor:
    """Handles command execution with basic safety checks via SSH"""
    
    def __init__(self, ssh_manager, connection_id):
        if ssh_manager is None:
            raise ValueError("ssh_manager is required")
        if not connection_id:
            raise ValueError("connection_id is required")
        self.ssh_manager = ssh_manager
        self.connection_id = connection_id
        
        # Basic dangerous patterns for Phase 1
        self.dangerous_patterns = [
            # File system destruction
            'rm -rf /',
            'rm -rf /etc',
            'rm -rf /var',
            'rm -rf /usr',
            'rm -rf /boot',
            'rm -rf /home',
            
            # Disk operations
            'dd if=/dev/',
            'mkfs',
            'fdisk',
            'parted',
            
            # Critical service operations
            'systemctl stop sshd',
            'systemctl disable sshd',
            'systemctl stop network',
            'systemctl stop firewalld',
            
            # Network (dangerous)
            'iptables -F',
            'iptables --flush',
            'ip link set down',
            'ifconfig down',
            
            # User management (dangerous)
            'userdel -r root',
            'passwd -d root',
            
            # Process management (dangerous)
            'killall -9',
            'kill -9 1',
        ]
    
    def set_connection_id(self, connection_id: str):
        """Set the SSH connection ID for command execution - DEPRECATED, use constructor"""
        self.connection_id = connection_id
    
    def execute_steps(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a list of command steps"""
        if not hasattr(self, 'connection_id'):
            return {
                "success": False,
                "error": "No SSH connection set",
                "total_steps": len(steps),
                "successful_steps": 0,
                "failed_steps": 0,
                "skipped_steps": 0,
                "step_results": [],
                "total_execution_time": 0
            }
        
        start_time = time.time()
        total_steps = len(steps)
        successful_steps = 0
        failed_steps = 0
        skipped_steps = 0
        step_results = []
        
        print(f"🚀 Executing {total_steps} command steps...")
        
        for i, step in enumerate(steps, 1):
            step_num = step.get('step', i)
            command = step.get('command', '')
            description = step.get('description', 'No description')
            
            print(f"📝 Step {step_num}: {description}")
            print(f"   Command: {command}")
            
            # Basic safety check
            if self._is_dangerous_command(command):
                print(f"⚠️  Skipping dangerous command: {command}")
                step_results.append({
                    'step': step_num,
                    'command': command,
                    'status': 'skipped',
                    'reason': 'Dangerous command detected',
                    'execution_time': 0
                })
                skipped_steps += 1
                continue
            
            # Execute command
            try:
                step_start_time = time.time()
                result = self.ssh_manager.execute_command(self.connection_id, command)
                step_execution_time = time.time() - step_start_time
                
                if result['success']:
                    print(f"✅ Step {step_num} completed successfully")
                    successful_steps += 1
                    status = 'success'
                else:
                    print(f"❌ Step {step_num} failed: {result.get('error', 'Unknown error')}")
                    failed_steps += 1
                    status = 'failed'
                
                step_results.append({
                    'step': step_num,
                    'command': command,
                    'status': status,
                    'stdout': result.get('stdout', ''),
                    'stderr': result.get('stderr', ''),
                    'exit_code': result.get('exit_code', -1),
                    'execution_time': step_execution_time
                })
                
            except Exception as e:
                print(f"❌ Step {step_num} error: {str(e)}")
                failed_steps += 1
                step_results.append({
                    'step': step_num,
                    'command': command,
                    'status': 'error',
                    'error': str(e),
                    'execution_time': 0
                })
        
        total_execution_time = time.time() - start_time
        
        print(f"\n📊 Execution Summary:")
        print(f"   Total Steps: {total_steps}")
        print(f"   Successful: {successful_steps}")
        print(f"   Failed: {failed_steps}")
        print(f"   Skipped: {skipped_steps}")
        print(f"   Total Time: {total_execution_time:.2f}s")
        
        return {
            "success": successful_steps == total_steps,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "skipped_steps": skipped_steps,
            "step_results": step_results,
            "total_execution_time": total_execution_time
        }
    
    def execute_single_step(self, step: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """Execute a single command step"""
        if not hasattr(self, 'connection_id'):
            return {
                "success": False,
                "error": "No SSH connection set"
            }
        
        command = step.get('command', '')
        description = step.get('explanation', 'No description')
        
        print(f"📝 Executing Step {step_index}: {description}")
        print(f"   Command: {command}")
        
        # Basic safety check
        if self._is_dangerous_command(command):
            print(f"⚠️  Dangerous command detected: {command}")
            return {
                'success': False,
                'status': 'skipped',
                'reason': 'Dangerous command detected',
                'command': command,
                'output': '',
                'error': 'Command blocked for safety reasons'
            }
        
        # Execute command
        try:
            step_start_time = time.time()
            result = self.ssh_manager.execute_command(self.connection_id, command)
            step_execution_time = time.time() - step_start_time
            
            if result['success']:
                print(f"✅ Step {step_index} completed successfully")
                return {
                    'success': True,
                    'status': 'success',
                    'command': command,
                    'output': result.get('stdout', ''),
                    'stderr': result.get('stderr', ''),
                    'exit_code': result.get('exit_code', 0),
                    'execution_time': step_execution_time
                }
            else:
                print(f"❌ Step {step_index} failed: {result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'status': 'failed',
                    'command': command,
                    'output': result.get('stdout', ''),
                    'error': result.get('error', 'Unknown error'),
                    'stderr': result.get('stderr', ''),
                    'exit_code': result.get('exit_code', -1),
                    'execution_time': step_execution_time
                }
                
        except Exception as e:
            print(f"❌ Step {step_index} error: {str(e)}")
            return {
                'success': False,
                'status': 'error',
                'command': command,
                'output': '',
                'error': str(e),
                'execution_time': 0
            }
    
    def execute_single_command(self, command: str) -> Dict[str, Any]:
        """Execute a single command"""
        if not hasattr(self, 'connection_id'):
            return {
                "success": False,
                "error": "No SSH connection set"
            }
        
        try:
            result = self.ssh_manager.execute_command(self.connection_id, command)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def _is_dangerous_command(self, command: str) -> bool:
        """Check if command contains dangerous patterns"""
        command_lower = command.lower()
        
        for pattern in self.dangerous_patterns:
            if pattern.lower() in command_lower:
                return True
        
        return False