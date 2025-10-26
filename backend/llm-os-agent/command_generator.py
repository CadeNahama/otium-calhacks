#!/usr/bin/env python3
"""
Command Generator for Ping AI Agent - Using Anthropic Claude
Generates appropriate commands based on system context and user requests
"""

import json
import subprocess
import os
from typing import Dict, Any, List, Optional
from anthropic import Anthropic

# Configuration constants
DEFAULT_TIMEOUT = 5
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5 - Latest and most capable
DEFAULT_CLAUDE_MAX_TOKENS = 2000  # Increased for comprehensive DevOps responses
DEFAULT_CLAUDE_TEMPERATURE = 0.1  # Low temperature for consistent, reliable commands

# Fast pattern matching REMOVED - All requests now go to Claude Sonnet 4.5
# This ensures consistent, high-quality, context-aware command generation
# No more bypasses or incomplete responses

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
    """Generates appropriate commands based on system context using Anthropic Claude"""
    
    def __init__(self, system_context: Dict[str, Any], api_key: str = None):
        self.system_context = system_context
        self.api_key = api_key
        
        if api_key:
            self.anthropic_client = Anthropic(api_key=api_key)
        else:
            self.anthropic_client = None
    
    def generate_commands(self, user_request: str) -> Dict[str, Any]:
        """Generate commands using Claude Sonnet 4.5 with optimized context-aware prompts"""
        try:
            # Always use Claude for comprehensive, context-aware command generation
            print("🤖 Using Claude Sonnet 4.5 with optimized prompts...")
            return self._generate_ai_response(user_request)
            
        except Exception as e:
            print(f"❌ Error in generate_commands: {e}")
            # Only use fallback if Claude completely fails
            return self._create_error_fallback(user_request, str(e))
    
    def _create_error_fallback(self, user_request: str, error_msg: str) -> Dict[str, Any]:
        """Create fallback response only when Claude completely fails"""
        return {
            "intent": "error",
            "action": "api_failure",
            "packages": [],
            "services": [],
            "risk_level": "low",
            "explanation": f"Failed to generate commands using Claude API: {error_msg}. Please check your API key and try again.",
            "steps": [
                {
                    "step": 1,
                    "command": "echo 'Error: Could not generate commands. Please try again.'",
                    "description": "API Error - Claude Sonnet 4.5 could not be reached",
                    "expected_output": "Error message"
                }
            ]
        }
    
    def _generate_ai_response(self, user_request: str) -> Dict[str, Any]:
        """Generate AI-powered command response using Claude Sonnet 4.5"""
        if not self.anthropic_client:
            error_msg = "Anthropic API client not initialized. Please check ANTHROPIC_API_KEY."
            print(f"⚠️  {error_msg}")
            return self._create_error_fallback(user_request, error_msg)
        
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(user_request)
        
        # Call Anthropic Claude API
        print("🤖 Using Anthropic Claude API...")
        response = self._call_claude(user_prompt, system_prompt)
        
        # Parse and validate response
        return self._parse_and_validate_ai_response(response, user_request)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt optimized for Claude Sonnet - with enhanced context awareness"""
        os_name = self.system_context.get('os_name', 'Unknown')
        os_version = self.system_context.get('os_version', '')
        os_family = self.system_context.get('os_family', 'unknown')
        package_manager = self.system_context.get('package_manager', 'unknown')
        service_manager = self.system_context.get('service_manager', 'unknown')
        available_tools = self.system_context.get('available_tools', [])
        memory_available = self.system_context.get('memory_available', 'Unknown')
        disk_available = self.system_context.get('disk_available', 'Unknown')
        
        # Get more detailed system info if available
        cpu_info = self.system_context.get('cpu_info', 'Unknown')
        architecture = self.system_context.get('architecture', 'Unknown')
        kernel_version = self.system_context.get('kernel_version', 'Unknown')
        
        return f"""You are Claude, an expert DevOps engineer and Linux system administrator AI assistant that generates production-ready commands for real server environments.

═══════════════════════════════════════════════════════════════
CRITICAL CONTEXT: PRODUCTION ENVIRONMENT
═══════════════════════════════════════════════════════════════
You are generating commands that will be EXECUTED IMMEDIATELY on a LIVE PRODUCTION server.
Every command you generate will run with root privileges. Exercise extreme caution.

═══════════════════════════════════════════════════════════════
SYSTEM SPECIFICATIONS
═══════════════════════════════════════════════════════════════
Operating System:
  • Distribution: {os_name} {os_version}
  • OS Family: {os_family}
  • Architecture: {architecture}
  • Kernel: {kernel_version}

System Resources:
  • Memory Available: {memory_available}
  • Disk Space: {disk_available}
  • CPU: {cpu_info}

