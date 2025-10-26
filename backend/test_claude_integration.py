#!/usr/bin/env python3
"""
Quick test script to verify Claude integration is working
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the llm-os-agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm-os-agent'))

from anthropic import Anthropic

def test_api_key():
    """Test that API key is set"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False
    print(f"✅ API key found: {api_key[:20]}...")
    return True

def test_basic_call():
    """Test a basic Claude API call"""
    print("\n🧪 Testing basic Claude API call...")
    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'Hello from Claude!' and nothing else."}
            ]
        )
        
        result = response.content[0].text
        print(f"✅ Claude responded: {result}")
        return True
    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        return False

def test_command_generator():
    """Test the command generator with Claude"""
    print("\n🧪 Testing command generator...")
    try:
        from command_generator import CommandGenerator
        
        # Mock system context
        test_context = {
            "os_name": "Ubuntu",
            "os_version": "22.04",
            "os_family": "debian",
            "package_manager": "apt-get",
            "service_manager": "systemctl",
            "available_tools": ["curl", "wget", "git", "vim", "ps", "df", "free"],
            "memory_available": "8GB",
            "disk_available": "50GB"
        }
        
        generator = CommandGenerator(
            system_context=test_context,
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        # Test a simple command generation
        print("   Asking Claude to generate commands for: 'Check disk space'")
        result = generator.generate_commands("Check disk space")
        
        if result and 'steps' in result:
            print(f"✅ Command generation successful!")
            print(f"   Intent: {result.get('intent', 'N/A')}")
            print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
            print(f"   Steps: {len(result.get('steps', []))}")
            for i, step in enumerate(result.get('steps', [])[:3], 1):
                print(f"   Step {i}: {step.get('command', 'N/A')}")
            return True
        else:
            print("❌ Command generation failed - no steps returned")
            return False
            
    except Exception as e:
        print(f"❌ Error in command generator: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🧪 Claude Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("API Key Configuration", test_api_key),
        ("Basic Claude API Call", test_basic_call),
        ("Command Generator Integration", test_command_generator)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Test: {name}")
        print("-" * 60)
        results.append(test_func())
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for (name, _), result in zip(tests, results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(results)
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Claude integration is working!")
        print("=" * 60)
        print("\n✅ Next steps:")
        print("1. Start the backend server:")
        print("   cd backend/llm-os-agent")
        print("   uvicorn api_server_enhanced:app --reload --port 8000")
        print("\n2. Visit http://localhost:8000/docs to test the API")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

