"""
Script to check the structure of the user table.
"""
import asyncio
import os
import sys
from sqlalchemy import text

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db

async def check_user_table():
    """Check the structure of the user table."""
    print("Checking user table structure...")
    
    async for db in get_db():
        try:
            # Get columns in user table
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'user'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print("\nColumns in user table:")
            print("-" * 60)
            print(f"{'Column':<20} {'Type':<20} {'Nullable':<10}")
            print("-" * 60)
            for col in columns:
                print(f"{col[0]:<20} {col[1]:<20} {col[2]:<10}")
            
            # Also check if there are any users
            result = await db.execute(text("""
                SELECT id, email, is_active, is_superuser 
                FROM "user" 
                LIMIT 5
            """))
            users = result.fetchall()
            
            if users:
                print("\nSample users:")
                print("-" * 60)
                print(f"{'ID':<5} {'Email':<30} {'Active':<8} {'Superuser':<10}")
                print("-" * 60)
                for user in users:
                    print(f"{user[0]:<5} {user[1]:<30} {str(user[2]):<8} {str(user[3]):<10}")
            else:
                print("\nNo users found in the database.")
            
            break
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    asyncio.run(check_user_table()) 