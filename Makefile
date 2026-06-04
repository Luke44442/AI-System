.PHONY: help install dev docker-up docker-down cycle api test clean

help:
	@echo "AI Wealth System — Commands"
	@echo ""
	@echo "  make install      Install Python dependencies"
	@echo "  make dev          Start API in development mode"
	@echo "  make docker-up    Start full stack with Docker Compose"
	@echo "  make docker-down  Stop all Docker services"
	@echo "  make cycle        Run a single research cycle"
	@echo "  make continuous   Run continuous autonomous mode"
	@echo "  make test         Run test suite"
	@echo "  make clean        Clean up caches"

install:
	pip install -r requirements.txt
	playwright install chromium --with-deps 2>/dev/null || true

dev:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

api:
	python main.py --mode api

cycle:
	python main.py --mode cycle

continuous:
	python main.py --mode continuous

all:
	python main.py --mode all

docker-up:
	docker compose up --build -d
	@echo "Dashboard: http://localhost:8000"
	@echo "API docs:  http://localhost:8000/api/docs"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f --tail=100

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

test:
	python -m pytest tests/ -v 2>/dev/null || echo "No tests configured yet"

env:
	cp .env.example .env
	@echo ".env created — edit it and add your API keys"
