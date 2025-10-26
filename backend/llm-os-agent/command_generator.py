#!/usr/bin/env python3
"""
Command Generator for Ping AI Agent - Phase 1 Simplified (OpenAI Only)
Generates appropriate commands based on system context and user requests
"""

import json
import subprocess
import os
from typing import Dict, Any, List, Optional
from openai import OpenAI

# Configuration constants
DEFAULT_TIMEOUT = 5
DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"
DEFAULT_OPENAI_MAX_TOKENS = 1000
DEFAULT_OPENAI_TEMPERATURE = 0.1

# Fast pattern matching keywords
FAST_PATTERNS = {
    'system_info': ['system info', 'system status', 'show system', 'get info'],
    'process_list': ['list process', 'show process', 'ps aux', 'running process'],
    'memory_check': ['memory usage', 'check memory', 'free memory', 'ram usage'],
    'disk_usage': ['disk usage', 'disk space', 'check disk', 'df -h'],
    'network_check': ['network connection', 'netstat', 'listening port', 'network status'],
    'nginx_install': ['install nginx', 'setup nginx', 'nginx proxy', 'nginx server'],
    'apache_install': ['install apache', 'setup apache', 'apache server', 'install httpd', 'setup httpd']
}

# Package name mappings by OS family
PACKAGE_MAPPINGS = {
    'rhel': {
        'apache': 'httpd',
        'apache2': 'httpd',
    },
    'debian': {
        'httpd': 'apache2',
    }
}

# Service name mappings by OS family
SERVICE_MAPPINGS = {
    'rhel': {
        'apache': 'httpd',
        'apache2': 'httpd',
    },
    'debian': {
        'httpd': 'apache2',
    }
}


class CommandGenerator:
    """Generates appropriate commands based on system context - Phase 1 Simplified (OpenAI Only)"""
    
    def __init__(self, system_context: Dict[str, Any], api_key: str = None):
        self.system_context = system_context
        self.api_key = api_key
        
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
    
    def generate_commands(self, user_request: str) -> Dict[str, Any]:
        """Generate commands based on system context and user request"""
        try:
            # Try fast pattern matching first
            fast_response = self._try_fast_pattern_match(user_request)
            if fast_response:
                print("⚡ Using fast pattern matching...")
                return fast_response
            
            # Generate AI-powered response
            return self._generate_ai_response(user_request)
            
        except Exception as e:
            print(f"🔍 Error in generate_commands: {e}")
            return self._create_simple_fallback(user_request)
    
    def _try_fast_pattern_match(self, user_request: str) -> Optional[Dict[str, Any]]:
        """Try to match common patterns quickly without AI"""
        user_lower = user_request.lower()
        
        for pattern_type, patterns in FAST_PATTERNS.items():
            if any(pattern in user_lower for pattern in patterns):
                return self._create_simple_fallback(pattern_type)
        
        return None
    
    def _generate_ai_response(self, user_request: str) -> Dict[str, Any]:
        """Generate AI-powered command response"""
        if not self.openai_client:
            print("⚠️  No OpenAI API key provided, using fallback")
            return self._create_simple_fallback(user_request)
        
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(user_request)
        
        # Call OpenAI API
        print("🤖 Using OpenAI API...")
        response = self._call_openai(user_prompt, system_prompt)
        
        # Parse and validate response
        return self._parse_and_validate_ai_response(response, user_request)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt with system context"""
        os_name = self.system_context.get('os_name', 'Unknown')
        os_version = self.system_context.get('os_version', '')
        os_family = self.system_context.get('os_family', 'unknown')
        package_manager = self.system_context.get('package_manager', 'unknown')
        service_manager = self.system_context.get('service_manager', 'unknown')
        available_tools = self.system_context.get('available_tools', [])
        memory_available = self.system_context.get('memory_available', 'Unknown')
        disk_available = self.system_context.get('disk_available', 'Unknown')
        
        return f"""You are an expert Linux system administrator AI that EXECUTES commands in production environments.

SYSTEM CONTEXT:
- Operating System: {os_name} {os_version} (Family: {os_family})
- Package Manager: {package_manager}
- Service Manager: {service_manager}
- Available Tools: {', '.join(available_tools[:20])} (and {len(available_tools)-20} more)
- Memory Available: {memory_available}
- Disk Space Available: {disk_available}

