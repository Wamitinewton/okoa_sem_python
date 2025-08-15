.PHONY: 
		install dev setup migrate seed test clean docker-build docker-run

# Install dependencies
install:
		pip install -r requirements.txt

# Run development server
dev:
		uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

prod:
		uvicorn app.main:app --host 0.0.0.0 --port $$PORT

# Complete setup (database + migrations + seed)
setup:
		PYTHONPATH=. python scripts/setup_database.py

# Run migrations only
migrate:
		PYTHONPATH=. python scripts/run_migrations.py

# Seed database with sample data
seed:
		PYTHONPATH=. python scripts/seed_data.py

# Run tests
test:
		pytest tests/ -v

# Clean up cache files
clean:
		find . -type d -name "__pycache__" -exec rm -rf {} +
		find . -type f -name "*.pyc" -delete

# Docker commands
docker-build:
		docker-compose build

docker-run:
		docker-compose up -d

docker-logs:
		docker-compose logs -f

docker-stop:
		docker-compose down

docker-clean:
		docker-compose down -v
		docker system prune -f

# Database commands
db-reset:
		docker-compose down -v
		docker-compose up -d db redis
		sleep 5
		python scripts/setup_database.py
		python scripts/seed_data.py

# Help
help:
		@echo "Available commands:"
		@echo "  install      - Install Python dependencies"
		@echo "  dev          - Run development server"
		@echo "  setup        - Complete database setup with sample data"
		@echo "  migrate      - Run database migrations"
		@echo "  seed         - Seed database with sample data"
		@echo "  test         - Run tests"
		@echo "  clean        - Clean cache files"
		@echo "  docker-build - Build Docker containers"
		@echo "  docker-run   - Run with Docker Compose"
		@echo "  docker-logs  - View Docker logs"
		@echo "  docker-stop  - Stop Docker containers"
		@echo "  db-reset     - Reset database completely"