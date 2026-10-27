# ========================================================
# PRAMAAN-X Automation Makefile
# Commands for running, testing, seeding, and orchestrating
# ========================================================

PYTHON ?= python
PIP ?= pip
DOCKER_COMPOSE ?= docker compose

.PHONY: help setup run run-docker run-local test seed-data generate-data seed-registry demo-reset build down logs clean

help:
	@echo "Available commands for PRAMAAN-X:"
	@echo "  make setup       - Prepare environment: create .env and install dependencies"
	@echo "  make seed-data   - Generate synthetic data, seed issuer registry, and populate DB"
	@echo "  make demo-reset  - Restore database, issuer registry, and receipts to exact presentation state"
	@echo "  make test        - Run ALL tests in backend/tests, mock_issuer, and backend/test_api.py"
	@echo "  make run         - Start all services with Docker Compose (Postgres, Backend, Mock-Issuer, Frontend)"
	@echo "  make down        - Stop all Docker Compose services"
	@echo "  make build       - Build all Docker images"
	@echo "  make logs        - Tail live logs from all running containers"
	@echo "  make clean       - Remove cached pyc and build artifacts"

# --- Environment Setup ---
setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi
	$(PIP) install -r mock_issuer/requirements.txt
	$(PIP) install -r synthetic_generator/requirements.txt
	$(PIP) install -r backend/requirements.txt
	@echo "PRAMAAN-X environment setup complete."

# --- Docker Orchestration ---
run:
	$(DOCKER_COMPOSE) up --build

run-docker: run

build:
	$(DOCKER_COMPOSE) build

down:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f

# --- Testing & Quality Assurance ---
test:
	@echo "Running ALL automated test suites in backend/tests, mock_issuer, and test_api..."
	PYTHONPATH=. $(PYTHON) -m pytest backend/tests mock_issuer backend/test_api.py -v

test-mock-issuer:
	@echo "Running Mock Issuer statutory gateway test suite..."
	PYTHONPATH=. $(PYTHON) -m pytest mock_issuer/test_mock_issuer.py -v

benchmark-extraction:
	@echo "Running Field-Level Extraction Benchmark against Synthetic Ground Truth..."
	PYTHONPATH=. $(PYTHON) -m backend.app.services.evaluate_field_extraction

test-all: test

# --- Database Seeding & Synthetic Data Generation ---
seed-data: generate-data seed-registry seed-db
	@echo "All synthetic data generated, registries seeded, and database populated!"

seed-db:
	@echo "Populating database with synthetic AICTE benchmark data..."
	PYTHONPATH=. $(PYTHON) -m backend.app.data.seed_data

demo-reset:
	@echo "Restoring database, issuer registry, and audit receipt ledger to deterministic demo state..."
	PYTHONPATH=. $(PYTHON) -m backend.app.data.seed_data --reset
	PYTHONPATH=. $(PYTHON) mock_issuer/seed_registry.py
	@echo "PRAMAAN-X demo baseline restored successfully!"

seed-registry:
	@echo "Generating authoritative government registries from synthetic ground truth..."
	PYTHONPATH=. $(PYTHON) mock_issuer/seed_registry.py

generate-data:
	@echo "Generating synthetic regulatory dossiers for 100 institutions (Seed 42 - Tuning / Development Set)..."
	PYTHONPATH=. $(PYTHON) -m synthetic_generator.generate_synthetic_data --institutions 100 --defect-rate 0.20 --seed 42 --output-dir generated_data/seed_42
	@echo "Generating synthetic regulatory dossiers for 100 institutions (Seed 7 - Held-out Test Set)..."
	PYTHONPATH=. $(PYTHON) -m synthetic_generator.generate_synthetic_data --institutions 100 --defect-rate 0.20 --seed 7 --output-dir generated_data
	@echo "Generating infrastructure photo variants & EXIF metadata..."
	PYTHONPATH=. $(PYTHON) -m synthetic_generator.generate_photo_variants --output-dir generated_data/photos --ground-truth generated_data/ground_truth.csv

generate-photos:
	@echo "Generating infrastructure photo variants & EXIF metadata (Prompt 2.2)..."
	python -m synthetic_generator.generate_photo_variants --output-dir generated_data/photos --ground-truth generated_data/ground_truth.csv

# --- Local Standalone Runners (Zero-Docker Mode) ---
run-backend:
	uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

run-issuer:
	uvicorn mock_issuer.app.main:app --reload --host 127.0.0.1 --port 8001

run-frontend:
	cd frontend && npm run dev

# --- Cleanup ---
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/dist .pytest_cache 2>/dev/null || true