Package & Service Management:
  • Package Manager: {package_manager}
  • Service Manager: {service_manager}
  • Available CLI Tools: {', '.join(available_tools[:25])}{'...' if len(available_tools) > 25 else ''}

═══════════════════════════════════════════════════════════════
YOUR ROLE & RESPONSIBILITIES
═══════════════════════════════════════════════════════════════
As an expert DevOps engineer, you must:

1. ANALYZE the request in context of this SPECIFIC system
   • Consider the OS family ({os_family}) for command syntax
   • Use ONLY {package_manager} for package management
   • Use ONLY {service_manager} for service control
   • Verify tools are in the available_tools list before using them

2. GENERATE context-aware, idempotent commands
   • Commands should work on {os_name} {os_version} specifically
   • Use appropriate flags for this package manager
   • Handle different scenarios (package already installed, service already running)
   • Provide clear error handling

3. ASSESS risk levels accurately
   • low: Read-only operations, safe checks, system info queries
   • medium: Package installations, config changes with backups, non-critical restarts
   • high: System-wide changes, critical service restarts, data operations

4. PROVIDE clear explanations
   • Explain WHY each step is necessary
   • Describe expected outcomes
   • Warn about potential impacts

═══════════════════════════════════════════════════════════════
SAFETY & SECURITY PROTOCOLS
═══════════════════════════════════════════════════════════════

CRITICAL SERVICES - NEVER touch without explicit approval:
  ✗ SSH/SSHD - Could lock out access
  ✗ Database services (postgresql, mysql, mariadb) - Data loss risk
  ✗ Firewall rules - Could break connectivity
  ✗ Core networking (NetworkManager, systemd-networkd) - Connection loss
  ✗ Authentication services (LDAP, Active Directory) - Access issues

MANDATORY SAFETY CHECKS:
  ✓ Check if package is already installed before installing
  ✓ Verify service status before attempting restart
  ✓ Create backups before modifying configuration files
  ✓ Use --dry-run or equivalent when available
  ✓ Check available disk space before installations
  ✓ Verify network connectivity before package updates
  ✓ Test configuration syntax before applying (nginx -t, apache2ctl configtest)
  ✓ Use appropriate flags: -y for non-interactive, --no-install-recommends when possible

FORBIDDEN OPERATIONS (mark as high risk and require explicit approval):
  ✗ rm -rf on system directories (/etc, /var, /usr, /boot, /)
  ✗ Full system upgrades (dist-upgrade, do-release-upgrade)
  ✗ Kernel modifications or replacements
  ✗ Stopping/disabling firewall without explicit request
  ✗ Modifying /etc/fstab, /etc/hosts, /etc/resolv.conf without clear need
  ✗ chmod/chown on system directories
  ✗ Package manager repository changes without approval

BEST PRACTICES for {os_family}:
  • For Debian/Ubuntu: Use apt-get (more stable than apt in scripts)
  • For RHEL/CentOS: Use yum or dnf based on version
  • For Arch: Use pacman with appropriate flags
  • Always include -y or equivalent for non-interactive execution
  • Use full paths for critical commands when possible
  • Implement error checking (command chaining with &&)

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT - STRICT JSON ONLY
═══════════════════════════════════════════════════════════════
CRITICAL: Your response must be ONLY a valid JSON object. No markdown, no explanations outside JSON.

Required JSON structure:
{{
  "intent": "package_management|service_management|configuration|troubleshooting|monitoring|security|general_help",
  "action": "clear, concise description of the action",
  "packages": ["package1", "package2"],  // Empty array if none
  "services": ["service1", "service2"],  // Empty array if none
  "risk_level": "low|medium|high",
  "explanation": "Detailed explanation considering the specific system context and why these steps are appropriate for {os_name}",
  "steps": [
    {{
      "step": 1,
      "command": "actual command using {package_manager} or {service_manager}",
      "description": "What this command does and why",
      "expected_output": "What success looks like"
    }}
  ]
}}

EXAMPLE for {os_family} system:
If user asks "install nginx", you should consider:
- Is nginx package name correct for {os_name}? 
- Does it require additional dependencies on this OS?
- Should we enable it to start on boot?
- Are there port conflicts to check?
- Is firewall configuration needed?

═══════════════════════════════════════════════════════════════
DECISION-MAKING FRAMEWORK
═══════════════════════════════════════════════════════════════
When generating commands, think through:

1. REQUEST ANALYSIS
   → What is the user actually trying to accomplish?
   → Are there implicit requirements? (e.g., "install web server" implies starting it)
   → What's the current state likely to be?

