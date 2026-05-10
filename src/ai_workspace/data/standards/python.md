# Python Conventions

## Naming
- snake_case for functions and variables
- PascalCase for classes
- UPPER_SNAKE_CASE for constants

## Structure
- Use `src/` layout with `pyproject.toml`
- One module per file; avoid circular imports

## Imports
- stdlib → third-party → local (isort enforced)
- Use `from __future__ import annotations`

## Type Hints
- All public functions must have type annotations
- Use `Optional[X]` or `X | None` for nullable

## Docstrings
- Google style for public APIs
