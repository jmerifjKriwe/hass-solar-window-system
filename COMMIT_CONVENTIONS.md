# Commit Message Conventions

This project uses **Conventional Commits** for automated changelog generation and versioning.

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

## Types

- **feat**: New feature (adds functionality)
- **fix**: Bug fix (fixes existing behavior)
- **docs**: Documentation changes only
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring (neither adds nor fixes)
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (build, deps, etc.)
- **ci**: CI/CD changes
- **revert**: Reverts a previous commit

## Scope

Optional - should be the area of the codebase affected:
- `coordinator`: Solar calculation coordinator
- `sensor`: Sensor entities
- `store`: Configuration storage
- `const`: Constants and configuration
- `manifest`: Integration manifest
- `config_flow`: Configuration flow
- `ci`: CI/CD workflows
- `docs`: Documentation
- `tests`: Test files

## Examples

### Good Commits
```bash
feat(coordinator): add diffuse radiation estimation
fix(sensor): resolve device info missing for window sensors
docs(readme): update installation instructions
ci(workflow): upgrade to python 3.14
chore(deps): update homeassistant to 2026.2.3
```

### Bad Commits (avoid these)
```bash
update stuff
fix bug
wip
typo fix
changes
```

## Commit Message Hook

This project includes a commit-msg hook that validates your commit messages. If your message doesn't follow the conventions, the commit will be rejected.

## For AI Agents (Claude Code, Copilot, etc.)

When creating commits, use this format:

```
type(scope): description

Detailed explanation of what was changed and why.

Footer for breaking changes or references.
```

### AI Agent Examples

**Claude Code:**
```bash
feat(coordinator): implement sun visibility calculation

Add geometric and shading calculations to determine when
direct sunlight is available through windows.

- Azimuth range checking
- Shading depth calculation
- Elevation angle validation

Fixes #42
```

**GitHub Copilot:**
```bash
fix(sensor): resolve state unavailable error

Handle missing sensor states gracefully by returning
default values instead of raising exceptions.

Closes #15
```

## Breaking Changes

If a commit introduces breaking changes, add `!` after the type/scope:

```
feat!: redesign coordinator API

BREAKING CHANGE: The coordinator interface has changed
completely. Update all integrations.
```

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Release Please](https://github.com/googleapis/release-please)