2. SYSTEM-SPECIFIC ADAPTATION
   → Which {os_family} commands work on this {os_name} version?
   → Are there version-specific considerations?
   → What tools from available_tools should I use?

3. SAFETY ASSESSMENT
   → What could go wrong with this operation?
   → What's the blast radius if something fails?
   → Are there dependencies or side effects?

4. COMMAND OPTIMIZATION
   → Can this be idempotent?
   → Should I check current state first?
   → Are there more efficient approaches?

5. VERIFICATION STEPS
   → How can we verify success?
   → What should expected_output describe?
   → Should we add validation commands?

═══════════════════════════════════════════════════════════════
REMEMBER:
✓ You are generating commands for {os_name} {os_version} SPECIFICALLY
✓ Use {package_manager} for ALL package operations
✓ Use {service_manager} for ALL service operations  
✓ Output ONLY valid JSON - no markdown, no extra text
✓ Every command will be executed immediately in production
✓ When in doubt about safety, mark risk_level as "high" and explain concerns
═══════════════════════════════════════════════════════════════"""
    
    def _create_user_prompt(self, user_request: str) -> str:
        """Create user prompt optimized for Claude with enhanced context"""
        return f"""═══════════════════════════════════════════════════════════════
USER REQUEST
═══════════════════════════════════════════════════════════════
{user_request}

═══════════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════════
Analyze this request and generate production-ready commands that:

1. Are SPECIFIC to the system specifications provided above
2. Use the correct package manager and service manager for this OS
3. Include proper safety checks and error handling
4. Are idempotent where possible (can be run multiple times safely)
5. Consider the available tools on this system
6. Follow DevOps best practices for this OS family

Think through:
• What is the user trying to accomplish?
• What commands are needed on THIS specific OS distribution?
• What safety checks should be included?
• What could go wrong and how to prevent it?
• Are there any dependencies or prerequisites?
• How should success be verified?

═══════════════════════════════════════════════════════════════
CRITICAL OUTPUT FORMAT REQUIREMENTS
═══════════════════════════════════════════════════════════════
⚠️  RESPOND WITH ONLY THE RAW JSON OBJECT - NOTHING ELSE!

