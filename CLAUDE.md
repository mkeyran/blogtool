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

## Development Plan

The project follows an iterative MVP approach with 7 phases, prioritizing the most common workflow:

1. **Phase 1**: ✅ **COMPLETED** - Basic GUI + Micropost Creator (Playable MVP) - Qt window + micropost creation
2. **Phase 2**: Git Operations - commit and push workflow 
3. **Phase 3**: Content Browser Basics - view and manage existing microposts
4. **Phase 4**: Full Post Support - regular posts and conversations
5. **Phase 5**: Hugo Server Integration - preview capabilities
6. **Phase 6**: Publishing Pipeline - draft ↔ published workflow
7. **Phase 7**: Polish & Settings - configuration and UX improvements

Each phase delivers working software that provides immediate value. The order prioritizes the most frequent use case: microposts + git operations for daily blogging workflow.

### Current Status

**Phase 1 Complete**: The application now provides a working Qt GUI with micropost creation functionality:
- Qt application with menu bar and About dialog
- "New Micropost" feature (Ctrl+M) with dialog for title input and auto-slug generation
- Hugo CLI integration creating real micropost files in `content/microposts/`
- Comprehensive test coverage including unit tests and integration tests
- Clean code following PEP 8 standards with type hints and proper error handling

**Phase 2 Complete**: Git operations are now fully integrated to complete the write → publish workflow:
- Real-time git status display in status bar showing branch, changes, and unpushed commits
- Commit and push dialog (Ctrl+Shift+C) with predefined message templates for blog operations
- Automated commit message generation using `llm` tool with custom format for blog posts
- Automatic git status refresh after content creation and git operations
- Full test coverage for git functionality including unit and integration tests
- Complete micropost creation → commit → push workflow now available

**Phase 3 Complete**: Content Browser Basics now provides content management capabilities:
- MicropostBrowser widget displaying all microposts with title, date, and preview
- Smart title generation from content or filename with markdown formatting removal
- Basic actions: "Open in Editor", "Open Folder", and "Delete micropost" with confirmations
- Automatic refresh after micropost creation and deletion operations
- Comprehensive test coverage for browser functionality and Hugo micropost parsing
- Integrated into main window with real-time updates and git status synchronization

**Next Priority**: Phase 4 (Full Post Support) to extend functionality to regular posts and conversations.