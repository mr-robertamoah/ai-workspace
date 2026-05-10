# Security Conventions

## Secrets
- Never hardcode secrets in source or templates
- Use environment variables or secret managers

## Path Validation
- Always use `safe_path()` for user-supplied paths
- Reject traversal attempts (`../`)

## Input Sanitization
- Validate all YAML with Pydantic models
- Use `safe_load` for YAML; reject `!!python/object`
