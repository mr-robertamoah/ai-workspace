# Testing Conventions

## Naming
- Test files: `test_<module>.py`
- Test functions: `test_<what>_<condition>`

## Fixtures
- Use `tmp_path` for filesystem tests
- Prefer function-scoped fixtures

## Coverage
- Minimum 80% overall
- 85%+ on core business logic

## Snapshot Tests
- Use for generated file content
