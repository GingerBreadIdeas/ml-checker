#!/usr/bin/env python3
"""
Simple migration script to add metrics column to chat_messages table
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/ml-checker")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if metrics column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'chat_messages' 
                AND column_name = 'metrics'
            """))
            
            if result.fetchone():
                print("✅ Metrics column already exists in chat_messages table")
                return True
            
            # Add the metrics column
            conn.execute(text("ALTER TABLE chat_messages ADD COLUMN metrics JSONB"))
            conn.commit()
            
            print("✅ Successfully added metrics column to chat_messages table")
            return True
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)