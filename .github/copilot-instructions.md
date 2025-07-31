---
applyTo: '**'
---
# Coding Standards

## General Guidelines
- Use Context7 to fetch up-to-date documentation for libraries and frameworks rather than relying on training data.
- Use English for all code, comments, documentation, and commit messages
- Write code that is easy to read and understand
- Follow the principle of least surprise; code should behave in a way that is expected
- Use descriptive names for variables, functions, and classes
- Avoid using magic numbers; use constants instead
- Follow the DRY principle (Don't Repeat Yourself)
- Keep functions small and focused on a single task.
- Use comments to explain why something is done, not how
- Use version control (Git) for all code changes
- Use consistent indentation and formatting throughout the codebase.
- Fix all ESLint issues before committing (JavaScript/TypeScript linting & formatting).
- Fix all Ruff issues before committing (Python linting & formatting).
- Fix all Pylance issues before committing (Python type checking).
## Home Assistant Guidelines
- Follow the official [Home Assistant Developer Documentation](https://developers.home-assistant.io/) as the primary reference for development.
- Use platform-specific best practices when writing custom components (e.g., for sensors, switches, services).
- Align with the Home Assistant [architecture decisions](https://developers.home-assistant.io/docs/architecture_index/) and avoid anti-patterns that contradict their standards.
- Ensure compatibility with Home Assistant’s update cycles and deprecation policies.
- Write code that can be upstreamed or reused by the Home Assistant community.
- Always refer to the latest official Home Assistant documentation instead of relying on outdated community posts or AI suggestions.
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
- No warnings should be ignored; address them appropriately
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
- Ensure automated tests run on every code change via CI/CD pipeline
## Code Reviews
- All code changes must go through peer review
- Provide meaningful descriptions in pull requests
- Review code for readability, security, and performance
- Ask for clarification rather than making assumptions
## Internationalization (i18n)
- Keep all translation files in `/translations/` up-to-date, especially `en.json`.
- Add new keys to `en.json` whenever UI text is added or changed.
- Do not remove keys without verifying their usage across the codebase.
- Use consistent key naming for translations to ensure clarity and maintainability.
