"""
Script to create the initial database migration
Run with: python scripts/create_initial_migration.py
"""
import subprocess
import sys
import os

def create_migration():
    try:
        # Create initial migration
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", "-m", "Initial migration"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Initial migration created successfully!")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print("❌ Error creating migration:")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    create_migration()
