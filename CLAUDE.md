# AI Development Instructions: LLM_A2Z_System

## Project Overview

**LLM_A2Z_System** - Model, train, test, use system

This project follows a staged development methodology designed for AI-assisted development. All changes must be validated before integration into the main codebase.

## Development Methodology

### Core Principles

1. **Never Trust, Always Validate** - Test all external APIs, models, and libraries in isolation before using them
2. **Staged Development** - Work in clear phases: Plan → Validate → Implement → Test
3. **Document Everything** - Keep SESSION_LOG.md current, document errors in KNOWN_ISSUES.md
4. **Pinned Dependencies** - Always pin versions and document why each dependency exists

### Project Structure

```
LLM_A2Z_System/
├── src/                    # Source code
│   ├── core/              # Core models and business logic
│   ├── providers/         # Abstract interfaces for external services
│   ├── utils/             # Utility functions
│   └── cli.py            # Entry point
├── tests/                 # Test suite
│   ├── test_core/        # Unit tests
│   └── test_integration/ # Integration tests
├── configs/              # Configuration files
└── .claude/agent_docs/   # Integration documentation
```

## Workflow Commands

### Planning
```bash
/plan [feature-description]
```
Creates a structured plan before implementation. Use this at the start of any new feature.

### Validation
```bash
/validate-integration [library-name]
```
Test external APIs/libraries in isolation before adding them to the project.

### Dependency Management
```bash
/freeze-deps
```
Update requirements.txt with current dependencies and document why each exists.

```bash
/check-compatibility [package-name]
```
Check if a new package is compatible before installing.

### Session Continuity
```bash
/save-session
```
Save current progress to SESSION_LOG.md (use at end of session).

```bash
/resume
```
Resume from last saved session.

### Error Documentation
```bash
/document-error
```
Document an error and its solution in KNOWN_ISSUES.md.

### Checkpointing
```bash
/checkpoint
```
Create a git checkpoint before risky changes.

## Integration Validation Pattern

When adding ANY external dependency:

1. **Create validation script** in `.claude/agent_docs/integrations-registry.md`
2. **Test in isolation** - Run validation before touching main code
3. **Document behavior** - Record actual vs. expected behavior
4. **Update dependencies** - Add to requirements.txt with version pin and reason

Example workflow:
```bash
/validate-integration anthropic
# Creates validation script, tests the API
# If validation passes:
pip install anthropic==0.x.x
/freeze-deps
```

## Code Organization

### Adding New Features

1. Define data models in `src/core/models.py`
2. Create abstract interfaces in `src/providers/base.py`
3. Implement providers in separate files under `src/providers/`
4. Add business logic in `src/core/`
5. Wire up CLI in `src/cli.py`

### Testing Strategy

- Unit tests in `tests/test_core/`
- Integration tests in `tests/test_integration/`
- Use pytest fixtures in `tests/conftest.py`
- Aim for high coverage on core logic

## Session Log Maintenance

Update SESSION_LOG.md after:
- Completing any feature
- Solving a difficult problem
- Before ending a session
- When switching contexts

## Known Issues

Check KNOWN_ISSUES.md before starting work. Add any new errors encountered with their solutions.

## Configuration

Default configuration in `configs/default.yaml`. Override with environment-specific configs as needed.

## Questions?

When uncertain about:
- Architecture decisions → Create a plan first (`/plan`)
- New dependencies → Validate first (`/validate-integration`)
- Breaking changes → Create checkpoint first (`/checkpoint`)
