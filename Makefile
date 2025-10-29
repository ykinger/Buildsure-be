.PHONY: help install run dev test test-verbose test-cov migrate makemigrations clean

# Default target
help:
	@echo "BuildSure API     - Available Commands"
	@echo "======================================="
	@echo "make install      - Install dependencies"
	@echo "make run          - Run server (production mode)"
	@echo "make dev          - Run server with auto-reload (development mode)"
	@echo "make test         - Run all tests"
	@echo "make test-verbose - Run tests with verbose output"
	@echo "make test-cov     - Run tests with coverage report"
	@echo "make clean        - Remove cache files and databases"

# Install dependencies
install:
	pip install -r requirements.txt

# Run server in production mode
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run server in development mode with auto-reload
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest

# Run tests with verbose output
test-verbose:
	pytest -v

# Run tests with coverage
test-cov:
	pytest --cov=app --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Apply database migrations
migrate:
	alembic upgrade head

# Create a new migration
makemigrations:
	alembic revision --autogenerate -m "$(message)"

# Clean cache and test files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -f test*.db buildsure.db
	rm -rf htmlcov/
	rm -f .coverage
	@echo "Cleaned cache files and test databases"
