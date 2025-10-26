#!/usr/bin/env python3
"""
Test script for chat functionality
"""
import os
import sys
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user"
TEST_COMMAND_ID = None  # Will be set after creating a command

def test_create_command():
    """Create a test command"""
    global TEST_COMMAND_ID
    
    print("🧪 Test 1: Creating a test command...")
    
    # This would normally come from submitting a task
    # For testing, we'll use the database directly
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm-os-agent'))
    from database import Base, Command, User, Connection
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime
    import uuid
    
    # Connect to database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ping.db")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get test user
        user = session.query(User).filter_by(id=TEST_USER_ID).first()
        if not user:
            print("❌ Test user not found. Run setup_database.py first.")
            return False
        
        # Create a test command
        command = Command(
            id=str(uuid.uuid4()),
            user_id=TEST_USER_ID,
            connection_id="test_connection",
            request="Test command for chat",
            intent="test",
            action="test",
            risk_level="low",
            generated_commands=[{
                "step": 1,
                "command": "echo 'test'",
                "explanation": "Test command"
            }]
        )
        session.add(command)
        session.commit()
        
        TEST_COMMAND_ID = command.id
        print(f"✅ Test command created: {TEST_COMMAND_ID}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating test command: {e}")
        return False
    finally:
        session.close()

def test_send_message():
    """Test sending a chat message"""
    global TEST_COMMAND_ID
    
    if not TEST_COMMAND_ID:
        print("❌ No command ID available")
        return False
    
    print("\n🧪 Test 2: Sending a chat message...")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code != 200:
            print("❌ Server not responding. Start it with: uvicorn api_server_enhanced:app --reload")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Start it with: uvicorn api_server_enhanced:app --reload")
        return False
    
    # Send chat message
    url = f"{BASE_URL}/api/commands/{TEST_COMMAND_ID}/chat"
    headers = {"user-id": TEST_USER_ID, "Content-Type": "application/json"}
    data = {"message": "Hello, this is a test message"}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Message sent successfully!")
            print(f"   User message: {result['user_message']['message']}")
            print(f"   AI response: {result['ai_message']['message']}")
            return True
        else:
            print(f"❌ Error sending message: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception sending message: {e}")
        return False

def test_get_messages():
    """Test retrieving chat messages"""
    global TEST_COMMAND_ID
    
    if not TEST_COMMAND_ID:
        print("❌ No command ID available")
        return False
    
    print("\n🧪 Test 3: Retrieving chat messages...")
    
    url = f"{BASE_URL}/api/commands/{TEST_COMMAND_ID}/chat"
    headers = {"user-id": TEST_USER_ID}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            messages = result.get('messages', [])
            print(f"✅ Retrieved {len(messages)} message(s)")
            
            for msg in messages:
                sender = "👤 User" if msg['sender'] == 'user' else "🤖 AI"
                print(f"   {sender}: {msg['message']}")
            
            return True
        else:
            print(f"❌ Error retrieving messages: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception retrieving messages: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing Chat Functionality")
    print("=" * 60)
    
    # Test 1: Create command (using database directly)
    if not test_create_command():
        print("\n❌ Test failed at command creation")
        return 1
    
    # Test 2: Send message (requires API server running)
    if not test_send_message():
        print("\n⚠️  Message test failed (server may not be running)")
        print("   To test fully, run: uvicorn api_server_enhanced:app --reload")
        return 1
    
    # Test 3: Get messages
    if not test_get_messages():
        print("\n❌ Test failed at message retrieval")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
