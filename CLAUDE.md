# Claude Development Guide

This file contains important information for Claude about this project and the development workflow to follow.

## Project Context

This is a Qt-based Hugo blog management console designed to simplify common blog management operations. The project focuses on convenience and simplicity rather than comprehensive feature coverage.

### Key Project Constraints
- Use external editors instead of built-in editing
- Integrate with existing Hugo workflow via CLI
- Maintain file-based Hugo approach
- Focus on most common operations only
- Avoid over-engineering or feature creep

## Engineering Workflow

**ALWAYS follow this engineering workflow for every change:**

### 1. Use uv for Python Package Management
- Use `uv` for all Python package management operations
- Maintain `pyproject.toml` for dependencies
- Use `uv run` for executing scripts and tests

### 2. Small Incremental Changes
- Make small, focused changes that can be easily reviewed
- Each change should address one specific issue or feature
- Avoid large refactoring in single commits
- Keep commits atomic and well-scoped

### 3. Create Tests for Changes
- Write tests for all new functionality
- Use pytest as the testing framework
- Ensure good test coverage for core features
- Include both unit tests and integration tests where appropriate

### 4. Run All Tests
- Execute full test suite after each change
- Ensure all existing tests continue to pass
- Fix any broken tests before proceeding
- Use `uv run pytest` for test execution

### 5. Run Linters on Each Change
- Run code formatting and linting tools
- Use tools like `black`, `isort`, `flake8`, or `ruff`
- Fix all linting issues before committing
- Maintain consistent code style throughout project

### 6. Update Documentation
- Update `CLAUDE.md` with any workflow or context changes
- Update `README.md` with feature changes or usage updates
- Update any other relevant documentation
- Keep documentation current and accurate

### 7. Git Commit
- Create meaningful commit messages
- Follow conventional commit format where appropriate
- Include both summary and detailed description when needed
- Ensure commits represent complete, working changes

## Development Commands

### Testing
```bash
uv run pytest                    # Run all tests
uv run pytest -v               # Verbose test output
uv run pytest tests/test_file.py # Run specific test file
```

### Linting
```bash
uv run black .                  # Format code
uv run isort .                  # Sort imports
uv run flake8                   # Check code style
```

### Application
```bash
uv run python -m blogtool       # Run the application
```

## Project Structure Guidelines

- Keep Qt UI components modular and testable
- Separate business logic from UI code
- Use dependency injection for testability
- Follow Qt/PySide6 best practices
- Maintain clear separation of concerns

## Testing Strategy

- Test Qt components using QTest framework
- Mock external dependencies (Hugo CLI, Git, file system)
- Test user workflows end-to-end where possible
- Include edge cases and error conditions
- Maintain fast test execution times

## Code Quality Standards

- Follow PEP 8 Python style guidelines
- Use type hints throughout the codebase
- Write clear, self-documenting code
- Include docstrings for public APIs
- Handle errors gracefully with appropriate user feedback

Remember: This workflow ensures code quality, maintainability, and reliability. Never skip steps in this process.