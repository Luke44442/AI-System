.DEFAULT_GOAL := help
SHELL         := /bin/bash
COMPOSE       := docker compose
BACKEND       := $(COMPOSE) exec backend
DC_RUN        := $(COMPOSE) run --rm backend
CYAN          := \033[0;36m
RESET         := \033[0m

.PHONY: help dev build docker-up docker-down restart clean migrate seed test lint format shell-backend shell-db logs

help:
	@printf '$(CYAN)Scentara$(RESET) — available targets:\n\n'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'

check-env:
	@test -f .env || (cp .env.example .env && echo "Created .env — please fill in secrets" && exit 1)

dev: check-env docker-up ## Start all services and tail logs
	@$(COMPOSE) logs -f backend celery-worker

build: ## Build all Docker images
	$(COMPOSE) build --no-cache

docker-up: check-env ## Start all services (detached)
	$(COMPOSE) up -d --remove-orphans
	@printf "\n$(CYAN)API:$(RESET)    http://localhost:$${BACKEND_PORT:-8000}\n"
	@printf "$(CYAN)Docs:$(RESET)   http://localhost:$${BACKEND_PORT:-8000}/docs\n"
	@printf "$(CYAN)Flower:$(RESET) http://localhost:$${FLOWER_PORT:-5555}\n"

docker-down: ## Stop all services
	$(COMPOSE) down --remove-orphans

restart: ## Restart all services
	$(COMPOSE) restart

clean: ## Stop services and remove volumes (DESTRUCTIVE)
	@echo "Warning: deletes all data. Ctrl-C to abort." && sleep 3
	$(COMPOSE) down --volumes --remove-orphans

migrate: ## Apply SQL migrations to PostgreSQL
	@for f in $$(ls database/migrations/*.sql | sort); do \
		printf "$(CYAN)Applying $$f...$(RESET)\n"; \
		$(COMPOSE) exec -T postgres psql \
			-U $${POSTGRES_USER:-scentara_user} \
			-d $${POSTGRES_DB:-scentara} \
			-f /dev/stdin < $$f; \
	done

migrate-alembic: ## Run Alembic migrations
	$(BACKEND) alembic upgrade head

seed: ## Seed database with sample data
	$(BACKEND) python -m app.scripts.seed_db

test: ## Run full test suite
	$(DC_RUN) pytest tests/ --cov=app --cov-report=term-missing -x -v

lint: ## Run ruff linter
	$(BACKEND) ruff check app/ tests/

format: ## Format code with ruff
	$(BACKEND) ruff format app/ tests/

shell-backend: ## Open bash shell in backend container
	$(BACKEND) bash

shell-db: ## Open psql shell
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-scentara_user} -d $${POSTGRES_DB:-scentara}

logs: ## Tail all service logs
	$(COMPOSE) logs -f --tail=100

logs-backend: ## Tail backend logs
	$(COMPOSE) logs -f --tail=100 backend

logs-worker: ## Tail celery worker logs
	$(COMPOSE) logs -f --tail=100 celery-worker
