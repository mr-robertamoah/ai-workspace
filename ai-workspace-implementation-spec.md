# AI Workspace CLI — Implementation Specification for AI Agents

Version: 1.1-consolidated  
Status: Implementation-Ready  
Target Platform: Ubuntu Linux (primary), general Linux (secondary)  
Language: Python 3.11+  
Architecture: Modular CLI + Local Intelligence Layer

---

## How to Use This Document

This document is the single source of truth for building `ai-workspace`. Read it fully before writing any code. When requirements appear ambiguous, follow the explicit decision rules in each section rather than guessing. Every section includes **AI Agent Notes** to resolve common implementation uncertainties.

---

## 1. What This System Is

A CLI tool that creates and maintains a structured engineering workspace so that multiple AI agents and humans can collaborate on software projects without losing context between sessions.

It solves three concrete problems:

- **Context loss**: agents re-scan repositories on every session, wasting tokens and producing inconsistent results
- **Knowledge fragmentation**: engineering patterns learned on one project are not reused on others
- **Governance gaps**: AI-generated changes enter codebases without structured review

This is NOT a coding agent, deployment platform, or CI/CD system.

---

## 2. Architecture Overview

```
Layer A — Global Intelligence (~/.ai-workspace/)
  └── Skills, standards, templates, indexes, prompts, memory, cache

Layer B — Workspace Context (<project>/.ai/)
  └── Summaries, repo maps, ADRs, active tasks, handoffs, indexes, generated artifacts

Layer C — Project Code (<project>/src, apps/, etc.)
  └── The actual application — the workspace system does not own this layer
```

**Dependency rule**: Layer B reads from Layer A. Layer C is read but never restructured by the workspace system. Layer A is global and persistent across projects.

---

## 3. Repository Structure

```
ai-workspace/                        ← the tool's own repository
├── pyproject.toml
├── README.md
├── src/
│   └── ai_workspace/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py              ← Typer app entry point
│       │   ├── init_cmd.py
│       │   ├── adopt_cmd.py
│       │   ├── validate_cmd.py
│       │   ├── index_cmd.py
│       │   ├── summarize_cmd.py
│       │   ├── skills_cmd.py
│       │   ├── docs_cmd.py
│       │   └── handoff_cmd.py
│       ├── core/
│       │   ├── config.py            ← Pydantic workspace schema
│       │   ├── paths.py             ← all path resolution logic
│       │   ├── filesystem.py        ← safe file operations
│       │   └── errors.py
│       ├── intelligence/
│       │   ├── skills.py
│       │   ├── standards.py
│       │   └── indexes.py
│       ├── workspace/
│       │   ├── generator.py         ← .ai/ scaffold generation
│       │   ├── adopter.py           ← existing project adoption
│       │   ├── summarizer.py
│       │   ├── handoff.py
│       │   └── index_builder.py
│       ├── docs/
│       │   ├── templates.py
│       │   └── creator.py
│       └── security/
│           ├── validator.py
│           └── scanner.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── snapshots/
└── scripts/
    └── install.sh
```

---

## 4. Technology Stack

| Concern | Library | Notes |
|---|---|---|
| CLI framework | `typer` | Use `typer.Typer(invoke_without_command=True)` |
| Terminal rendering | `rich` | All output via `rich.console.Console()` |
| Validation | `pydantic` v2 | Strict mode for YAML schemas |
| YAML | `ruamel.yaml` | Preserves comments; preferred over PyYAML |
| Testing | `pytest` | `pytest-cov` for coverage |
| Dependency audit | `pip-audit` | Called via subprocess |
| Static analysis | `bandit`, `ruff` | Integrated into `validate security` |
| Formatting | `black`, `isort` | Dev dependencies only |

**Python version**: 3.11+ required. Use `tomllib` (stdlib) for reading `pyproject.toml`, not a third-party library.

---

## 5. Workspace YAML Schema

The YAML file is the canonical source of truth. Interactive mode must produce a valid YAML file as output. Both modes resolve to the same internal Pydantic model.

### Full Schema

