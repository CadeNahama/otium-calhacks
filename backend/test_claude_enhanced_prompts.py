#!/usr/bin/env python3
"""
Test Claude's enhanced context-aware command generation
Demonstrates improvements from OpenAI to Claude with optimized prompts
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the llm-os-agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm-os-agent'))

from command_generator import CommandGenerator

def test_context_aware_generation():
    """Test that Claude uses system context effectively"""
    print("=" * 80)
    print("🧪 Testing Claude's Context-Aware Command Generation")
    print("=" * 80)
    
    # Test with Ubuntu system
    ubuntu_context = {
        "os_name": "Ubuntu",
        "os_version": "22.04 LTS",
        "os_family": "debian",
        "package_manager": "apt-get",
        "service_manager": "systemctl",
        "available_tools": ["curl", "wget", "git", "vim", "ps", "df", "free", "systemctl", "apt-get"],
        "memory_available": "8GB",
        "disk_available": "50GB",
        "architecture": "x86_64",
        "kernel_version": "5.15.0-91-generic"
    }
    
    # Test with CentOS system
    centos_context = {
        "os_name": "CentOS",
        "os_version": "8.5",
        "os_family": "rhel",
        "package_manager": "dnf",
        "service_manager": "systemctl",
        "available_tools": ["curl", "wget", "git", "vim", "ps", "df", "free", "systemctl", "dnf"],
        "memory_available": "16GB",
        "disk_available": "100GB",
        "architecture": "x86_64",
        "kernel_version": "4.18.0-348.el8.x86_64"
    }
    
    test_cases = [
        {
            "name": "Install Web Server on Ubuntu",
            "context": ubuntu_context,
            "request": "Install and configure nginx web server"
        },
        {
            "name": "Install Web Server on CentOS",
            "context": centos_context,
            "request": "Install and configure nginx web server"
        },
        {
            "name": "System Health Check",
            "context": ubuntu_context,
            "request": "Check system health including CPU, memory, disk, and running services"
        },
        {
            "name": "Security Update (requires OS-specific commands)",
            "context": ubuntu_context,
            "request": "Update security patches"
        }
    ]
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found")
        return False
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"Test Case {i}: {test_case['name']}")
        print(f"{'─' * 80}")
        print(f"Context: {test_case['context']['os_name']} {test_case['context']['os_version']}")
        print(f"Package Manager: {test_case['context']['package_manager']}")
        print(f"Request: \"{test_case['request']}\"")
        print()
        
        try:
            generator = CommandGenerator(
                system_context=test_case['context'],
                api_key=api_key
            )
            
            print("🤖 Calling Claude Sonnet 4.5...")
            result = generator.generate_commands(test_case['request'])
            
            if result and 'steps' in result:
                print(f"✅ Success! Generated {len(result['steps'])} steps")
                print(f"\n📋 Response Details:")
                print(f"   Intent: {result.get('intent', 'N/A')}")
                print(f"   Action: {result.get('action', 'N/A')}")
                print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
                print(f"   Packages: {', '.join(result.get('packages', [])) or 'None'}")
                print(f"   Services: {', '.join(result.get('services', [])) or 'None'}")
                print(f"\n💡 Explanation:")
                print(f"   {result.get('explanation', 'N/A')}")
                print(f"\n🔧 Generated Commands:")
                
                for step in result['steps'][:5]:  # Show first 5 steps
                    print(f"   Step {step['step']}: {step['command']}")
                    print(f"      → {step['description']}")
                
                # Verify context awareness
                context_checks = {
                    "Uses correct package manager": test_case['context']['package_manager'] in ' '.join(s['command'] for s in result['steps']),
                    "Uses correct service manager": test_case['context']['service_manager'] in ' '.join(s['command'] for s in result['steps']) or len(result['steps']) == 0,
                    "Has risk assessment": 'risk_level' in result and result['risk_level'] in ['low', 'medium', 'high'],
                    "Includes explanation": 'explanation' in result and len(result['explanation']) > 20
                }
                
                print(f"\n🎯 Context-Awareness Checks:")
                for check, passed in context_checks.items():
                    status = "✅" if passed else "❌"
                    print(f"   {status} {check}")
                
                if not all(context_checks.values()):
                    all_passed = False
                    print(f"\n⚠️  Some context checks failed")
                
            else:
                print("❌ No steps generated")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print(f"\n{'=' * 80}")
    if all_passed:
        print("🎉 All tests passed! Claude is using system context effectively!")
    else:
        print("⚠️  Some tests had issues")
    print(f"{'=' * 80}")
    
    return all_passed

def compare_prompt_improvements():
    """Show the improvements made to prompts"""
    print("\n" + "=" * 80)
    print("📊 Prompt Improvements for Claude Sonnet 4.5")
    print("=" * 80)
    
    improvements = [
        {
            "category": "System Context",
            "old": "Basic OS info and package manager",
            "new": "Detailed specs: OS family, architecture, kernel, available tools, resources"
        },
        {
            "category": "Safety Guidance",
            "old": "Generic safety rules",
            "new": "Comprehensive safety protocols with critical services list and forbidden operations"
        },
        {
            "category": "Decision Framework",
            "old": "No explicit framework",
            "new": "5-step decision-making process: Analysis → Adaptation → Safety → Optimization → Verification"
        },
        {
            "category": "OS-Specific Best Practices",
            "old": "Not included",
            "new": "Debian/Ubuntu vs RHEL/CentOS specific command guidance"
        },
        {
            "category": "Risk Assessment",
            "old": "Simple low/medium/high",
            "new": "Detailed criteria with examples for each level"
        },
        {
            "category": "Output Quality",
            "old": "Basic command generation",
            "new": "Idempotent, context-aware commands with error handling"
        },
        {
            "category": "Token Allocation",
            "old": "1000 tokens",
            "new": "2000 tokens for comprehensive DevOps responses"
        }
    ]
    
    for improvement in improvements:
        print(f"\n📌 {improvement['category']}")
        print(f"   Before: {improvement['old']}")
        print(f"   After:  {improvement['new']}")
    
    print("\n" + "=" * 80)

def main():
    print("🚀 Claude Enhanced Prompt Testing Suite")
    print("Testing context-aware command generation with optimized prompts\n")
    
    # Show improvements
    compare_prompt_improvements()
    
    # Run tests
    success = test_context_aware_generation()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

