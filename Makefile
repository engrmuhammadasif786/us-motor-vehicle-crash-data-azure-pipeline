.PHONY: help install up down pipeline dbt-build dbt-test dashboard infra-preview infra-up test lint clean

SHELL := /bin/bash

UV_BIN := $(shell command -v uv 2>/dev/null)
PYTHON_CMD := $(if $(UV_BIN),uv run python,python3)
DBT_CMD := $(if $(UV_BIN),uv run dbt,dbt)
STREAMLIT_CMD := $(if $(UV_BIN),uv run streamlit,streamlit)

load_env = set -a; source ./.env; set +a;

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all Python dependencies
	pip install -e ".[all]"

up: ## Start local services (Azurite, Prefect)
	docker compose up -d

down: ## Stop local services
	docker compose down

pipeline: ## Run the Prefect pipeline locally
	@$(call load_env) $(PYTHON_CMD) -m pipelines.prefect.flows

dbt-build: ## Run dbt models
	@$(call load_env) cd dbt && $(DBT_CMD) build --target $(DBT_TARGET)

dbt-test: ## Run dbt tests only
	@$(call load_env) cd dbt && $(DBT_CMD) test --target $(DBT_TARGET)

dashboard: ## Launch Streamlit dashboard
	@$(call load_env) $(STREAMLIT_CMD) run dashboards/streamlit/app.py

infra-preview: ## Preview Pulumi infrastructure changes
	cd infrastructure/pulumi && pulumi preview

infra-up: ## Deploy Pulumi infrastructure
	cd infrastructure/pulumi && pulumi up

test: ## Run Python tests
	pytest tests/ -v

lint: ## Run linters and formatters
	black .
	ruff check . --fix
	mypy pipelines/ infrastructure/

clean: ## Clean temporary files and Docker volumes
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name dbt_packages -exec rm -rf {} +
	find . -type d -name target -exec rm -rf {} +
