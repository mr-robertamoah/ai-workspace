# Module Boundaries

This document defines the allowed import relationships between packages in `src/ai_workspace/`.
These rules are enforced mechanically by ruff (`banned-module-level-imports`).

## Dependency Graph

```
cli  →  core, workspace, intelligence, security, docs
workspace  →  core
intelligence  →  core
security  →  core
docs  →  core
core  →  (nothing internal)
```

## Rules

| Package | May import | Must NOT import |
|---|---|---|
| `cli` | anything | — |
| `workspace` | `core` | `cli`, `intelligence`, `security`, `docs` |
| `intelligence` | `core` | `cli`, `workspace`, `security`, `docs` |
| `security` | `core` | `cli`, `workspace`, `intelligence`, `docs` |
| `docs` | `core` | `cli`, `workspace`, `intelligence`, `security` |
| `core` | stdlib, third-party only | any `ai_workspace.*` subpackage |

## Rationale

- `core` is the foundation — it must have zero internal dependencies so it can be tested and reasoned about in isolation.
- `security` must remain standalone so it can be audited without understanding business logic.
- `workspace` must not import `cli` — business logic must not depend on presentation.
- `intelligence` must not import `workspace` — global layer logic must not depend on per-project logic.

## Enforcement

Ruff `flake8-tidy-imports` banned imports are configured in `pyproject.toml`.
Any violation fails the lint CI job.
