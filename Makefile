.PHONY: help install dev-install test lint format type-check clean run

help:
	@echo "Available commands:"
	@echo "  install     - Install the package"
	@echo "  dev-install - Install with development dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting (flake8)"
	@echo "  format      - Format code (black + isort)"
	@echo "  type-check  - Run type checking (mypy)"
	@echo "  clean       - Clean build artifacts"
	@echo "  run         - Run the application"

install:
	uv sync

dev-install:
	uv sync --extra dev

test:
	uv run pytest

lint:
	uv run flake8 blogtool tests

format:
	uv run black blogtool tests
	uv run isort blogtool tests

type-check:
	uv run mypy blogtool

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	uv run blogtool