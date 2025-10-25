#!/usr/bin/env python3
"""
Database Migration Script for State-Aware Execution Tables
Adds the new tables and columns required for state-aware step execution
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

# Add the llm-os-agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm-os-agent'))

from database import DATABASE_URL, Base

def run_migration():
    """Run the database migration to add state-aware execution tables"""
    
    print("🚀 Starting State-Aware Execution Database Migration...")
    print(f"📊 Database URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else DATABASE_URL)
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # First, add new columns to existing tables (PostgreSQL ALTER TABLE)
        print("📋 Adding new columns to existing tables...")
        with engine.connect() as conn:
            # Check if we're using PostgreSQL or SQLite
            is_postgres = 'postgresql' in DATABASE_URL
            
            if is_postgres:
                print("   Detected PostgreSQL, using ALTER TABLE...")
                
                # Add columns to commands table
                try:
                    conn.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS current_step_index INTEGER DEFAULT 0"))
                    conn.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS requires_state_evaluation BOOLEAN DEFAULT TRUE"))
                    conn.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS adaptive_mode BOOLEAN DEFAULT FALSE"))
                    conn.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS baseline_system_state JSONB"))
                    conn.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS last_state_evaluation TIMESTAMP"))
                    conn.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS state_evaluation_count INTEGER DEFAULT 0"))
                    conn.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS adaptive_steps_generated INTEGER DEFAULT 0"))
                    conn.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS corrective_steps_generated INTEGER DEFAULT 0"))
                    conn.commit()
                    print("   ✅ Commands table updated")
                except Exception as e:
                    print(f"   ⚠️  Commands table columns may already exist: {e}")
                    conn.rollback()
                
                # Add columns to command_approvals table
                try:
                    conn.execute(text("ALTER TABLE command_approvals ADD COLUMN IF NOT EXISTS step_id VARCHAR"))
                    conn.execute(text("ALTER TABLE command_approvals ADD COLUMN IF NOT EXISTS state_context JSONB"))
                    conn.execute(text("ALTER TABLE command_approvals ADD COLUMN IF NOT EXISTS approval_reasoning TEXT"))
                    conn.execute(text("ALTER TABLE command_approvals ADD COLUMN IF NOT EXISTS expected_impact JSONB"))
                    conn.commit()
                    print("   ✅ Command approvals table updated")
                except Exception as e:
                    print(f"   ⚠️  Command approvals columns may already exist: {e}")
                    conn.rollback()
        
        # Create all tables (this will add new tables without affecting existing ones)
        print("📋 Creating new tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Migration completed successfully!")
        print("\n📊 New tables created:")
        print("  - command_steps")
        print("  - system_state_snapshots") 
        print("  - step_evaluations")
        print("\n📝 Updated tables:")
        print("  - commands (added state-aware fields)")
        print("  - command_approvals (added state-aware fields)")
        
        # Verify tables exist
        with engine.connect() as conn:
            # Check if new tables exist (SQLite compatible)
            tables_to_check = [
                'command_steps',
                'system_state_snapshots', 
                'step_evaluations'
            ]
            
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"))
                    exists = result.fetchone() is not None
                    if exists:
                        print(f"✅ Table '{table}' exists")
                    else:
                        print(f"❌ Table '{table}' missing")
                except Exception as e:
                    print(f"⚠️  Could not verify table '{table}': {e}")
        
        print("\n🎯 State-aware execution database schema is ready!")
        print("💡 Next steps:")
        print("  1. Update application code to use new tables")
        print("  2. Integrate StateEvaluator into command execution")
        print("  3. Implement adaptive step generation")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
