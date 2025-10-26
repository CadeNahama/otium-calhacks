#!/usr/bin/env python3
"""
Database Viewer for Ping AI Agent
Interactive tool to view and manage your database
"""

import os
import sys
from datetime import datetime
import json

# Add the llm-os-agent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm-os-agent'))

def print_table_header(title):
    """Print a formatted table header"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")

def print_separator():
    """Print a separator line"""
    print("-" * 60)

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if timestamp:
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"

def view_users():
    """View all users"""
    try:
        from database import get_db
        from database_service import DatabaseService
        
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get all users (we'll need to add this method)
        users = db.query(db.query().from_statement(text("SELECT * FROM users")).all())
        
        print_table_header("USERS")
        if users:
            print(f"{'ID':<20} {'Email':<30} {'Role':<10} {'Last Login':<20}")
            print_separator()
            for user in users:
                print(f"{user.id:<20} {user.email:<30} {user.role:<10} {format_timestamp(user.last_login):<20}")
        else:
            print("No users found")
        
        db.close()
    except Exception as e:
        print(f"❌ Error viewing users: {e}")

def view_connections():
    """View all connections"""
    try:
        from database import get_db
        from database_service import DatabaseService
        
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get all connections
        connections = db.query(db.query().from_statement(text("SELECT * FROM connections")).all())
        
        print_table_header("SSH CONNECTIONS")
        if connections:
            print(f"{'ID':<20} {'User':<20} {'Hostname':<25} {'Status':<12} {'Connected':<20}")
            print_separator()
            for conn in connections:
                print(f"{conn.id[:20]:<20} {conn.user_id:<20} {conn.hostname:<25} {conn.status:<12} {format_timestamp(conn.connected_at):<20}")
        else:
            print("No connections found")
        
        db.close()
    except Exception as e:
        print(f"❌ Error viewing connections: {e}")

def view_recent_commands():
    """View recent commands"""
    try:
        from database import get_db
        from database_service import DatabaseService
        
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get recent commands
        commands = db.query(db.query().from_statement(text("SELECT * FROM commands ORDER BY created_at DESC LIMIT 10")).all())
        
        print_table_header("RECENT COMMANDS")
        if commands:
            print(f"{'ID':<20} {'User':<20} {'Request':<40} {'Status':<15} {'Risk':<8} {'Created':<20}")
            print_separator()
            for cmd in commands:
                request = cmd.request[:40] + "..." if len(cmd.request) > 40 else cmd.request
                print(f"{cmd.id[:20]:<20} {cmd.user_id:<20} {request:<40} {cmd.status:<15} {cmd.risk_level:<8} {format_timestamp(cmd.created_at):<20}")
        else:
            print("No commands found")
        
        db.close()
    except Exception as e:
        print(f"❌ Error viewing commands: {e}")

def view_approval_status():
    """View step-by-step approval status"""
    try:
        from database import get_db
        from database_service import DatabaseService
        from sqlalchemy import text
        
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get commands with approval status
        result = db.execute(text("""
            SELECT 
                c.id,
                c.request,
                c.status,
                COUNT(ca.id) as total_approvals,
                COUNT(CASE WHEN ca.approved = true THEN 1 END) as approved_steps,
                COUNT(CASE WHEN ca.approved = false THEN 1 END) as rejected_steps
            FROM commands c
            LEFT JOIN command_approvals ca ON c.id = ca.command_id
            GROUP BY c.id, c.request, c.status
            ORDER BY c.created_at DESC
            LIMIT 10
        """))
        
        print_table_header("APPROVAL STATUS")
        rows = result.fetchall()
        if rows:
            print(f"{'Command ID':<20} {'Request':<40} {'Status':<15} {'Approved':<8} {'Rejected':<8}")
            print_separator()
            for row in rows:
                request = row[1][:40] + "..." if len(row[1]) > 40 else row[1]
                print(f"{row[0][:20]:<20} {request:<40} {row[2]:<15} {row[4]:<8} {row[5]:<8}")
        else:
            print("No commands with approvals found")
        
        db.close()
    except Exception as e:
        print(f"❌ Error viewing approval status: {e}")

def view_recent_audit_logs():
    """View recent audit logs"""
    try:
        from database import get_db
        from database_service import DatabaseService
        from sqlalchemy import text
        
        db = next(get_db())
        db_service = DatabaseService(db)
        
        # Get recent audit logs
        result = db.execute(text("""
            SELECT user_id, action, success, timestamp, details
            FROM audit_logs
            ORDER BY timestamp DESC
            LIMIT 15
        """))
        
        print_table_header("RECENT AUDIT LOGS")
        rows = result.fetchall()
        if rows:
            print(f"{'User':<20} {'Action':<20} {'Success':<8} {'Timestamp':<20}")
            print_separator()
            for row in rows:
                success_icon = "✅" if row[2] else "❌"
                timestamp = format_timestamp(row[3]) if row[3] else "N/A"
                print(f"{row[0]:<20} {row[1]:<20} {success_icon:<8} {timestamp:<20}")
        else:
            print("No audit logs found")
        
        db.close()
    except Exception as e:
        print(f"❌ Error viewing audit logs: {e}")

def show_database_stats():
    """Show database statistics"""
    try:
        from database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        
        print_table_header("DATABASE STATISTICS")
        
        # Get table counts
        tables = ['users', 'connections', 'commands', 'command_approvals', 'audit_logs', 'system_checkpoints']
        
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"📋 {table:<20}: {count:>8} records")
            except Exception as e:
                print(f"❌ {table:<20}: Error - {e}")
        
        # Get recent activity
        try:
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total_commands,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as commands_today,
                    COUNT(CASE WHEN status = 'pending_approval' THEN 1 END) as pending_approvals
                FROM commands
            """))
            stats = result.fetchone()
            print(f"\n📊 Command Statistics:")
            print(f"   Total Commands: {stats[0]}")
            print(f"   Commands Today: {stats[1]}")
            print(f"   Pending Approvals: {stats[2]}")
        except Exception as e:
            print(f"❌ Could not get command statistics: {e}")
        
        db.close()
    except Exception as e:
        print(f"❌ Error getting database stats: {e}")

