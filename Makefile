# ========================================================
# PRAMAAN-X Automation Makefile
# Commands for running, testing, seeding, and orchestrating
# ========================================================

PYTHON ?= python
PIP ?= pip
DOCKER_COMPOSE ?= docker compose

.PHONY: help run run-docker run-local test seed-data build down logs clean

help:
	@echo "Available commands for PRAMAAN-X:"
	@echo "  make run         - Start all services with Docker Compose (Postgres, Backend, Mock-Issuer, Frontend)"
	@echo "  make down        - Stop all Docker Compose services"
	@echo "  make test        - Run backend API test suite"
	@echo "  make seed-data   - Seed database with synthetic benchmark colleges, documents, and audit chains"
	@echo "  make build       - Build all Docker images"
	@echo "  make logs        - Tail live logs from all running containers"
	@echo "  make run-backend - Run FastAPI backend locally"
	@echo "  make run-issuer  - Run Mock Issuer FastAPI service locally"
	@echo "  make run-frontend- Run React Vite frontend locally"
	@echo "  make clean       - Remove cached pyc and build artifacts"

# --- Docker Orchestration ---
run:
	$(DOCKER_COMPOSE) up -d --build

run-docker: run

build:
	$(DOCKER_COMPOSE) build

down:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f

# --- Testing & Quality Assurance ---
test:
	@echo "Running PRAMAAN-X comprehensive automated test suite (Phase 1-5)..."
	python -m pytest backend/tests/test_phase5.py backend/tests/test_rules_engine.py backend/test_api.py -v

test-mock-issuer:
	@echo "Running Mock Issuer statutory gateway test suite..."
	python -m pytest mock_issuer/test_mock_issuer.py -v

benchmark-extraction:
	@echo "Running Field-Level Extraction Benchmark against Synthetic Ground Truth (Prompt 5.2)..."
	python -m backend.app.services.evaluate_field_extraction

test-all: test test-mock-issuer

# --- Database Seeding & Synthetic Data Generation ---
seed-data:
	@echo "Populating database with synthetic AICTE benchmark data..."
	python -m backend.app.data.seed_data

seed-registry:
	@echo "Generating authoritative government registries from synthetic ground truth..."
	python mock_issuer/seed_registry.py

generate-data:
	@echo "Generating synthetic regulatory dossiers & ground-truth defects (Prompt 2.1)..."
	python -m synthetic_generator.generate_synthetic_data --institutions 20 --defect-rate 0.20 --seed 42 --output-dir generated_data

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