DO NOT include:
❌ Markdown code blocks (```json ... ```)
❌ Explanatory text before or after the JSON
❌ Comments in the JSON (// or /* */)
❌ Trailing commas in arrays or objects
❌ Any text outside the JSON object

DO include:
✅ Pure, valid JSON starting with {{ and ending with }}
✅ All required fields (intent, action, packages, services, risk_level, explanation, steps)
✅ Properly escaped strings (use \\" for quotes inside strings)
✅ Valid JSON syntax throughout

Your ENTIRE response should be parseable by JSON.parse() with no modifications."""
    
    def _call_claude(self, user_prompt: str, system_prompt: str) -> str:
        """Call Anthropic Claude API"""
        try:
            response = self.anthropic_client.messages.create(
                model=DEFAULT_CLAUDE_MODEL,
                max_tokens=DEFAULT_CLAUDE_MAX_TOKENS,
                temperature=DEFAULT_CLAUDE_TEMPERATURE,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error calling Anthropic Claude: {e}"
    
    def _parse_and_validate_ai_response(self, response: str, user_request: str) -> Dict[str, Any]:
        """Parse and validate Claude's response"""
        try:
            print(f"🔍 Claude Response: {response[:200]}...")
            
            # Extract JSON from response
            parsed_response = self._extract_json_from_response(response)
            if not parsed_response:
                error_msg = "Could not extract valid JSON from Claude's response"
                print(f"❌ {error_msg}")
                return self._create_error_fallback(user_request, error_msg)
            
            # Validate and fix commands for OS-specific compatibility
            self._validate_and_fix_commands(parsed_response)
            
            print(f"✅ Successfully generated {len(parsed_response.get('steps', []))} commands")
            return parsed_response
            
        except Exception as e:
            print(f"❌ Error parsing Claude response: {e}")
            return self._create_error_fallback(user_request, f"Parse error: {str(e)}")
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract and clean JSON from Claude's response with robust error handling"""
        import re
        
        try:
            # Step 1: Strip markdown code blocks (```json ... ``` or ``` ... ```)
            response = re.sub(r'^```(?:json)?\s*\n', '', response, flags=re.MULTILINE)
            response = re.sub(r'\n```\s*$', '', response, flags=re.MULTILINE)
            
            # Step 2: Extract JSON object (find outermost braces)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                print("❌ No JSON object found in response")
                return None
            
            json_str = json_match.group()
            print(f"🔍 Extracted JSON ({len(json_str)} chars): {json_str[:200]}...")
            
            # Step 3: Clean the JSON string
            json_str = self._clean_json_string(json_str)
            
            # Step 4: Try to parse
            parsed = json.loads(json_str)
            print(f"✅ Successfully parsed JSON with {len(parsed.get('steps', []))} steps")
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error at line {e.lineno}, col {e.colno}: {e.msg}")
            print(f"📍 Error context: ...{json_str[max(0, e.pos-50):e.pos+50]}...")
            
            # Try to fix common JSON errors and retry
            try:
                fixed_json = self._try_fix_json_errors(json_str, e)
                if fixed_json:
                    parsed = json.loads(fixed_json)
                    print(f"✅ Fixed and parsed JSON with {len(parsed.get('steps', []))} steps")
                    return parsed
            except Exception as fix_error:
                print(f"❌ Could not auto-fix JSON: {fix_error}")
            
            return None
            
        except Exception as e:
            print(f"❌ Unexpected error extracting JSON: {e}")
            return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean common JSON formatting issues from Claude's response"""
        import re
        
        # Remove // style comments (not valid in JSON)
        json_str = re.sub(r'//[^\n]*', '', json_str)
        
        # Remove /* */ style comments
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # Fix trailing commas before closing braces/brackets
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # CRITICAL: Escape unescaped control characters inside string values
        # This fixes "Invalid control character at" errors from Claude
        json_str = self._escape_control_characters_in_strings(json_str)
        
        # Remove any non-JSON text before first { or after last }
        json_str = json_str.strip()
        
        return json_str
    
    def _escape_control_characters_in_strings(self, json_str: str) -> str:
        """Escape literal control characters (newlines, tabs, etc.) ONLY inside JSON string values"""
        import re
        
        # This regex finds string values in JSON and escapes control characters within them
        # It matches: "key": "value with\npotential\ncontrol chars"
        
        def escape_string_content(match):
            """Escape control characters inside a JSON string value"""
            string_value = match.group(0)
            
            # Only process if it's a string value (starts with ")
            if not string_value.startswith('"'):
                return string_value
            
            # Escape control characters inside the string
            string_value = string_value.replace('\r\n', ' ')  # Replace Windows line endings with space
            string_value = string_value.replace('\n', ' ')     # Replace Unix newlines with space
            string_value = string_value.replace('\r', ' ')     # Replace carriage returns with space
            string_value = string_value.replace('\t', ' ')     # Replace tabs with space
            
            # Replace other control characters (ASCII 0-31) with space
            for i in range(32):
                if chr(i) not in [' ', '\n', '\r', '\t']:  # Don't double-process
                    string_value = string_value.replace(chr(i), ' ')
            
            return string_value
        
        # Match string values in JSON (handles escaped quotes AND newlines inside strings)
        # Pattern: "..." where ... can contain escaped quotes \" AND literal newlines
        # We use DOTALL flag so . matches newlines too
        pattern = r'"(?:[^"\\]|\\.|[\n\r])*?"'
        
        try:
            json_str = re.sub(pattern, escape_string_content, json_str, flags=re.DOTALL)
        except Exception as e:
            print(f"⚠️ Could not escape control characters: {e}")
            # If regex fails, do a simpler global replace (may break JSON structure but better than crash)
            json_str = json_str.replace('\r\n', ' ')
            json_str = json_str.replace('\n', ' ')
            json_str = json_str.replace('\r', ' ')
            json_str = json_str.replace('\t', ' ')
        
        return json_str
    
    def _try_fix_json_errors(self, json_str: str, error: json.JSONDecodeError) -> Optional[str]:
        """Try to automatically fix common JSON errors"""
        import re
        
        # If the error is near the end, the JSON might be truncated
        if error.pos > len(json_str) - 100:
            print("🔧 Attempting to fix truncated JSON...")
            
            # Count unclosed braces and brackets
            open_braces = json_str.count('{') - json_str.count('}')
            open_brackets = json_str.count('[') - json_str.count(']')
            
            # Close any unclosed structures
            fixed = json_str
            for _ in range(open_brackets):
                fixed += ']'
            for _ in range(open_braces):
                fixed += '}'
            
            return fixed
        
        # If error is "Expecting ',' delimiter", try adding missing commas
        if "Expecting ',' delimiter" in error.msg:
            print("🔧 Attempting to fix missing comma...")
            # This is complex - let Claude handle it by regenerating
            return None
        
        # If error is "Expecting property name", there's a trailing comma
        if "Expecting property name" in error.msg:
            print("🔧 Removing trailing comma...")
            # Already handled in _clean_json_string, but try again
            fixed = re.sub(r',(\s*})', r'\1', json_str)
            fixed = re.sub(r',(\s*])', r'\1', fixed)
            return fixed
        
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