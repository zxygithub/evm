.PHONY: help install uninstall test clean lint format run build-macos install-macos

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
	rm -rf evm-cli-macos/
	rm -f evm-cli-macos.tar.gz
	rm -f evm.spec
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint: ## Run linting
	flake8 evm tests
	mypy evm

format: ## Format code with black
	black evm tests

run: ## Run EVM with example commands
	@echo "Setting up example environment..."
	python -m evm.python set NODE_ENV development
	python -m evm.python set API_URL http://localhost:3000
	python -m evm.python set DEBUG true
	@echo ""
	@echo "Listing environment variables:"
	python -m evm.python list
	@echo ""
	@echo "Running example complete!"

demo: ## Run a full demo of EVM features
	@echo "=== EVM Demo ==="
	@echo ""
	@echo "1. Setting environment variables..."
	python -m evm.python set APP_NAME "EVM Demo"
	python -m evm.python set APP_VERSION "1.0.0"
	python -m evm.python set ENVIRONMENT "development"
	@echo ""
	@echo "2. Listing all variables:"
	python -m evm.python list
	@echo ""
	@echo "3. Getting a specific variable:"
	python -m evm.python get APP_NAME
	@echo ""
	@echo "4. Searching for 'APP':"
	python -m evm.python search APP
	@echo ""
	@echo "5. Exporting to .env format:"
	python -m evm.python export --format env
	@echo ""
	@echo "6. Creating backup:"
	python -m evm.python backup
	@echo ""
	@echo "7. Renaming variable:"
	python -m evm.python rename ENVIRONMENT ENV
	@echo ""
	@echo "8. Copying variable:"
	python -m evm.python copy APP_NAME APP
	@echo ""
	@echo "9. Final list:"
	python -m evm.python list
	@echo ""
	@echo "=== Demo Complete ==="

# macOS 构建目标
build-macos: ## Build standalone macOS executable
	@echo "Building macOS standalone executable..."
	bash build_macos.sh

install-macos: ## Install EVM on macOS from source
	@echo "Installing EVM on macOS..."
	bash install_macos.sh
