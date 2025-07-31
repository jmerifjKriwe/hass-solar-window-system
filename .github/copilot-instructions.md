---
applyTo: '**'
---
# Coding Standards

## General Guidelines
- Use Context7 to fetch up-to-date documentation for libraries and frameworks rather than relying on training data.
- Use english language for all code, comments, documentation and commit messages.
- Write code that is easy to read and understand
- Follow the principle of least surprise; code should behave in a way that is expected
- Use descriptive names for variables, functions, and classes
- Avoid using magic numbers; use constants instead
- Keep code DRY (Don't Repeat Yourself); avoid duplication
- Keep functions small and focused on a single task.
- Use comments to explain why something is done, not what is done
- Use version control (Git) for all code changes
- Use consistent indentation and formatting throughout the codebase.
- Use ESLint or Prettier for code formatting and linting.
## Naming Conventions
- Use PascalCase for component names, interfaces, and type aliases
- Use camelCase for variables, functions, and methods
- Prefix private class members with underscore (_)
- Use ALL_CAPS for constants
## Code Structure
- Organize code into modules or packages based on functionality
- Use a consistent file structure across the project
- Keep related files together (e.g., components, styles, tests)
## Error Handling
- Use try/catch blocks for async operations
- Always log errors with contextual information
- Use custom error classes for specific error types
- Avoid swallowing errors silently
- Provide user-friendly error messages
## Documentation
- Use docstrings for all public functions, classes, and methods
- Use Markdown for README files and documentation
- Keep documentation up-to-date with code changes
- Use comments to explain complex logic or important decisions
## Testing
- Write unit tests for all new features and bug fixes
- Use a consistent testing framework (pytest)
- Use fixtures for setup and teardown of test environments
- Use mocks for external dependencies in tests
- Ensure tests cover both happy path and edge cases
- Run tests automatically on code changes (CI/CD)