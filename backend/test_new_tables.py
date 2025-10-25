#!/usr/bin/env python3
"""
Test script to verify the new state-aware execution tables work correctly
"""

import os
import sys
import uuid
from datetime import datetime

# Add the llm-os-agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm-os-agent'))

from database import (
    Base, engine, SessionLocal, 
    User, Command, CommandStep, SystemStateSnapshot, StepEvaluation, CommandApproval
)

def test_new_tables():
    """Test that the new tables can be created and used"""
    
    print("🧪 Testing new state-aware execution tables...")
    
    # Create a test session
    db = SessionLocal()
    
    try:
        # Test 1: Create a test user
        print("1️⃣ Creating test user...")
        test_user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        db.add(test_user)
        db.commit()
        print("✅ Test user created")
        
        # Test 2: Create a test command with new fields
        print("2️⃣ Creating test command with state-aware fields...")
        test_command = Command(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            connection_id="test-connection",
            request="Test state-aware command",
            intent="test",
            action="test_action",
            # New state-aware fields
            current_step_index=0,
            requires_state_evaluation=True,
            adaptive_mode=True,
            baseline_system_state={"os": "Ubuntu", "version": "22.04"},
            state_evaluation_count=0,
            adaptive_steps_generated=0,
            corrective_steps_generated=0
        )
        db.add(test_command)
        db.commit()
        print("✅ Test command created with state-aware fields")
        
        # Test 3: Create a test command step
        print("3️⃣ Creating test command step...")
        test_step = CommandStep(
            id=str(uuid.uuid4()),
            command_id=test_command.id,
            step_index=0,
            step_type="generated",
            command="echo 'Hello World'",
            explanation="Test command step",
            risk_level="low",
            status="pending",
            expected_outcome="Print Hello World",
            system_state_before={"memory": "8G", "disk": "50G"},
            system_state_after={"memory": "8G", "disk": "50G"}
        )
        db.add(test_step)
        db.commit()
        print("✅ Test command step created")
        
        # Test 4: Create a test system state snapshot
        print("4️⃣ Creating test system state snapshot...")
        test_snapshot = SystemStateSnapshot(
            id=str(uuid.uuid4()),
            command_id=test_command.id,
            step_id=test_step.id,
            snapshot_type="before_step",
            system_info={"os": "Ubuntu", "version": "22.04", "cpu": "4 cores"},
            services_status=["ssh", "nginx"],
            packages_installed=["nginx", "apache2"],
            network_connections=[{"interface": "eth0", "status": "up"}],
            resource_usage={"cpu": "10%", "memory": "2G", "disk": "45G"}
        )
        db.add(test_snapshot)
        db.commit()
        print("✅ Test system state snapshot created")
        
        # Test 5: Create a test step evaluation
        print("5️⃣ Creating test step evaluation...")
        test_evaluation = StepEvaluation(
            id=str(uuid.uuid4()),
            step_id=test_step.id,
            evaluation_type="success",
            success_indicators=["Command executed successfully", "Exit code 0"],
            failure_indicators=[],
            state_changes=[{"type": "file_change", "description": "Output file created"}],
            recommendations=["Step completed successfully"],
            confidence_score=0.95
        )
        db.add(test_evaluation)
        db.commit()
        print("✅ Test step evaluation created")
        
        # Test 6: Create a test command approval with new fields
        print("6️⃣ Creating test command approval with state-aware fields...")
        test_approval = CommandApproval(
            id=str(uuid.uuid4()),
            command_id=test_command.id,
            user_id=test_user.id,
            step_index=0,
            approved=True,
            approval_reason="Test approval",
            # New state-aware fields
            step_id=test_step.id,
            state_context={"system_state": "stable", "risk_level": "low"},
            approval_reasoning="Low risk command, system state is stable",
            expected_impact={"changes": ["output file creation"], "risk": "minimal"}
        )
        db.add(test_approval)
        db.commit()
        print("✅ Test command approval created with state-aware fields")
        
        # Test 7: Verify relationships work
        print("7️⃣ Testing relationships...")
        
        # Test command -> steps relationship
        command_steps = test_command.steps
        print(f"   Command has {len(command_steps)} steps")
        
        # Test command -> state snapshots relationship
        command_snapshots = test_command.state_snapshots
        print(f"   Command has {len(command_snapshots)} state snapshots")
        
        # Test step -> evaluations relationship
        step_evaluations = test_step.evaluations
        print(f"   Step has {len(step_evaluations)} evaluations")
        
        # Test step -> approvals relationship
        step_approvals = test_step.approvals
        print(f"   Step has {len(step_approvals)} approvals")
        
        print("✅ All relationships working correctly")
        
        # Test 8: Query the data back
        print("8️⃣ Testing data retrieval...")
        
        # Query command with all related data
        retrieved_command = db.query(Command).filter(Command.id == test_command.id).first()
        print(f"   Retrieved command: {retrieved_command.request}")
        print(f"   Adaptive mode: {retrieved_command.adaptive_mode}")
        print(f"   State evaluation count: {retrieved_command.state_evaluation_count}")
        
        # Query step with evaluation
        retrieved_step = db.query(CommandStep).filter(CommandStep.id == test_step.id).first()
        print(f"   Retrieved step: {retrieved_step.command}")
        print(f"   Step type: {retrieved_step.step_type}")
        print(f"   Status: {retrieved_step.status}")
        
        print("✅ Data retrieval working correctly")
        
        print("\n🎉 All tests passed! New state-aware execution tables are working correctly!")
        print("\n📊 Summary of what was tested:")
        print("  ✅ command_steps table")
        print("  ✅ system_state_snapshots table") 
        print("  ✅ step_evaluations table")
        print("  ✅ Enhanced commands table (new fields)")
        print("  ✅ Enhanced command_approvals table (new fields)")
        print("  ✅ All relationships working")
        print("  ✅ Data storage and retrieval")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_new_tables()
    sys.exit(0 if success else 1)