```yaml
workspace:
  name: string                      # required; kebab-case enforced
  type: monorepo | single | multi   # required

repositories:                       # required if type is monorepo or multi
  - name: string                    # kebab-case
    path: string                    # relative path from project root

language:
  primary: python | go | typescript | rust | java | other  # required
  secondary: []                     # optional list

architecture:
  style: modular-monolith | microservices | monolith | serverless | library | other

ai:
  enabled: true                     # default: true
  adr: true                         # generate ADR system; default: true
  handoffs: true                    # generate handoff templates; default: true
  tasks: true                       # generate active-task system; default: true
  agents:                           # optional; hints for agent-specific behavior
    - claude
    - codex
    - kiro

documentation:
  enabled: true                     # default: true
  structure: standard               # standard | minimal | full; default: standard

security:
  enabled: true                     # default: true
  dependency_scanning: true
  bandit: true

standards:
  testing: pytest | jest | go-test | rspec | other
  formatting: black | prettier | gofmt | other
  linting: ruff | eslint | golangci-lint | other
```

### Pydantic Model Rules

- `workspace.name`: regex `^[a-z0-9-]+$`; max 64 chars
- `repositories[].path`: must be relative (no leading `/`); normalized with `pathlib.Path`
- All string enums must be validated with `Literal` types
- Unknown fields must raise `ValidationError`, not silently ignored
- Missing required fields must produce a clear human-readable error message via Rich

---

## 6. Global Intelligence Layer (`~/.ai-workspace/`)

### Directory Structure

```
~/.ai-workspace/
├── config.yaml                     ← global tool config (version, defaults)
├── skills/
│   └── <skill-name>/
│       ├── skill.yaml              ← metadata
│       ├── templates/              ← reusable file templates
│       ├── examples/               ← usage examples
│       ├── checks/                 ← validation scripts (shell or python)
│       └── notes.md                ← human-readable notes
├── standards/
│   ├── python.md
│   ├── terraform.md
│   ├── testing.md
│   ├── documentation.md
│   └── security.md
├── templates/
│   ├── docs/
│   ├── adr/
│   └── workspace/
├── prompts/
│   └── *.md                        ← reusable agent prompts
├── memory/
│   └── *.yaml                      ← cross-project learned facts
├── embeddings/                     ← reserved; not implemented in Phase 1
├── indexes/
│   ├── skills-index.yaml
│   ├── standards-index.yaml
│   ├── templates-index.yaml
│   └── tags-index.yaml
└── cache/
    └── *.yaml
```

### Initialization

On first run of any `ai-workspace` command, if `~/.ai-workspace/` does not exist:

1. Create the full directory tree
2. Write `config.yaml` with tool version and creation timestamp
3. Seed with built-in standard skills (terraform-module, python-package, etc.)
4. Build initial global indexes
5. Print a Rich panel confirming setup

**AI Agent Note**: Never assume `~/.ai-workspace/` exists. Always call `ensure_global_layer()` at the start of every command.

---

## 7. Skill Schema

```yaml
# skill.yaml
name: terraform-module               # kebab-case; must match directory name
version: "1.0.0"                    # semver
description: |
  Standard reusable Terraform module implementation workflow.
tags:
  - terraform
  - infrastructure
  - iac
author: human | ai-proposed          # track provenance
status: active | draft | deprecated
created_at: "2025-01-01T00:00:00Z"
updated_at: "2025-01-01T00:00:00Z"
validation:
  - terraform fmt
  - terraform validate
related_skills:
  - terragrunt-module
  - helm-chart
```

### Skill Governance Rules

- AI agents may write to `~/.ai-workspace/skills/<name>-proposed/` only (suffixed directory)
- Proposed skills are visible in `skills list` with `[proposed]` tag
- `skills propose` command creates the proposed directory and opens the schema for editing
- Human runs `skills accept <name>` to rename from `<name>-proposed` to `<name>` and update indexes
- Direct writes to non-proposed skill directories must be blocked programmatically

---

## 8. Workspace Context Layer (`<project>/.ai/`)

### Full Directory Structure