def interactive_menu():
    """Interactive menu for database viewing"""
    while True:
        print(f"\n{'='*60}")
        print("🗄️  PING AI AGENT DATABASE VIEWER")
        print(f"{'='*60}")
        print("1. 📊 Database Statistics")
        print("2. 👥 View Users")
        print("3. 🔌 View SSH Connections")
        print("4. 📝 View Recent Commands")
        print("5. ✅ View Approval Status")
        print("6. 📋 View Recent Audit Logs")
        print("7. 🔄 Refresh All")
        print("0. ❌ Exit")
        print("-" * 60)
        
        choice = input("Select an option (0-7): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            show_database_stats()
        elif choice == "2":
            view_users()
        elif choice == "3":
            view_connections()
        elif choice == "4":
            view_recent_commands()
        elif choice == "5":
            view_approval_status()
        elif choice == "6":
            view_recent_audit_logs()
        elif choice == "7":
            show_database_stats()
            view_users()
            view_connections()
            view_recent_commands()
            view_approval_status()
            view_recent_audit_logs()
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

def main():
    """Main function"""
    print("🗄️  Ping AI Agent Database Viewer")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("📋 Please set it first:")
        print("   export DATABASE_URL=your_database_url")
        print("   # or")
        print("   railway variables set DATABASE_URL=your_database_url")
        return
    
    print(f"✅ Database URL: {database_url[:50]}...")
    
    # Check if we can connect
    try:
        from database import get_db
        db = next(get_db())
        db.close()
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Start interactive menu
    interactive_menu()

if __name__ == "__main__":
    main()
