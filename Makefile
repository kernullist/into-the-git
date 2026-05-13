.PHONY: setup run test clean lint help

# Default Python (respects virtualenv)
PYTHON := python
PIP := $(PYTHON) -m pip

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: ## Create virtual environment
	$(PYTHON) -m venv venv
	@echo "Virtualenv created. Activate with:"
	@echo "  Windows: venv\\Scripts\\activate"
	@echo "  Unix:    source venv/bin/activate"

setup: venv ## Create venv and install dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

install: ## Install project dependencies (requires active venv)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

run: ## Start development server
	$(PYTHON) app.py

test: ## Run all tests
	$(PYTHON) -m unittest discover tests -v

clean: ## Remove build artifacts and cache
	@rm -rf __pycache__/ .pytest_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf *.egg-info/ dist/ build/

clean-all: clean ## Also remove venv and data
	@rm -rf venv/ .venv/
	@rm -f data/dashboard.db

db-reset: ## Reset the database
	@rm -f data/dashboard.db
	@echo "Database reset. Restart the app to recreate."

lint: ## Run basic lint checks
	$(PYTHON) -m py_compile app.py config.py database.py models.py
	@echo "No syntax errors in core files."

check: test lint ## Run tests and lint
	@echo "All checks passed."