```
.ai/
├── start-here.md                   ← FIRST FILE agents must read; generated on init
├── project-summary.md              ← high-level project description
├── architecture-summary.md         ← architecture decisions and patterns
├── repo-map.md                     ← directory tree with purpose annotations
├── current-state.md                ← current implementation status
│
├── indexes/
│   ├── adr-index.yaml
│   ├── task-index.yaml
│   ├── docs-index.yaml
│   └── repo-index.yaml
│
├── active-task/
│   ├── current-task.md             ← what is being built right now
│   ├── current-plan.md             ← step-by-step implementation plan
│   ├── blockers.md                 ← known blockers
│   └── next-steps.md              ← what to do after current task
│
├── handoffs/
│   └── YYYY-MM-DD-HH-MM-<slug>.md ← timestamped handoff documents
│
├── generated/
│   ├── repo-map-generated.md       ← auto-generated repo map (do not edit)
│   ├── dependency-summary.md       ← auto-generated dependency info
│   └── tech-detection.yaml         ← auto-detected technologies
│
├── context/
│   └── *.md                        ← freeform context files agents may write
│
├── templates/
│   └── *.md                        ← project-local templates (override global)
│
└── cache/
    └── *.yaml                      ← ephemeral cache; safe to delete
```

### `start-here.md` Template

This file is critical. Every agent must read it before doing anything else.

```markdown
# Start Here

Generated: {{timestamp}}
Project: {{workspace.name}}
Type: {{workspace.type}}

## What This Project Is

{{project_summary_one_liner}}

## Before You Do Anything

1. Read `project-summary.md`
2. Read `architecture-summary.md`
3. Check `active-task/current-task.md` for in-progress work
4. Query `indexes/` before scanning any directories
5. Check `handoffs/` for the most recent handoff

## Active Task

{{active_task_summary_or_none}}

## Key Architecture Decisions

See `architecture-summary.md` and `indexes/adr-index.yaml`.

## Index Locations

- ADRs: `indexes/adr-index.yaml`
- Docs: `indexes/docs-index.yaml`
- Tasks: `indexes/task-index.yaml`
- Repo: `indexes/repo-index.yaml`

## Mandatory Workflow

Do NOT skip these steps:
1. Read context (this file + summaries)
2. Query indexes
3. Clarify ambiguities before implementing
4. Plan before coding
5. Implement incrementally
6. Validate (tests + lint + security)
7. Update summaries and handoffs
8. Prepare PR summary — do NOT merge
```

---

## 9. Index Schemas

All indexes are YAML files with a consistent structure.

### `docs-index.yaml`

```yaml
generated_at: "2025-01-01T00:00:00Z"
docs:
  - id: arch-overview
    title: Architecture Overview
    path: docs/architecture/architecture-overview.md
    tags: [architecture, overview]
    purpose: Describe system architecture
    last_modified: "2025-01-01T00:00:00Z"
    summary: "One sentence summary of document contents."
```

### `adr-index.yaml`

```yaml
generated_at: "2025-01-01T00:00:00Z"
adrs:
  - id: ADR-001
    title: Use PostgreSQL as primary database
    path: docs/decisions/ADR-001-postgresql.md
    status: accepted | proposed | deprecated | superseded
    date: "2025-01-01"
    tags: [database, infrastructure]
    superseded_by: null
```

### `task-index.yaml`

```yaml
generated_at: "2025-01-01T00:00:00Z"
tasks:
  - id: TASK-001
    title: Implement authentication service
    status: active | complete | blocked | proposed
    started_at: "2025-01-01T00:00:00Z"
    completed_at: null
    path: .ai/active-task/current-task.md
    tags: [auth, backend]
```

### `repo-index.yaml`

```yaml
generated_at: "2025-01-01T00:00:00Z"
repositories:
  - name: orchestrator
    path: apps/orchestrator
    language: python
    purpose: "Orchestrates workflow execution"
    entry_points:
      - apps/orchestrator/src/main.py
    key_directories:
      - path: apps/orchestrator/src
        purpose: Application source
      - path: apps/orchestrator/tests
        purpose: Test suite
```

---

## 10. Handoff Document Schema

A handoff is generated by `ai-workspace handoff generate` and written to `.ai/handoffs/`.

```markdown
# Handoff — {{slug}}

Generated: {{timestamp}}
Agent: {{agent_name_or_human}}
Session duration: {{duration_or_unknown}}

## What Was Accomplished

{{bullet list of completed work}}

## Current State

{{where the codebase is right now}}

## Active Task Status

- Task: {{current_task_title}}
- Plan step reached: Step {{N}} of {{M}}
- Blockers: {{blockers_or_none}}

## What Was NOT Done

{{explicit list of incomplete work — never omit this}}

## Next Steps

{{ordered list of recommended next actions}}

## Tests Passing

{{yes/no + which test command was run}}

## Files Modified

{{list of files changed in this session}}

## Decisions Made

{{any architecture or implementation decisions, with rationale}}

## References

{{links to relevant ADRs, docs, specs}}
```