SAFETY RULES:
- Do NOT run full system upgrades unless explicitly approved
- Always check if a package is already installed before attempting to install
- Always validate configuration files before enabling/restarting services
- Avoid restarting critical services unless necessary
- For file changes, back up the original file before modifying
- Check network connectivity before attempting package installations
- Verify write permissions before attempting file modifications

CRITICAL SERVICE SAFEGUARDS:
- Never restart SSH service (sshd) without explicit user confirmation
- Never stop database services (postgresql, mysql, mariadb) without explicit approval
- Never restart web servers (nginx, apache2, httpd) during peak hours without approval
- Always check service dependencies before stopping any critical service

OUTPUT FORMAT REQUIREMENTS:
- Output must be a single valid JSON object and contain no text outside of it
- Do not include any explanatory text, comments, or markdown formatting
- Ensure all JSON is properly formatted and valid
- Include all required fields in the JSON response

Analyze the user's request and respond with a JSON object containing executable steps:

{{
  "intent": "package_management|service_management|configuration|troubleshooting|general_help",
  "action": "specific action needed",
  "packages": ["list of packages if needed"],
  "services": ["list of services if needed"],
  "risk_level": "low|medium|high",
  "explanation": "brief explanation of what you'll do",
  "steps": [
    {{
      "step": 1,
      "command": "{package_manager} update -y",
      "description": "Update package lists",
      "expected_output": "Package lists updated"
    }}
  ]
}}

This is a PRODUCTION {os_name} system that executes real commands. Keep commands simple and reliable.
Generate commands specifically for this system's package manager ({package_manager}) and service manager ({service_manager}).

REMEMBER: Output must be a single valid JSON object with no text outside of it."""
    
    def _create_user_prompt(self, user_request: str) -> str:
        """Create user prompt with the request"""
        return f"""User Request: {user_request}

