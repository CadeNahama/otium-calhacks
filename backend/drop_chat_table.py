#!/usr/bin/env python3
"""
Drop the command_messages table from the database
"""
import os
import sys

# Add the llm-os-agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm-os-agent'))

from sqlalchemy import create_engine, text
from database import Base

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../otium.db")

print(f"Connecting to database: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)

try:
    # Drop the command_messages table if it exists
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS command_messages"))
        conn.commit()
        print("✅ Successfully dropped command_messages table")
except Exception as e:
    print(f"❌ Error dropping table: {e}")
    sys.exit(1)

print("✅ Chat table cleanup complete!")