---

## 11. CLI Commands — Full Specification

All commands use `rich` for output. Use `Console().print()` — never `print()`.

### `ai-workspace init`

**Interactive mode** (no flags): prompt user for all required fields, then write `workspace.yaml`, then generate `.ai/` scaffold.

**YAML mode** (`-f workspace.yaml`): validate YAML, then generate scaffold.

**Behavior**:
1. Validate no `.ai/` already exists (or prompt to overwrite)
2. Write `workspace.yaml` to project root
3. Generate full `.ai/` structure with template files
4. Generate `docs/` structure if `documentation.enabled: true`
5. Build initial local indexes (mostly empty at this stage)
6. Print success summary with Rich panel listing created files

**Flags**:
- `-f / --file PATH`: path to workspace YAML
- `--dry-run`: show what would be created without writing
- `--existing`: adoption mode (see `adopt` command)
- `--force`: overwrite existing `.ai/` without prompting

### `ai-workspace adopt`

For existing repositories. Does NOT restructure the project.

**Behavior**:
1. Analyze repository (see Section 12)
2. Write analysis to `.ai/generated/tech-detection.yaml`
3. Generate `.ai/` context files populated with detected info
4. Generate `start-here.md` with detected project summary
5. Suggest (but do NOT create) documentation files
6. Build initial indexes from existing docs
7. Print diff-style summary of what was created vs suggested

**Safety rules**:
- Never modify files outside `.ai/` and `docs/` (and only suggest `docs/` changes)
- If `.ai/` already exists, prompt before overwriting any file
- Always support `--dry-run`

### `ai-workspace validate`

Checks workspace health.

**Checks performed**:
1. `workspace.yaml` exists and is valid against schema
2. `.ai/` directory exists with required files
3. `start-here.md` exists and is not empty
4. All index files exist and are valid YAML
5. Index entries reference files that exist on disk
6. No stale handoffs (>30 days old, no newer handoff)
7. Active task file is populated if `ai.tasks: true`

**Output**: Rich table showing check name, status (✓/✗/⚠), and message.

### `ai-workspace validate security`

Checks security posture. Runs independently from `validate`.

**Checks performed**:
1. Run `pip-audit` on project dependencies
2. Run `bandit -r src/` on Python source
3. Check workspace YAML for suspicious content (shell injection patterns)
4. Check generated templates for hardcoded secrets (regex: `password\s*=\s*["\'][^"\']+["\']`, API key patterns)
5. Validate file permissions on `.ai/` (no world-writable files)
6. Check `pip-audit` exit code and surface CVEs

**Output**: Rich table per check with severity (INFO/WARN/CRITICAL).

### `ai-workspace index rebuild`

Rebuilds all local indexes from scratch.

**Behavior**:
1. Scan `docs/` for markdown files and build `docs-index.yaml`
2. Scan `docs/decisions/` for ADR files and build `adr-index.yaml`
3. Scan `.ai/active-task/` and build `task-index.yaml`
4. Scan configured repository paths and build `repo-index.yaml`
5. Update `generated_at` timestamps on all indexes
6. Print count of indexed items per index

**AI Agent Note**: This command is safe to run repeatedly. It is not destructive — it overwrites indexes with fresh data from disk.

### `ai-workspace summarize`

Generates or refreshes summary files in `.ai/`.

