# scripts/setup_database.py
"""
Complete database setup script
Run with: python scripts/setup_database.py
"""
import subprocess
import sys
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not the specific database)
        server_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/postgres"
        engine = create_engine(server_url)
        
        with engine.connect() as connection:
            # Set autocommit mode
            connection = connection.execution_options(autocommit=True)
            
            # Check if database exists
            result = connection.execute(text(
                f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DB}'"
            ))
            
            if not result.fetchone():
                # Create database
                connection.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))
                print(f"✅ Database '{settings.POSTGRES_DB}' created successfully!")
            else:
                print(f"✅ Database '{settings.POSTGRES_DB}' already exists!")
                
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)

def initialize_alembic():
    """Initialize Alembic if not already initialized"""
    try:
        if not os.path.exists("alembic"):
            result = subprocess.run([
                "alembic", "init", "alembic"
            ], check=True, capture_output=True, text=True)
            print("✅ Alembic initialized successfully!")
        else:
            print("✅ Alembic already initialized!")
            
    except subprocess.CalledProcessError as e:
        print("❌ Error initializing Alembic:")
        print(e.stderr)
        sys.exit(1)

def create_migration():
    """Create initial migration"""
    try:
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", "-m", "Initial migration"
        ], check=True, capture_output=True, text=True)
        print("✅ Initial migration created!")
        
    except subprocess.CalledProcessError as e:
        print("❌ Error creating migration:")
        print(e.stderr)
        sys.exit(1)

def run_migrations():
    """Apply migrations"""
    try:
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], check=True, capture_output=True, text=True)
        print("✅ Migrations applied successfully!")
        
    except subprocess.CalledProcessError as e:
        print("❌ Error running migrations:")
        print(e.stderr)
        sys.exit(1)

def main():
    print("🚀 Setting up database...")
    
    # Step 1: Create database
    create_database()
    
    # Step 2: Initialize Alembic
    initialize_alembic()
    
    # Step 3: Create migration (if migrations folder is empty)
    migrations_exist = os.path.exists("alembic/versions") and len(os.listdir("alembic/versions")) > 0
    if not migrations_exist:
        create_migration()
    
    # Step 4: Run migrations
    run_migrations()
    
    print("🎉 Database setup complete!")

if __name__ == "__main__":
    main()