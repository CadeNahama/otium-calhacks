#!/usr/bin/env python3
"""
SSH System Detector for Ping AI Agent - Phase 1 Simplified
Detects basic system information on remote servers via SSH
"""

from typing import Dict, Any
from datetime import datetime


class SSHSystemDetector:
    """System detection for remote servers via SSH - Phase 1 Simplified"""
    
    def __init__(self, ssh_manager, connection_id: str):
        self.ssh_manager = ssh_manager
        self.connection_id = connection_id
        self.detection_time = datetime.now().isoformat()
        self.system_info = {}
        
    def detect_system(self) -> Dict[str, Any]:
        """Main detection method - detects essential system information"""
        print("🔍 Detecting remote system environment via SSH...")
        
        # 1. OS Detection
        os_info = self._detect_os()
        self.system_info.update(os_info)
        
        # 2. Package Manager Detection
        pkg_info = self._detect_package_manager()
        self.system_info.update(pkg_info)
        
        # 3. Service Manager Detection
        svc_info = self._detect_service_manager()
        self.system_info.update(svc_info)
        
        # 4. Available Tools Detection
        tools_info = self._detect_available_tools()
        self.system_info.update(tools_info)
        
        # 5. Basic System Resources
        resources_info = self._detect_basic_resources()
        self.system_info.update(resources_info)
        
        # Print summary
        self._print_detection_summary()
        
        return self.system_info
    
    def _run_ssh_command(self, command: str) -> Dict[str, Any]:
        """Run command via SSH and return result"""
        try:
            result = self.ssh_manager.execute_command(self.connection_id, command)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1
            }
    
    def _detect_os(self) -> Dict[str, Any]:
        """Detect operating system and version via SSH"""
        try:
            # Try different OS release files
            release_files = [
                "/etc/redhat-release",
                "/etc/os-release", 
                "/etc/lsb-release",
                "/etc/debian_version"
            ]
            
            for release_file in release_files:
                result = self._run_ssh_command(f"cat {release_file}")
                if result['success']:
                    content = result['stdout'].strip()
                    
                    if "redhat" in release_file.lower() or "centos" in content.lower():
                        return {
                            "os_name": "Red Hat Enterprise Linux",
                            "os_version": content,
                            "os_family": "rhel"
                        }
                    elif "debian" in content.lower() or "ubuntu" in content.lower():
                        return {
                            "os_name": "Debian/Ubuntu",
                            "os_version": content,
                            "os_family": "debian"
                        }
                    elif "suse" in content.lower() or "opensuse" in content.lower():
                        return {
                            "os_name": "SUSE Linux",
                            "os_version": content,
                            "os_family": "suse"
                        }
            
            # Fallback to uname
            result = self._run_ssh_command("uname -a")
            if result['success']:
                return {
                    "os_name": "Linux",
                    "os_version": result['stdout'].strip(),
                    "os_family": "unknown"
                }
            
        except Exception as e:
            print(f"⚠️  Error detecting OS: {e}")
        
        return {
            "os_name": "Unknown",
            "os_version": "Unknown",
            "os_family": "unknown"
        }
    
    def _detect_package_manager(self) -> Dict[str, Any]:
        """Detect package manager via SSH"""
        package_managers = [
            ("dnf", "dnf --version"),
            ("yum", "yum --version"),
            ("apt", "apt --version"),
            ("apt-get", "apt-get --version"),
            ("zypper", "zypper --version"),
            ("pacman", "pacman --version")
        ]
        
        for pm_name, pm_cmd in package_managers:
            result = self._run_ssh_command(pm_cmd)
            if result['success']:
                return {
                    "package_manager": pm_name,
                    "package_manager_version": result['stdout'].strip().split('\n')[0]
                }
        
        return {"package_manager": "unknown"}
    
    def _detect_service_manager(self) -> Dict[str, Any]:
        """Detect service manager via SSH"""
        service_managers = [
            ("systemctl", "systemctl --version"),
            ("service", "service --version"),
            ("rc-service", "rc-service --version")
        ]
        
        for sm_name, sm_cmd in service_managers:
            result = self._run_ssh_command(sm_cmd)
            if result['success']:
                return {
                    "service_manager": sm_name,
                    "service_manager_version": result['stdout'].strip().split('\n')[0]
                }
        
        return {"service_manager": "unknown"}
    
    def _detect_available_tools(self) -> Dict[str, Any]:
        """Detect available tools via SSH"""
        tools = [
            "curl", "wget", "git", "vim", "nano", "htop", "tree",
            "ss", "netstat", "iptables", "firewall-cmd", "ufw",
            "ps", "top", "free", "df", "du", "lscpu", "cat"
        ]
        
        available_tools = []
        for tool in tools:
            result = self._run_ssh_command(f"which {tool}")
            if result['success']:
                available_tools.append(tool)
        
        return {"available_tools": available_tools}
    
    def _detect_basic_resources(self) -> Dict[str, Any]:
        """Detect basic system resources via SSH"""
        resources = {}
        
        # Memory info
        result = self._run_ssh_command("free -h")
        if result['success']:
            lines = result['stdout'].strip().split('\n')
            if len(lines) > 1:
                mem_line = lines[1].split()
                if len(mem_line) >= 2:
                    resources["memory_available"] = mem_line[1]
        
        # Disk info
        result = self._run_ssh_command("df -h /")
        if result['success']:
            lines = result['stdout'].strip().split('\n')
            if len(lines) > 1:
                disk_line = lines[1].split()
                if len(disk_line) >= 4:
                    resources["disk_available"] = disk_line[3]
        
        # CPU info
        result = self._run_ssh_command("nproc")
        if result['success']:
            resources["cpu_cores"] = result['stdout'].strip()
        
        return resources
    
    def _print_detection_summary(self) -> None:
        """Print detection summary"""
        print(f"\n📊 System Detection Summary:")
        print(f"   OS: {self.system_info.get('os_name', 'Unknown')} {self.system_info.get('os_version', '')}")
        print(f"   Package Manager: {self.system_info.get('package_manager', 'Unknown')}")
        print(f"   Service Manager: {self.system_info.get('service_manager', 'Unknown')}")
        print(f"   Available Tools: {len(self.system_info.get('available_tools', []))}")
        print(f"   Memory: {self.system_info.get('memory_available', 'Unknown')}")
        print(f"   Disk: {self.system_info.get('disk_available', 'Unknown')}")
        print(f"   CPU Cores: {self.system_info.get('cpu_cores', 'Unknown')}")
