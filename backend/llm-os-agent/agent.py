#!/usr/bin/env python3
"""
Ping AI Agent - Simplified Phase 1
SSH-based Linux system administration AI agent with core functionality only
"""

import os
import sys
from typing import Dict, Any

# Import our modules
from command_generator import CommandGenerator
from command_executor import CommandExecutor
from ssh_system_detector import SSHSystemDetector


class Agent:
    """Simplified AI Agent for SSH-based Linux system administration"""
    
    def __init__(self, api_key: str, ssh_manager, connection_id: str):
        # Validate required parameters
        if not api_key:
            raise ValueError("Anthropic API key is required")
        if not ssh_manager:
            raise ValueError("SSH manager is required")
        if not connection_id:
            raise ValueError("SSH connection ID is required")
        
        self.api_key = api_key
        self.ssh_manager = ssh_manager
        self.connection_id = connection_id
        
        # Initialize components
        self.system_detector = None
        self.command_executor = None
        self.command_generator = None
        self.system_context = {}
    
    def start(self) -> bool:
        """Start the agent and initialize environment"""
        print("🚀 Starting Ping AI Agent...")
        print("🔌 Starting in SSH mode...")
        
        try:
            # Validate SSH connection
            if not self.ssh_manager.is_connection_alive(self.connection_id):
                print("❌ SSH connection not available or not alive")
                return False
            
            print("✅ SSH connection validated")
            
            # Initialize command executor
            print("🔧 Initializing command executor...")
            self.command_executor = CommandExecutor(ssh_manager=self.ssh_manager, connection_id=self.connection_id)
            self.command_executor.set_connection_id(self.connection_id)
            print("✅ Command executor initialized")
            
            # Initialize system detector
            print("🔍 Initializing system detector...")
            self.system_detector = SSHSystemDetector(self.ssh_manager, self.connection_id)
            print("✅ System detector created")
            
            # Detect system
            print("🔍 Detecting system...")
            self.system_context = self.system_detector.detect_system()
            print(f"✅ System detection complete: {len(self.system_context)} items")
            
            # Initialize command generator
            print("🤖 Initializing command generator...")
            self.command_generator = CommandGenerator(
                self.system_context, 
                api_key=self.api_key
            )
            print("✅ Command generator initialized")
            
            print("✅ Ping Agent initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start agent: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_request(self, user_request: str) -> Dict[str, Any]:
        """Process a user request and execute commands"""
        print(f"\n{'='*60}")
        print(f"📝 Processing Request: {user_request}")
        print(f"{'='*60}")
        
        try:
            # Generate commands based on system context
            print("🤖 Generating commands...")
            command_plan = self.command_generator.generate_commands(user_request)
            
            if not command_plan or 'steps' not in command_plan:
                raise ValueError("Failed to generate command plan")
            
            # Basic safety check
            if self._is_dangerous_operation(command_plan):
                print("🚨 DANGEROUS OPERATION DETECTED")
                print("This operation requires explicit approval.")
                return {
                    "success": False,
                    "error": "Dangerous operation requires approval",
                    "command_plan": command_plan,
                    "requires_approval": True
                }
            
            # Print plan
            self._print_command_plan(command_plan)
            
            # Execute commands
            execution_results = self._execute_commands(command_plan)
            
            return {
                "success": execution_results["successful_steps"] == execution_results["total_steps"],
                "command_plan": command_plan,
                "execution_results": execution_results,
                "system_context": self.system_context
            }
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_dangerous_operation(self, command_plan: Dict[str, Any]) -> bool:
        """Basic safety check for dangerous operations"""
        dangerous_patterns = [
            'rm -rf /',
            'rm -rf /etc',
            'rm -rf /var',
            'rm -rf /usr',
            'rm -rf /boot',
            'dd if=/dev/',
            'mkfs',
            'fdisk',
            'systemctl stop sshd',
            'systemctl disable sshd',
            'iptables -F',
            'firewall-cmd --reload'
        ]
        
        steps = command_plan.get('steps', [])
        for step in steps:
            command = step.get('command', '').lower()
            for pattern in dangerous_patterns:
                if pattern in command:
                    print(f"⚠️  Dangerous pattern detected: {pattern}")
                    return True
        
        return False
    
    def _print_command_plan(self, command_plan: Dict[str, Any]) -> None:
        """Print command plan information"""
        print(f"\n📋 Command Plan:")
        print(f"   Intent: {command_plan.get('intent', 'Unknown')}")
        print(f"   Action: {command_plan.get('action', 'Unknown')}")
        print(f"   Risk Level: {command_plan.get('risk_level', 'Unknown')}")
        print(f"   Explanation: {command_plan.get('explanation', 'No explanation')}")
        print(f"   Steps: {len(command_plan.get('steps', []))}")
        
        # Print individual steps
        for i, step in enumerate(command_plan.get('steps', []), 1):
            print(f"   Step {i}: {step.get('command', 'No command')}")
            print(f"      Description: {step.get('description', 'No description')}")
    
    def _execute_commands(self, command_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute commands from command plan"""
        steps = command_plan.get('steps', [])
        if steps:
            return self.command_executor.execute_steps(steps)
        else:
            return {
                "total_steps": 0,
                "successful_steps": 0,
                "failed_steps": 0,
                "skipped_steps": 0,
                "step_results": [],
                "total_execution_time": 0
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        return self.system_context
    
    def cleanup(self):
        """Cleanup resources"""
        if self.ssh_manager and self.connection_id:
            try:
                print("🧹 Cleaning up SSH connection...")
                self.ssh_manager.disconnect(self.connection_id)
                print("✅ SSH connection cleaned up")
            except Exception as e:
                print(f"⚠️  Error cleaning up SSH connection: {e}")


def main():
    """Main entry point"""
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment variables")
    except Exception as e:
        print(f"⚠️  Error loading .env file: {e}")
    
    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ No Anthropic API key found. Set ANTHROPIC_API_KEY environment variable.")
        return 1
    
    print(f"✅ Anthropic API key found: {api_key[:20]}...")
    
    # Note: Agent is now API-only, no interactive mode needed
    print("🤖 Ping Agent designed for API use only")
    print("💡 Use the API endpoints to interact with the agent")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())