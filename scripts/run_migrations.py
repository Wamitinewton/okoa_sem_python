import subprocess
import sys

def run_migrations():
    try:
        # Run migrations
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Migrations applied successfully!")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print("❌ Error running migrations:")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()