#!/usr/bin/env python3
"""
Database setup script for Ping AI Agent
This script helps you set up and manage the PostgreSQL database
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add the llm-os-agent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm-os-agent'))

def setup_database():
    """Set up the database and create tables"""
    print("🗄️  Setting up Ping AI Agent Database...")
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("📋 Please set it using one of these methods:")
        print("   1. Railway CLI: railway variables set DATABASE_URL=your_postgres_url")
        print("   2. Environment: export DATABASE_URL=your_postgres_url")
        print("   3. For local testing: export DATABASE_URL=sqlite:///./otium.db")
        return False
    
    print(f"✅ Database URL found: {database_url[:50]}...")
    
    try:
        # Test database connection
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
        
        # Import and create tables
        from database import init_database, create_tables
        create_tables()
        print("✅ Database tables created successfully!")
        
        # Test basic operations
        from database_service import DatabaseService
        from database import get_db
        
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Create a test user
        test_user = db_service.create_or_get_user(
            user_id="test_user",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        print(f"✅ Test user created: {test_user.id}")
        
        db.close()
        
        print("\n🎉 Database setup complete!")
        print("📋 Available tables:")
        print("   - users (user accounts and roles)")
        print("   - connections (SSH connections with encrypted credentials)")
        print("   - commands (AI-generated commands)")
        print("   - command_approvals (step-by-step approvals)")
        print("   - audit_logs (complete audit trail)")
        print("   - system_checkpoints (system state snapshots)")
        
        return True
        
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("📋 Make sure your DATABASE_URL is correct and the database is accessible")
        return False
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def show_database_info():
    """Show information about the current database setup"""
    print("📊 Database Information")
    print("=" * 50)
    
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print(f"Database URL: {database_url[:50]}...")
        
        # Try to connect and show basic info
        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                # Get database version
                if "postgresql" in database_url:
                    result = conn.execute(text("SELECT version()"))
                    version = result.fetchone()[0]
                    print(f"Database: PostgreSQL")
                    print(f"Version: {version}")
                elif "sqlite" in database_url:
                    result = conn.execute(text("SELECT sqlite_version()"))
                    version = result.fetchone()[0]
                    print(f"Database: SQLite")
                    print(f"Version: {version}")
                
                # Count tables
                if "postgresql" in database_url:
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """))
                else:
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM sqlite_master 
                        WHERE type='table'
                    """))
                
                table_count = result.fetchone()[0]
                print(f"Tables: {table_count}")
                
        except Exception as e:
            print(f"❌ Could not connect to database: {e}")
    else:
        print("❌ No DATABASE_URL environment variable set")

def show_railway_help():
    """Show Railway-specific database setup help"""
    print("🚂 Railway Database Setup Help")
    print("=" * 50)
    print("1. Add PostgreSQL to your Railway project:")
    print("   railway add --database postgres")
    print()
    print("2. Get the database URL:")
    print("   railway variables get DATABASE_URL")
    print()
    print("3. Set the DATABASE_URL in your service:")
    print("   railway variables set DATABASE_URL=postgresql://...")
    print()
    print("4. Deploy your service:")
    print("   railway up")
    print()
    print("5. View your database in Railway dashboard:")
    print("   railway open")
    print()
    print("📋 Railway Dashboard Features:")
    print("   - View database tables and data")
    print("   - Run SQL queries")
    print("   - Monitor database performance")
    print("   - View connection logs")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "info":
            show_database_info()
        elif sys.argv[1] == "railway":
            show_railway_help()
        else:
            print("Usage: python setup_database.py [info|railway]")
    else:
        setup_database()