**Files generated/updated**:
- `.ai/generated/repo-map-generated.md`: directory tree with file counts
- `.ai/generated/dependency-summary.md`: parsed from `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, etc.
- `.ai/generated/tech-detection.yaml`: detected languages, frameworks, CI systems

**Does NOT overwrite**:
- `project-summary.md` (human-owned)
- `architecture-summary.md` (human-owned)
- `current-state.md` (human-owned)

### `ai-workspace skills list`

Lists all available skills from `~/.ai-workspace/skills/`.

**Output**: Rich table with columns: Name, Status, Tags, Description (truncated at 60 chars).

### `ai-workspace skills search <query>`

Searches skill names, descriptions, and tags. Case-insensitive substring match initially; regex optional.

### `ai-workspace skills show <name>`

Prints full skill details including `skill.yaml` content and available templates.

### `ai-workspace skills propose`

Interactive prompt to create a new proposed skill in `~/.ai-workspace/skills/<name>-proposed/`.

### `ai-workspace docs templates`

Lists available documentation templates from global and local template stores.

### `ai-workspace docs create <template-name>`

Creates a new document from a template at the appropriate path under `docs/`.

Example: `ai-workspace docs create architecture-overview` creates `docs/architecture/architecture-overview.md`.

### `ai-workspace handoff generate`

Generates a handoff document interactively.

Prompts for:
- What was accomplished
- Current state
- Blockers
- Next steps
- Tests passing (y/n)

Writes to `.ai/handoffs/YYYY-MM-DD-HH-MM-<slugified-task-name>.md`.

---

## 12. Repository Adoption — Detection Logic

When `adopt` or `init --existing` is run, the system must detect the following without executing any project code.

### Language Detection (in order of priority)

| Signal | Language |
|---|---|
| `pyproject.toml` or `requirements.txt` | Python |
| `package.json` | Node.js / TypeScript |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml` or `build.gradle` | Java |
| `*.tf` files | Terraform (IaC) |

### Framework Detection

| Signal | Framework |
|---|---|
| `fastapi` in `requirements.txt` | FastAPI |
| `django` in `requirements.txt` | Django |
| `express` in `package.json` | Express.js |
| `next` in `package.json` | Next.js |
| `provider` blocks in `*.tf` | Terraform |

### CI/CD Detection

| Signal | System |
|---|---|
| `.github/workflows/` exists | GitHub Actions |
| `.gitlab-ci.yml` exists | GitLab CI |
| `Jenkinsfile` exists | Jenkins |
| `.circleci/` exists | CircleCI |

### Fallback Behavior

If nothing is detected, set `language.primary: other` and log a warning. Never fail — always produce a partial detection result.

---

## 13. Documentation System

### Standard Structure

```
docs/
├── architecture/
│   └── architecture-overview.md
├── api/
├── infrastructure/
├── workflows/
├── onboarding/
│   └── getting-started.md
├── runbooks/
├── product/
└── decisions/
    └── ADR-001-<title>.md
```

### Document Metadata Header

All generated documents must begin with this YAML front matter:

```yaml
---
title: Architecture Overview
created_at: "2025-01-01T00:00:00Z"
last_modified: "2025-01-01T00:00:00Z"
purpose: Describe the system architecture for human and AI readers
tags:
  - architecture
used_by:
  - architecture-summary-generator
  - onboarding-system
status: draft | current | outdated
---
```

### ADR Naming Convention

`ADR-<zero-padded-number>-<kebab-title>.md`

Example: `ADR-001-use-postgresql.md`

### ADR Template

```markdown
---
title: "ADR-001: Use PostgreSQL as primary database"
date: YYYY-MM-DD
status: proposed | accepted | deprecated | superseded
superseded_by: null
tags: [database, infrastructure]
---

# ADR-001: Use PostgreSQL as primary database

## Context

What is the problem or situation that requires a decision?

## Decision

What was decided?

## Rationale

Why was this decision made over alternatives?

## Consequences

What are the positive and negative consequences of this decision?

## Alternatives Considered

- Alternative A: why it was not chosen
- Alternative B: why it was not chosen
```

---

## 14. Security Implementation

### Path Validation (mandatory on all file operations)

```python
from pathlib import Path

def safe_path(base: Path, user_input: str) -> Path:
    """Resolve user-provided path, reject traversal attempts."""
    resolved = (base / user_input).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise ValueError(f"Path traversal attempt blocked: {user_input}")
    return resolved
```

Apply `safe_path()` everywhere a user-supplied string is joined to a base directory.

### YAML Validation

- Use `ruamel.yaml` with `safe_load` equivalent (no `yaml.load()` without Loader)
- Validate all loaded YAML through Pydantic models before use
- Reject YAML containing `!!python/object` tags

### Secret Detection Patterns

```python
SECRET_PATTERNS = [
    r'password\s*=\s*["\'][^"\']{4,}["\']',
    r'api_key\s*=\s*["\'][^"\']{8,}["\']',
    r'secret\s*=\s*["\'][^"\']{8,}["\']',
    r'token\s*=\s*["\'][^"\']{16,}["\']',
    r'AKIA[0-9A-Z]{16}',             # AWS key pattern
    r'ghp_[a-zA-Z0-9]{36}',          # GitHub token pattern
]
```

