"""
Script to check database tables.
"""
import asyncio
import os
import sys
from sqlalchemy import text

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db

async def check_tables():
    """Check database tables."""
    print("Checking database tables...")
    
    async for db in get_db():
        try:
            # Get list of tables
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.scalars().all()
            
            print("\nTables in database:")
            print("-" * 40)
            for table in tables:
                print(f"- {table}")
            
            # Check if llm_analytics table exists
            if 'llm_analytics' in tables:
                # Get columns in llm_analytics table
                result = await db.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'llm_analytics'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                print("\nColumns in llm_analytics table:")
                print("-" * 60)
                print(f"{'Column':<20} {'Type':<20} {'Nullable':<10}")
                print("-" * 60)
                for col in columns:
                    print(f"{col[0]:<20} {col[1]:<20} {col[2]:<10}")
            else:
                print("\nllm_analytics table not found!")
            
            break
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    asyncio.run(check_tables()) 