Generate appropriate commands for this specific system. Consider the system context and generate commands that will work on this particular Linux distribution."""
    
    def _call_openai(self, user_prompt: str, system_prompt: str) -> str:
        """Call OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model=DEFAULT_OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=DEFAULT_OPENAI_TEMPERATURE,
                max_tokens=DEFAULT_OPENAI_MAX_TOKENS
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling OpenAI: {e}"
    
    def _parse_and_validate_ai_response(self, response: str, user_request: str) -> Dict[str, Any]:
        """Parse AI response and validate commands"""
        try:
            print(f"🔍 AI Response: {response[:200]}...")
            
            # Extract JSON from response
            parsed_response = self._extract_json_from_response(response)
            if not parsed_response:
                return self._create_simple_fallback(user_request)
            
            # Validate and fix commands
            self._validate_and_fix_commands(parsed_response)
            
            return parsed_response
            
        except Exception as e:
            print(f"🔍 Error parsing AI response: {e}")
            return self._create_simple_fallback(user_request)
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from AI response"""
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            print(f"🔍 Found JSON: {json_str[:200]}...")
            return json.loads(json_str)
        return None
    
    def _validate_and_fix_commands(self, parsed_response: Dict[str, Any]) -> None:
        """Validate and fix commands in the response"""
        if 'steps' in parsed_response:
            for step in parsed_response['steps']:
                if 'command' in step:
                    original_cmd = step['command']
                    fixed_cmd = self._fix_command_for_system(original_cmd)
                    if fixed_cmd != original_cmd:
                        print(f"🔧 Fixed command: {original_cmd} -> {fixed_cmd}")
                        step['command'] = fixed_cmd
    
    def _fix_command_for_system(self, command: str) -> str:
        """Fix command to work on this specific system"""
        available_tools = self.system_context.get('available_tools', [])
        package_manager = self.system_context.get('package_manager', 'unknown')
        service_manager = self.system_context.get('service_manager', 'unknown')
        
        # Replace generic package managers with detected one
        command = command.replace('apt-get', package_manager)
        command = command.replace('yum', package_manager)
        command = command.replace('dnf', package_manager)
        command = command.replace('zypper', package_manager)
        
        # Replace generic service managers with detected one
        command = command.replace('systemctl', service_manager)
        command = command.replace('service', service_manager)
        
        # Replace unavailable tools with alternatives
        command = self._replace_unavailable_tools(command, available_tools)
        
        return command
    
    def _replace_unavailable_tools(self, command: str, available_tools: List[str]) -> str:
        """Replace unavailable tools with alternatives"""
        replacements = [
            ('ss -tuln', 'ss', 'netstat -tuln', 'netstat', 'cat /proc/net/tcp'),
            ('lscpu', 'lscpu', 'cat /proc/cpuinfo', None, None),
            ('free -h', 'free', 'cat /proc/meminfo', None, None)
        ]
        
        for original, tool, alt1, alt1_tool, alt2 in replacements:
            if original in command and tool not in available_tools:
                if alt1_tool and alt1_tool in available_tools:
                    command = command.replace(original, alt1)
                elif alt2:
                    command = command.replace(original, alt2)
        
        return command
    
    def _create_simple_fallback(self, user_request: str) -> Dict[str, Any]:
        """Create simple fallback response when AI fails"""
        user_lower = user_request.lower()
        package_manager = self.system_context.get('package_manager', 'apt-get')
        service_manager = self.system_context.get('service_manager', 'systemctl')
        available_tools = self.system_context.get('available_tools', [])
        os_family = self.system_context.get('os_family', 'unknown')
        
        # Simple pattern matching for common requests
        if any(word in user_lower for word in ['nginx', 'proxy', 'install', 'setup']):
            return self._create_nginx_fallback(package_manager, service_manager)
        elif any(word in user_lower for word in ['apache', 'httpd', 'install', 'setup']):
            return self._create_apache_fallback(package_manager, service_manager, os_family)
        elif any(word in user_lower for word in ['process', 'ps']):
            return self._create_process_fallback()
        elif any(word in user_lower for word in ['disk', 'space', 'df']):
            return self._create_disk_fallback()
        elif any(word in user_lower for word in ['memory', 'ram', 'free']):
            return self._create_memory_fallback()
        elif any(word in user_lower for word in ['network', 'netstat', 'connection']):
            return self._create_network_fallback(available_tools)
        elif any(word in user_lower for word in ['system', 'info']):
            return self._create_system_info_fallback(available_tools)
        else:
            return self._create_default_fallback(user_request)
    
    def _create_nginx_fallback(self, package_manager: str, service_manager: str) -> Dict[str, Any]:
        """Create nginx installation fallback"""
        return {
            "intent": "service_management",
            "action": "install_and_configure_nginx_proxy",
            "packages": ["nginx"],
            "services": ["nginx"],
            "risk_level": "low",
            "explanation": "Install nginx and configure as proxy",
            "steps": [
                self._create_step(1, f"{package_manager} update -y", "Update package lists", "Package lists updated"),
                self._create_step(2, f"{package_manager} install -y nginx", "Install nginx package", "Nginx installed successfully"),
                self._create_step(3, f"{service_manager} start nginx", "Start nginx service", "Nginx service started"),
                self._create_step(4, f"{service_manager} enable nginx", "Enable nginx service", "Nginx service enabled")
            ]
        }
    
    def _create_apache_fallback(self, package_manager: str, service_manager: str, os_family: str) -> Dict[str, Any]:
        """Create apache installation fallback"""
        apache_pkg = self._get_package_name('apache', os_family)
        apache_svc = self._get_service_name('apache', os_family)
        
        return {
            "intent": "service_management",
            "action": "install_and_configure_apache",
            "packages": [apache_pkg],
            "services": [apache_svc],
            "risk_level": "low",
            "explanation": f"Install and configure Apache web server ({apache_pkg})",
            "steps": [
                self._create_step(1, f"{package_manager} update -y", "Update package lists", "Package lists updated"),
                self._create_step(2, f"{package_manager} install -y {apache_pkg}", f"Install Apache package ({apache_pkg})", "Apache installed successfully"),
                self._create_step(3, f"{service_manager} start {apache_svc}", f"Start Apache service ({apache_svc})", "Apache service started"),
                self._create_step(4, f"{service_manager} enable {apache_svc}", f"Enable Apache service ({apache_svc})", "Apache service enabled")
            ]
        }
    
    def _create_process_fallback(self) -> Dict[str, Any]:
        """Create process listing fallback"""
        return {
            "intent": "system_monitoring",
            "action": "list_running_processes",
            "packages": [],
            "services": [],
            "risk_level": "low",
            "explanation": "List running processes on the system",
            "steps": [self._create_step(1, "ps aux", "List all running processes", "List of running processes")]
        }
    
    def _create_disk_fallback(self) -> Dict[str, Any]:
        """Create disk usage fallback"""
        return {
            "intent": "system_monitoring",
            "action": "check_disk_usage",
            "packages": [],
            "services": [],
            "risk_level": "low",
            "explanation": "Check disk space usage",
            "steps": [self._create_step(1, "df -h", "Show disk space usage", "Disk space information")]
        }
    
    def _create_memory_fallback(self) -> Dict[str, Any]:
        """Create memory usage fallback"""
        return {
            "intent": "system_monitoring",
            "action": "check_memory_usage",
            "packages": [],
            "services": [],
            "risk_level": "low",
            "explanation": "Check memory usage",
            "steps": [self._create_step(1, "free -h", "Show memory usage", "Memory usage information")]
        }
    
    def _create_network_fallback(self, available_tools: List[str]) -> Dict[str, Any]:
        """Create network check fallback"""
        net_cmd, net_desc = self._get_network_command(available_tools)
        
        return {
            "intent": "system_monitoring",
            "action": "check_network_connections",
            "packages": [],
            "services": [],
            "risk_level": "low",
            "explanation": "Check network connections",
            "steps": [self._create_step(1, net_cmd, net_desc, "Network connection information")]
        }
    
    def _get_network_command(self, available_tools: List[str]) -> tuple:
        """Get appropriate network command based on available tools"""
        if 'ss' in available_tools:
            return "ss -tuln", "Show network connections (using ss)"
        elif 'netstat' in available_tools:
            return "netstat -tuln", "Show network connections (using netstat)"
        else:
            return "cat /proc/net/tcp", "Show network connections (using /proc/net/tcp)"
    
    def _create_system_info_fallback(self, available_tools: List[str]) -> Dict[str, Any]:
        """Create system info fallback"""
        return {
            "intent": "system_monitoring",
            "action": "get_system_information",
            "packages": [],
            "services": [],
            "risk_level": "low",
            "explanation": "Get comprehensive system information",
            "steps": [
                self._create_step(1, "uname -a", "Show kernel information", "Kernel information"),
                self._create_step(2, "cat /etc/os-release", "Show OS release information", "OS release information"),
                self._create_step(3, "cat /proc/cpuinfo" if 'lscpu' not in available_tools else "lscpu", "Show CPU information", "CPU information"),
                self._create_step(4, "cat /proc/meminfo" if 'free' not in available_tools else "free -h", "Show memory usage", "Memory information"),
                self._create_step(5, "cat /proc/mounts" if 'df' not in available_tools else "df -h", "Show disk usage", "Disk information")
            ]
        }
    
    def _create_default_fallback(self, user_request: str) -> Dict[str, Any]:
        """Create default fallback response"""
        return {
            "intent": "general_help",
            "action": "unknown_request",
            "packages": [],
            "services": [],
            "risk_level": "low",
            "explanation": "Unknown request - please provide more details",
            "steps": [self._create_step(1, "echo 'Request not understood'", "Unknown request", "Please provide a clearer request")]
        }
    
    def _create_step(self, step_num: int, command: str, description: str, expected_output: str) -> Dict[str, Any]:
        """Create a standardized command step"""
        return {
            "step": step_num,
            "command": command,
            "description": description,
            "expected_output": expected_output
        }
    
    def _get_package_name(self, generic_name: str, os_family: str) -> str:
        """Get OS-specific package name"""
        return PACKAGE_MAPPINGS.get(os_family, {}).get(generic_name, generic_name)
    
    def _get_service_name(self, generic_name: str, os_family: str) -> str:
        """Get OS-specific service name"""
        return SERVICE_MAPPINGS.get(os_family, {}).get(generic_name, generic_name)


if __name__ == "__main__":
    # Test the command generator
    test_context = {
        "os_name": "Red Hat Enterprise Linux",
        "os_version": "8.4",
        "package_manager": "dnf",
        "service_manager": "systemctl",
        "available_tools": ["curl", "wget", "git", "vim"],
        "memory_available": "2GB",
        "disk_available": "10GB"
    }
    
    generator = CommandGenerator(test_context, api_key="test")
    result = generator.generate_commands("Install nginx and configure as proxy")
    print(json.dumps(result, indent=2))