### Dangerous Actions Requiring Confirmation

These must prompt `[y/N]` (default no) before proceeding:
- `init --force` (overwriting existing `.ai/`)
- Any file deletion
- `index rebuild` on a non-empty index (warn, don't block)

Always support `--yes` / `-y` flag to skip prompts for CI use.

---

## 15. Error Handling

### Error Classes

```python
class WorkspaceError(Exception):
    """Base error for all workspace operations."""

class WorkspaceNotFoundError(WorkspaceError):
    """No .ai/ or workspace.yaml found in current directory."""

class ValidationError(WorkspaceError):
    """YAML schema validation failed."""

class SecurityError(WorkspaceError):
    """Security check failed — path traversal, secrets, etc."""

class SkillError(WorkspaceError):
    """Skill operation failed."""
```

### Output Format

All errors must be shown via Rich with a red `[ERROR]` prefix. Validation errors must show the specific field and value that failed. Never show raw Python tracebacks to users — catch at CLI boundary and show clean messages.

---

## 16. Testing Requirements

### Minimum Coverage: 80%

### Unit Tests Required For

- `config.py`: all Pydantic schema validations (valid and invalid inputs)
- `filesystem.py`: path safety checks, directory creation, file writes
- `index_builder.py`: index generation from fixture files
- `summarizer.py`: tech detection logic against fixture repositories
- `validator.py`: all security patterns and checks
- `adopter.py`: detection heuristics per language/framework

### Integration Tests Required For

- Full `init` flow: from YAML to generated `.ai/` structure
- Full `adopt` flow: against a fixture repository
- `index rebuild`: from populated docs directory to valid index
- `validate`: against a known-good and known-bad workspace

### Security Tests Required For

- Path traversal: `../../etc/passwd` style inputs
- Malicious YAML: `!!python/object` tags
- Secret detection: files containing fake API keys
- Invalid permissions: world-writable fixture files

### Snapshot Tests Recommended For

- Generated `start-here.md` content
- Generated `docs-index.yaml` from a fixture docs directory
- Terminal output of `skills list`

### Test Fixture Strategy

Create minimal fixture repositories in `tests/fixtures/`:
- `fixtures/greenfield/`: empty project with only `workspace.yaml`
- `fixtures/python-api/`: a small FastAPI project structure (no real code, just directory shape)
- `fixtures/monorepo/`: two-app monorepo structure
- `fixtures/no-docs/`: repo with no documentation at all (tests adoption fallbacks)

---

## 17. Implementation Phases — Dependency-Corrected Order

### Phase 1 — Foundation

Deliver:
- `pyproject.toml` with all dependencies pinned
- Typer CLI skeleton with all commands registered (returning `NotImplemented` stubs)
- `core/paths.py` with safe path resolution
- `core/filesystem.py` with safe file/directory operations
- `core/config.py` with full Pydantic workspace schema
- `core/errors.py` with error hierarchy
- Global layer initialization (`~/.ai-workspace/` setup)
- `validate` command (schema only, no file checks yet)
- Full unit tests for `config.py` and `paths.py`

**Exit criteria**: `ai-workspace --help` works, `ai-workspace validate` validates a YAML file.

### Phase 2 — Workspace Generation

Deliver:
- `workspace/generator.py`: full `.ai/` scaffold generation
- All template files for `.ai/` context files
- `init` command: interactive mode + YAML mode
- `docs/` structure generation
- ADR template generation
- Unit tests for generator

**Exit criteria**: `ai-workspace init` creates a complete, valid `.ai/` structure.

### Phase 3 — Indexing System

Deliver:
- `workspace/index_builder.py`: builds all four local indexes
- `intelligence/indexes.py`: global index management
- `index rebuild` command
- Index schema validation
- Unit and integration tests for indexing

**Exit criteria**: `ai-workspace index rebuild` produces valid, queryable indexes.

### Phase 4 — Existing Project Adoption

Deliver:
- `workspace/adopter.py`: detection logic for all languages/frameworks
- `adopt` command with dry-run support
- `generated/tech-detection.yaml` generation
- `generated/repo-map-generated.md` generation
- Integration tests against fixture repositories

**Exit criteria**: `ai-workspace adopt` works on a Python FastAPI project fixture.

### Phase 5 — Summarization

Deliver:
- `workspace/summarizer.py`
- `summarize` command
- `generated/dependency-summary.md` generation
- Tech detection integration into `start-here.md`

### Phase 6 — Skills System

Deliver:
- `intelligence/skills.py`: skill loading, indexing, search
- All `skills` subcommands
- Skill proposal workflow with governance enforcement
- Global skills index rebuild

### Phase 7 — Security and Validation

Deliver:
- `security/validator.py`: all checks
- `security/scanner.py`: `pip-audit` and `bandit` integration
- `validate security` command
- Secret detection patterns
- Security unit and integration tests

### Phase 8 — Docs, README, Packaging

Deliver:
- `docs` subcommands
- `handoff generate` command
- Full `README.md` (see Section 18)
- `pyproject.toml` packaging configuration
- `scripts/install.sh`
- Snapshot tests
- Coverage enforcement in CI

---

## 18. README Requirements

The README must include all of the following sections:

```
# AI Workspace CLI

## Overview
## Features
## Installation
  ### pip install
  ### Development install (editable)
## Quick Start
  ### Initialize a new project
  ### Adopt an existing project
  ### Rebuild indexes
  ### Generate a handoff
## Architecture
  ### Global Intelligence Layer
  ### Workspace Context Layer
  ### Indexing System
  ### Skills System
## Agent Workflow
  ### Mandatory steps
  ### How to read context
  ### How to query indexes
## Security Model
## Development
  ### Running tests
  ### Code style
  ### Contributing
## Uninstallation
```

---

## 19. Mandatory Agent Workflow (for AI agents using the system)

When an AI agent opens a project that uses `ai-workspace`:

1. **Read** `.ai/start-here.md` — mandatory, no exceptions
2. **Read** `.ai/active-task/current-task.md` — if `ai.tasks: true`
3. **Read** the most recent file in `.ai/handoffs/` — if any exist
4. **Query** `.ai/indexes/` before scanning any directory
5. **Clarify** — if architecture is unclear, blocked, or requirements conflict: ask, do not guess
6. **Plan** — write a step-by-step plan to `.ai/active-task/current-plan.md` before coding
7. **Implement** — small, incremental changes only
8. **Validate** — run tests, lint, and `ai-workspace validate` before finishing
9. **Update** — refresh `current-state.md`, task index, and any relevant summaries
10. **Handoff** — run `ai-workspace handoff generate` before ending session
11. **PR only** — never merge; prepare PR description with: what changed, why, test results

**AI agents must never**:
- Scan repository recursively when an index exists
- Modify files in `~/.ai-workspace/skills/` without human approval
- Merge pull requests
- Execute shell commands from workspace templates
- Skip the handoff step

---

## 20. Gap Resolution Decisions

These are explicit decisions for implementation ambiguities in the source specifications.

| Gap | Decision |
|---|---|
| How does summarization know when to re-run? | On demand only via `ai-workspace summarize`. No auto-trigger. |
| What if `pip-audit` is not installed? | Log a warning, skip that check, do not fail the command. |
| What if `.ai/` exists and `init` is re-run? | Prompt user. Only overwrite with `--force`. Never silently overwrite. |
| How are indexes kept fresh? | Manual `index rebuild`. Future phases may add file-watch support. |
| What is the handoff filename format? | `YYYY-MM-DD-HH-MM-<current-task-slug>.md` |
| What if no `active-task` exists? | `start-here.md` shows "No active task" — not an error. |
| What is `documentation: structure: minimal`? | Creates only `docs/architecture/` and `docs/decisions/`. |
| What is `documentation: structure: full`? | Creates all eight `docs/` subdirectories. |
| Should `validate` fail on stale indexes? | Warn only (⚠), not fail (✗). Indexes being stale is common. |
| Where do agent-written context files go? | `.ai/context/` — freeform, not indexed automatically. |
| Can two projects share the same `~/.ai-workspace/`? | Yes — that is the design intent. Skills and standards are global. |

---

## 21. Non-Goals (explicitly out of scope for this build)

- Autonomous deployment or production execution
- Cloud orchestration or Kubernetes management
- Running AI models or hosting LLMs
- CI/CD pipeline execution
- Real-time collaboration between agents
- Embeddings or semantic search (reserved for future phases)
- Windows or macOS support (Linux only initially)
- Web UI or Textual TUI (CLI only)
- Auto-merging pull requests under any circumstances
