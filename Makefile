.PHONY: help install uninstall test clean lint format run

help: ## Show this help message
	@echo "EVM - Environment Variable Manager"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install EVM in development mode
	pip install -e .

install-user: ## Install EVM for the current user only
	pip install --user -e .

uninstall: ## Uninstall EVM
	pip uninstall evm-cli -y

test: ## Run tests
	python -m pytest tests/ -v

test-coverage: ## Run tests with coverage report
	python -m pytest tests/ -v --cov=evm --cov-report=html --cov-report=term

clean: ## Clean up temporary files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f evm.spec
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint: ## Run linting
	ruff check .
	mypy evm

format: ## Format code with black
	black evm tests

run: ## Run EVM with example commands
	@echo "Setting up example environment..."
	python -m evm set NODE_ENV development
	python -m evm set API_URL http://localhost:3000
	python -m evm set DEBUG true
	@echo ""
	@echo "Listing environment variables:"
	python -m evm list
	@echo ""
	@echo "Running example complete!"

demo: ## Run a full demo of EVM features
	@echo "=== EVM Demo ==="
	@echo ""
	@echo "1. Setting environment variables..."
	python -m evm set APP_NAME "EVM Demo"
	python -m evm set APP_VERSION "1.0.0"
	python -m evm set ENVIRONMENT "development"
	@echo ""
	@echo "2. Listing all variables:"
	python -m evm list
	@echo ""
	@echo "3. Getting a specific variable:"
	python -m evm get APP_NAME
	@echo ""
	@echo "4. Searching for 'APP':"
	python -m evm search APP
	@echo ""
	@echo "5. Exporting to .env format:"
	python -m evm export --format env
	@echo ""
	@echo "6. Creating backup:"
	python -m evm backup
	@echo ""
	@echo "7. Renaming variable:"
	python -m evm rename ENVIRONMENT ENV
	@echo ""
	@echo "8. Copying variable:"
	python -m evm copy APP_NAME APP
	@echo ""
	@echo "9. Final list:"
	python -m evm list
	@echo ""
	@echo "=== Demo Complete ==="
