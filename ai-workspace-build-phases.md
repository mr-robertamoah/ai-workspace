# AI Workspace CLI — Build Phases

Version: 1.0  
Companion to: `ai-workspace-implementation-spec.md`  
By the end of Phase 8, the tool is fully built and installable.

---

## How to Use This Document

Each phase has:
- **Goal** — what this phase delivers and why it exists
- **Tasks** — ordered list of what to build, specific enough to start coding
- **Tests** — what must be tested before the phase is considered done
- **Commit checkpoint** — what to commit and what the commit message should look like
- **Definition of Done** — binary checklist; all items must be true before moving to the next phase

Work through tasks in order within each phase. Do not begin the next phase until every Definition of Done item is checked. Run the full test suite before every commit.

---

## Pre-Phase: Repository Bootstrap

Before any phase begins, the repository itself must exist in a clean, installable state.

### Tasks

1. Create the repository directory: `ai-workspace/`
2. Create `pyproject.toml` with the following content:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "ai-workspace"
version = "0.1.0"
description = "AI-native engineering workspace CLI"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "rich>=13",
    "pydantic>=2.7",
    "ruamel.yaml>=0.18",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov>=5",
    "black>=24",
    "isort>=5",
    "ruff>=0.4",
    "bandit>=1.7",
]

[project.scripts]
ai-workspace = "ai_workspace.cli.main:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src/ai_workspace --cov-report=term-missing"

[tool.coverage.run]
branch = true

[tool.ruff]
line-length = 100

[tool.black]
line-length = 100
```

3. Create the full source directory tree (empty `__init__.py` files in each package):

```
src/
└── ai_workspace/
    ├── __init__.py
    ├── cli/
    │   └── __init__.py
    ├── core/
    │   └── __init__.py
    ├── intelligence/
    │   └── __init__.py
    ├── workspace/
    │   └── __init__.py
    ├── docs/
    │   └── __init__.py
    └── security/
        └── __init__.py
tests/
├── __init__.py
├── unit/
│   └── __init__.py
├── integration/
│   └── __init__.py
├── security/
│   └── __init__.py
└── fixtures/
    ├── greenfield/
    │   └── workspace.yaml
    ├── python-api/
    │   ├── workspace.yaml
    │   ├── pyproject.toml
    │   ├── requirements.txt
    │   ├── src/
    │   │   └── main.py
    │   └── tests/
    ├── monorepo/
    │   ├── workspace.yaml
    │   ├── apps/
    │   │   ├── api/
    │   │   └── worker/
    └── no-docs/
        ├── workspace.yaml
        └── src/
```

4. Create `.gitignore`:

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.coverage
htmlcov/
.pytest_cache/
.ruff_cache/
```

5. Install in editable mode: `pip install -e ".[dev]"`
6. Verify: `python -m pytest tests/` passes (no tests yet, but must not error)
7. Verify: `ai-workspace --help` errors with `No such command` or similar (entry point resolves)

### Commit

```
git init
git add .
git commit -m "bootstrap: repository structure and pyproject.toml"
```

---

## Phase 1 — Core Foundation

**Goal**: The non-negotiable base that every other phase builds on. Safe path handling, the Pydantic workspace schema, the error hierarchy, and a working CLI skeleton. Nothing is fully functional yet, but the structure is correct and tested.

---

### Task 1.1 — Error Hierarchy (`src/ai_workspace/core/errors.py`)

Define all custom exceptions:

```python
class WorkspaceError(Exception):
    """Base for all workspace errors."""

class WorkspaceNotFoundError(WorkspaceError):
    """No .ai/ or workspace.yaml in current directory."""

class WorkspaceValidationError(WorkspaceError):
    """YAML schema validation failed."""

class SecurityError(WorkspaceError):
    """Security check failed."""

class SkillError(WorkspaceError):
    """Skill operation failed."""

class IndexError(WorkspaceError):
    """Index read or write failed."""
```

No tests needed — errors are tested implicitly through callers.

---

### Task 1.2 — Path Safety (`src/ai_workspace/core/paths.py`)

Implement:

```python
def safe_path(base: Path, user_input: str) -> Path:
    """Resolve user path, raise SecurityError on traversal attempt."""

def global_layer_path() -> Path:
    """Return Path to ~/.ai-workspace/, creating it if missing."""

def workspace_context_path(project_root: Path) -> Path:
    """Return Path to <project>/.ai/, does NOT create it."""

def find_project_root() -> Path:
    """Walk up from cwd until workspace.yaml or .ai/ is found.
    Raise WorkspaceNotFoundError if neither is found at or above cwd."""
```

**Tests** (`tests/unit/test_paths.py`):
- `safe_path` with a normal relative path returns the resolved path
- `safe_path` with `../../etc/passwd` raises `SecurityError`
- `safe_path` with `../sibling` raises `SecurityError`
- `safe_path` with an absolute path that escapes base raises `SecurityError`
- `global_layer_path` returns a path ending in `.ai-workspace`
- `find_project_root` finds `workspace.yaml` two levels up from a nested temp directory
- `find_project_root` raises `WorkspaceNotFoundError` when no marker exists

---

### Task 1.3 — Workspace Schema (`src/ai_workspace/core/config.py`)

Implement the full Pydantic v2 model matching the schema in Section 5 of the spec. Key rules:
- `workspace.name`: validated by regex `^[a-z0-9-]+$`, max 64 chars
- `repositories[].path`: must be relative (no leading `/`)
- All enum fields use `Literal` types
- Unknown extra fields raise `ValidationError` (use `model_config = ConfigDict(extra='forbid')`)
- Implement `load_workspace_yaml(path: Path) -> WorkspaceConfig` that reads YAML and validates through the model, raising `WorkspaceValidationError` with a human-readable message on failure

**Tests** (`tests/unit/test_config.py`):
- Valid minimal YAML (only required fields) loads without error
- Valid full YAML loads without error
- `workspace.name` with uppercase letters raises `WorkspaceValidationError`
- `workspace.name` with spaces raises `WorkspaceValidationError`
- `workspace.name` longer than 64 chars raises `WorkspaceValidationError`
- `repositories[].path` with leading `/` raises `WorkspaceValidationError`
- Unknown top-level key raises `WorkspaceValidationError`
- Missing required `workspace.name` raises `WorkspaceValidationError`
- Missing required `workspace.type` raises `WorkspaceValidationError`
- `workspace.type: invalid-type` raises `WorkspaceValidationError`
- Load from the `tests/fixtures/greenfield/workspace.yaml` fixture succeeds
- Load from the `tests/fixtures/python-api/workspace.yaml` fixture succeeds
- Load from the `tests/fixtures/monorepo/workspace.yaml` fixture succeeds

Write the fixture `workspace.yaml` files now to support these tests.

---

### Task 1.4 — Safe Filesystem Operations (`src/ai_workspace/core/filesystem.py`)

Implement:

```python
def ensure_directory(path: Path) -> None:
    """Create directory and parents if not exists. Never fails if already exists."""

def write_file(path: Path, content: str, overwrite: bool = False) -> None:
    """Write file. Raise WorkspaceError if exists and overwrite is False."""

def read_file(path: Path) -> str:
    """Read file. Raise WorkspaceError with clean message if not found."""

def file_exists(path: Path) -> bool:
    """True if path is an existing file."""

def directory_exists(path: Path) -> bool:
    """True if path is an existing directory."""
```

**Tests** (`tests/unit/test_filesystem.py`):
- `ensure_directory` creates directory and nested parents
- `ensure_directory` is idempotent (calling twice does not error)
- `write_file` creates a file with correct content
- `write_file` raises `WorkspaceError` when file exists and `overwrite=False`
- `write_file` overwrites when `overwrite=True`
- `read_file` returns correct content
- `read_file` raises `WorkspaceError` on missing file with a message containing the path

Use `tmp_path` pytest fixture for all filesystem tests.

---

### Task 1.5 — CLI Skeleton (`src/ai_workspace/cli/main.py`)

Create a Typer app with all commands registered as stubs. Every stub must:
- Print a Rich `[yellow]Not yet implemented[/yellow]` message
- Return without error

Commands to register (matching spec Section 11):
- `init`
- `adopt`
- `validate`
- `validate security` (as a subcommand group)
- `index rebuild` (as a subcommand group)
- `summarize`
- `skills list`
- `skills search`
- `skills show`
- `skills propose`
- `docs templates`
- `docs create`
- `handoff generate`

Use a `Console()` instance at module level for all output. Never use `print()`.

**Tests** (`tests/unit/test_cli_skeleton.py`):
- Use `typer.testing.CliRunner`
- Every registered command exits with code 0
- Every registered command prints output (not silent)
- `--help` on the root command exits with code 0 and contains "ai-workspace" in output
- `--help` on each subcommand group exits with code 0

---

### Phase 1 Definition of Done

- [ ] `src/ai_workspace/core/errors.py` exists with all six error classes
- [ ] `src/ai_workspace/core/paths.py` exists with all four functions
- [ ] `src/ai_workspace/core/config.py` exists with full Pydantic schema and loader
- [ ] `src/ai_workspace/core/filesystem.py` exists with all five functions
- [ ] `src/ai_workspace/cli/main.py` exists with all commands registered as stubs
- [ ] All unit tests pass with no failures
- [ ] Coverage on `core/` modules is 90%+
- [ ] `ai-workspace --help` lists all top-level commands
- [ ] `ai-workspace validate` prints "Not yet implemented" and exits 0
- [ ] `ruff check src/` passes with no errors
- [ ] `black --check src/` passes

### Phase 1 Commit

```
git add .
git commit -m "phase-1: core foundation — paths, config schema, filesystem, cli skeleton

- WorkspaceConfig Pydantic model with full validation
- safe_path() blocks traversal attempts
- Filesystem helpers with overwrite protection
- CLI skeleton with all commands registered
- 90%+ coverage on core modules"
```

---

## Phase 2 — Workspace Generation

**Goal**: `ai-workspace init` works end-to-end. Running it on an empty directory produces a complete, valid `.ai/` scaffold, a `docs/` structure, and a `workspace.yaml`. This is the most visible deliverable and the foundation for everything else.

---

### Task 2.1 — Template System (`src/ai_workspace/workspace/templates.py`)

Define all file templates as Python string constants or a template registry. Templates needed:
- `start-here.md` (use the full template from spec Section 8)
- `project-summary.md` (stub with headers: What This Project Is, Tech Stack, Key Components)
- `architecture-summary.md` (stub with headers: Architecture Style, Key Decisions, Component Map)
- `repo-map.md` (stub with a note: "Run `ai-workspace summarize` to populate")
- `current-state.md` (stub with headers: Current Phase, What Works, What Doesn't, Known Issues)
- `current-task.md` (stub with headers: Task, Goal, Acceptance Criteria, Steps)
- `current-plan.md` (stub)
- `blockers.md` (stub)
- `next-steps.md` (stub)
- ADR template (use the full template from spec Section 13)
- Doc metadata header (YAML front matter block)

Templates must support simple `{{variable}}` substitution. Do not use Jinja2 — implement a minimal `render(template: str, context: dict) -> str` function using `str.replace()`.

**Tests** (`tests/unit/test_templates.py`):
- `render` replaces `{{workspace.name}}` with the correct value
- `render` with a missing key leaves the placeholder unchanged (no crash)
- `render` with empty context returns template unchanged
- `start-here.md` template contains required sections: "Start Here", "Before You Do Anything", "Mandatory Workflow"
- ADR template contains required sections: "Context", "Decision", "Rationale", "Consequences"

---

### Task 2.2 — Workspace Generator (`src/ai_workspace/workspace/generator.py`)

Implement `generate_workspace(config: WorkspaceConfig, project_root: Path, force: bool = False) -> list[Path]`:

1. Create `.ai/` and all subdirectories
2. Write all template files with config values substituted
3. Create `docs/` structure based on `documentation.structure` setting:
   - `minimal`: `docs/architecture/`, `docs/decisions/`
   - `standard` (default): adds `docs/api/`, `docs/workflows/`, `docs/onboarding/`
   - `full`: all eight directories from spec
4. Write `.gitkeep` to empty directories
5. Create empty index YAML files with correct schema headers
6. Return list of all paths created

If `force=False` and `.ai/` already exists, raise `WorkspaceError` with a message telling the user to use `--force`.

**Tests** (`tests/integration/test_generator.py`):
- Generating into an empty `tmp_path` creates all expected directories
- Generating creates `start-here.md` containing the workspace name
- Generating creates all four index files
- Generating with `documentation.structure: minimal` creates only two doc directories
- Generating with `documentation.structure: full` creates all eight doc directories
- Generating with `force=False` into existing `.ai/` raises `WorkspaceError`
- Generating with `force=True` into existing `.ai/` overwrites without error
- All created index files are valid YAML (parse without error)
- `start-here.md` contains all mandatory sections

---

### Task 2.3 — Interactive Init Prompt (`src/ai_workspace/cli/init_cmd.py`)

Implement the `init` command:

**Interactive flow** (no `--file` flag):
Use `typer.prompt()` for each field. Collect:
1. Project name (validate kebab-case inline, re-prompt on invalid)
2. Workspace type (`monorepo` / `single` / `multi`) — show numbered options
3. Primary language — show numbered options
4. Architecture style — show numbered options, allow skip
5. Enable AI features? (y/n, default y)
6. Enable documentation? (y/n, default y)
7. Documentation structure? (minimal/standard/full, default standard)

After collection, build a `WorkspaceConfig`, write `workspace.yaml`, call `generate_workspace()`, and print a Rich success panel listing all created paths.

**YAML flow** (`--file PATH`):
Load and validate the YAML, write it to the project root as `workspace.yaml`, call `generate_workspace()`, print success panel.

**Flags**:
- `-f / --file PATH`: path to workspace YAML file
- `--dry-run`: print what would be created, do not write anything
- `--force`: pass `force=True` to generator

**Tests** (`tests/integration/test_init_cmd.py`):
- `init --file <greenfield-fixture>` in a temp directory creates `.ai/` and exits 0
- `init --file <monorepo-fixture>` creates correct structure
- `init --file <fixture> --dry-run` prints paths but creates nothing on disk
- `init --file <fixture>` twice without `--force` exits non-zero with a useful message
- `init --file <fixture> --force` twice succeeds both times
- `init --file <invalid-yaml>` exits non-zero with a validation error message
- Output contains "workspace.yaml" in the success summary

---

### Phase 2 Definition of Done

- [ ] `workspace/templates.py` exists with all templates and `render()` function
- [ ] `workspace/generator.py` exists and generates the full `.ai/` scaffold
- [ ] `cli/init_cmd.py` implements both interactive and YAML modes
- [ ] `init --file` works against all three fixture workspaces
- [ ] `init --dry-run` creates no files
- [ ] `init` twice without `--force` fails with a clear message
- [ ] All integration tests pass
- [ ] Coverage on `workspace/generator.py` is 85%+
- [ ] Generated `start-here.md` is human-readable and well-formed
- [ ] Generated index files are valid YAML
- [ ] `ruff` and `black` pass

### Phase 2 Commit

```
git add .
git commit -m "phase-2: workspace generation — init command fully working

- Template system with variable substitution
- Full .ai/ scaffold generation
- docs/ structure with minimal/standard/full modes
- init command: interactive mode and --file mode
- --dry-run support
- Integration tests against all fixture workspaces"
```

---

## Phase 3 — Indexing System

**Goal**: `ai-workspace index rebuild` produces valid, populated indexes from a project's docs and context files. Agents can query these files instead of scanning the repository.

---

### Task 3.1 — Index Schemas (`src/ai_workspace/core/index_schemas.py`)

Define Pydantic models for each index file matching the schemas in spec Section 9:
- `DocsIndex` / `DocsIndexEntry`
- `AdrIndex` / `AdrIndexEntry`
- `TaskIndex` / `TaskIndexEntry`
- `RepoIndex` / `RepoIndexEntry`

Implement:
- `load_index(path: Path, model: type) -> model` — loads YAML, validates, returns model
- `write_index(path: Path, index: BaseModel) -> None` — serializes model to YAML with `generated_at` updated to now

**Tests** (`tests/unit/test_index_schemas.py`):
- Each index model loads from a valid YAML fixture
- Each index model raises `ValidationError` on a missing required field
- `write_index` then `load_index` round-trips without data loss
- `generated_at` is updated on write

---

### Task 3.2 — Index Builder (`src/ai_workspace/workspace/index_builder.py`)

Implement `rebuild_all_indexes(project_root: Path, config: WorkspaceConfig) -> dict[str, int]`:

This function must:

**For `docs-index.yaml`**:
- Scan `docs/` recursively for `*.md` files
- For each file, read its YAML front matter (the `---` block at the top)
- Extract `title`, `purpose`, `tags`, `status` from front matter
- Fall back to filename-derived title if front matter is missing
- Record `last_modified` from `os.path.getmtime`
- Write to `.ai/indexes/docs-index.yaml`

**For `adr-index.yaml`**:
- Scan `docs/decisions/` for files matching `ADR-*.md`
- Parse front matter for `title`, `status`, `date`, `tags`, `superseded_by`
- Write to `.ai/indexes/adr-index.yaml`

**For `task-index.yaml`**:
- Read `.ai/active-task/current-task.md` if it exists
- Extract task title from first `# ` heading
- Status is always `active` if the file is non-empty
- Write to `.ai/indexes/task-index.yaml`

**For `repo-index.yaml`**:
- For each repository in `config.repositories`, record name, path, and purpose
- Detect language from files in that path using the detection logic from spec Section 12
- List key directories (src/, tests/, etc.) if they exist
- Write to `.ai/indexes/repo-index.yaml`

Return a dict of `{index_name: entry_count}`.

**Tests** (`tests/integration/test_index_builder.py`):
- Rebuilding on the `python-api` fixture produces a non-empty `docs-index.yaml`
- Rebuilding on a fixture with ADR files produces correct ADR entries
- Rebuilding when `docs/` is empty produces an empty but valid `docs-index.yaml`
- Front matter is correctly parsed and reflected in index entries
- Files without front matter are indexed with derived title
- `repo-index.yaml` reflects repositories from config
- Return dict contains correct counts
- All written index files parse as valid YAML

---

### Task 3.3 — Global Index Manager (`src/ai_workspace/intelligence/indexes.py`)

Implement for the global layer:
- `rebuild_global_indexes(global_root: Path) -> None` — scans `~/.ai-workspace/skills/`, `standards/`, `templates/` and writes corresponding global index files
- `search_skills_index(global_root: Path, query: str) -> list[dict]` — case-insensitive substring search across name, description, and tags
- `get_skills_index(global_root: Path) -> list[dict]` — returns all entries

**Tests** (`tests/unit/test_global_indexes.py`):
- `rebuild_global_indexes` on an empty global layer produces valid empty index files
- `search_skills_index` finds skills matching a tag
- `search_skills_index` is case-insensitive
- `search_skills_index` with no matches returns empty list

---

### Task 3.4 — Index Rebuild Command (`src/ai_workspace/cli/index_cmd.py`)

Implement `index rebuild`:
1. Locate project root
2. Load `workspace.yaml`
3. Call `rebuild_all_indexes()`
4. Print a Rich table showing index name and entry count
5. Exit 0

**Tests** (`tests/integration/test_index_cmd.py`):
- `index rebuild` in a fixture directory exits 0
- `index rebuild` produces a Rich table in output
- `index rebuild` outside a workspace directory exits non-zero with a clear message

---

### Phase 3 Definition of Done

- [ ] All four index schemas defined as Pydantic models
- [ ] `rebuild_all_indexes()` populates all indexes correctly
- [ ] Front matter parsing works for files with and without front matter
- [ ] Global index manager scans global layer correctly
- [ ] `index rebuild` command works in all fixture directories
- [ ] `index rebuild` outside a workspace fails cleanly
- [ ] All unit and integration tests pass
- [ ] Coverage on `workspace/index_builder.py` is 85%+
- [ ] `ruff` and `black` pass

### Phase 3 Commit

```
git add .
git commit -m "phase-3: indexing system — rebuild all four local indexes

- Pydantic index schemas with round-trip YAML serialization
- Index builder: docs, ADRs, tasks, repo indexes
- Front matter parsing with graceful fallback
- Global index manager for skills/standards/templates
- index rebuild command
- Integration tests against fixture repositories"
```

---

## Phase 4 — Existing Project Adoption

**Goal**: `ai-workspace adopt` runs safely on an existing repository, detects its technology stack, generates `.ai/` context files pre-populated with real data, and suggests (but never creates) missing documentation.

---

### Task 4.1 — Technology Detector (`src/ai_workspace/workspace/detector.py`)

Implement `detect_project(root: Path) -> DetectionResult` where `DetectionResult` is a dataclass/Pydantic model containing:
- `languages: list[str]` — detected primary and secondary languages
- `frameworks: list[str]`
- `package_managers: list[str]`
- `ci_systems: list[str]`
- `has_tests: bool` — any `tests/` or `test_` directories found
- `has_docs: bool` — any `docs/` directory found
- `entry_points: list[Path]` — detected main files
- `config_files: list[Path]` — detected config files (pyproject.toml, package.json, etc.)

Use ONLY static file inspection — no execution. Apply detection rules from spec Section 12, extended with:
- `package_managers`: pyproject.toml/pip → pip, package.json/npm → npm/yarn, go.mod → go
- `has_tests`: any directory named `tests`, `test`, or `__tests__` exists

**Tests** (`tests/unit/test_detector.py`):
- Detects Python from `pyproject.toml` in `python-api` fixture
- Detects Node.js from `package.json`
- Detects monorepo structure from `monorepo` fixture
- Returns `has_tests: True` when `tests/` directory exists
- Returns `has_docs: False` when no `docs/` directory exists
- Does not crash on an empty directory
- Does not execute any files (verified by mock — no subprocess calls)

---

### Task 4.2 — Adoption Context Generator (`src/ai_workspace/workspace/adopter.py`)

Implement `adopt_project(root: Path, config: WorkspaceConfig, force: bool = False) -> AdoptionResult`:

1. Run `detect_project(root)`
2. Write `.ai/generated/tech-detection.yaml` with full detection output
3. Generate `.ai/` scaffold (call `generate_workspace()`) with `force` flag
4. Populate `start-here.md` with detected info (language, frameworks, test status)
5. Populate `project-summary.md` with detected technologies as a starting point
6. Generate `.ai/generated/repo-map-generated.md` with a directory tree (2 levels deep, excluding `.git`, `__pycache__`, `node_modules`, `.ai`)
7. Build initial indexes (call `rebuild_all_indexes()`)
8. Return `AdoptionResult` containing:
   - `files_created: list[Path]`
   - `suggested_docs: list[str]` — doc filenames that should exist but don't
   - `detection: DetectionResult`

**Suggested docs logic**:
- If `has_tests` is True and no `docs/workflows/testing-strategy.md` exists → suggest it
- If any framework detected and no `docs/architecture/architecture-overview.md` → suggest it
- If any CI system detected and no `docs/workflows/deployment-workflow.md` → suggest it

**Safety rules**: Never modify any file outside `.ai/` and `docs/`. Do not create `docs/` files — only suggest them. If a file would be overwritten, only do so if `force=True`.

**Tests** (`tests/integration/test_adopter.py`):
- Adopting the `python-api` fixture creates `.ai/` and `generated/tech-detection.yaml`
- `tech-detection.yaml` contains detected Python and FastAPI
- `start-here.md` mentions detected language
- Suggested docs list includes `architecture-overview.md` for a framework project
- Adopting the `no-docs` fixture produces suggested docs but no errors
- Adoption is idempotent with `force=True`
- No files are created outside `.ai/` and `docs/`
- Repo map is generated and contains directory names

---

### Task 4.3 — Adopt Command (`src/ai_workspace/cli/adopt_cmd.py`)

Implement `adopt`:
1. Locate project root (default: cwd)
2. Check for `workspace.yaml` — if missing, run interactive `init` flow first, then adopt
3. Call `adopt_project()`
4. Print Rich panel with created files
5. Print Rich panel with suggested documentation (if any), framed as suggestions not instructions
6. Exit 0

**Flags**:
- `--dry-run`: detect and suggest but create nothing
- `--force`: overwrite existing `.ai/` files
- `--root PATH`: target a specific directory instead of cwd

**Tests** (`tests/integration/test_adopt_cmd.py`):
- `adopt` in `python-api` fixture exits 0
- `adopt --dry-run` creates no files
- `adopt` prints suggested documentation
- `adopt` outside any directory with a project exits non-zero with a clear message

---

### Phase 4 Definition of Done

- [ ] `detector.py` correctly identifies language, frameworks, CI, and test presence
- [ ] Detection uses only static file inspection (no subprocess calls)
- [ ] `adopter.py` generates a populated `.ai/` from an existing project
- [ ] `tech-detection.yaml` is written correctly
- [ ] Repo map file is generated
- [ ] Suggested docs logic works correctly for all three suggestion rules
- [ ] Adoption never modifies files outside `.ai/`
- [ ] `adopt` command works on all four fixtures
- [ ] `adopt --dry-run` creates no files (verified by assertion on disk)
- [ ] All integration tests pass
- [ ] Coverage on `workspace/adopter.py` is 80%+
- [ ] `ruff` and `black` pass

### Phase 4 Commit

```
git add .
git commit -m "phase-4: existing project adoption — detect, adopt, suggest

- Static technology detector: language, framework, CI, test presence
- Adopter generates pre-populated .ai/ from existing repo
- tech-detection.yaml with full detection output
- Repo map generation (2-level directory tree)
- Suggested documentation logic
- adopt command with --dry-run and --force
- Integration tests against all fixtures"
```

---

## Phase 5 — Summarization

**Goal**: `ai-workspace summarize` reads the project and produces machine-readable summary files in `.ai/generated/`. Agents use these instead of scanning the repo. Human-owned summary files are never touched.

---

### Task 5.1 — Dependency Summarizer (`src/ai_workspace/workspace/summarizer.py`)

Implement `generate_dependency_summary(root: Path) -> str` that:
- Reads `requirements.txt` if present → lists package names and versions
- Reads `pyproject.toml` `[project.dependencies]` if present
- Reads `package.json` `dependencies` and `devDependencies` if present
- Reads `go.mod` `require` block if present
- Produces a Markdown document summarizing all found dependencies grouped by file
- Marks dev vs production dependencies where distinguishable

Implement `generate_repo_map(root: Path, max_depth: int = 2) -> str`:
- Produces a Markdown-formatted directory tree
- Excludes: `.git`, `__pycache__`, `*.pyc`, `node_modules`, `.ai`, `dist`, `build`, `.egg-info`
- Annotates known directories: `src/` → "source code", `tests/` → "test suite", `docs/` → "documentation"
- Includes file counts per directory at depth 1

Implement `summarize_workspace(root: Path, config: WorkspaceConfig) -> dict[str, Path]`:
- Calls both generators above
- Writes results to `.ai/generated/dependency-summary.md` and `.ai/generated/repo-map-generated.md`
- Writes `.ai/generated/tech-detection.yaml` if not already present
- Returns dict of `{summary_name: path_written}`
- Never writes to human-owned files (`project-summary.md`, `architecture-summary.md`, `current-state.md`)

**Tests** (`tests/unit/test_summarizer.py`):
- Dependency summary from `python-api` fixture contains package names from `requirements.txt`
- Dependency summary from `monorepo` fixture handles multiple repos
- Dependency summary with no known dependency files returns a "none detected" document
- Repo map contains directory names at depth 1
- Repo map excludes `__pycache__` and `.git`
- Repo map annotates `tests/` correctly
- `summarize_workspace` does not write to `project-summary.md`
- All written files are valid Markdown (non-empty, contains `#` headings)

---

### Task 5.2 — Summarize Command (`src/ai_workspace/cli/summarize_cmd.py`)

Implement `summarize`:
1. Locate project root
2. Load config
3. Call `summarize_workspace()`
4. Print Rich table showing file name and path for each generated summary
5. Exit 0

**Flags**:
- `--dry-run`: print what would be generated without writing

**Tests** (`tests/integration/test_summarize_cmd.py`):
- `summarize` in `python-api` fixture exits 0 and produces files on disk
- `summarize --dry-run` prints output but creates no files
- `summarize` outside a workspace exits non-zero with clear message
- Output lists generated file paths

---

### Phase 5 Definition of Done

- [ ] Dependency summary reads `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`
- [ ] Repo map excludes noise directories and annotates known ones
- [ ] `summarize_workspace` never touches human-owned files
- [ ] All three generated files are written on `summarize`
- [ ] `summarize --dry-run` writes nothing
- [ ] All unit tests pass
- [ ] Coverage on `workspace/summarizer.py` is 85%+
- [ ] `ruff` and `black` pass

### Phase 5 Commit

```
git add .
git commit -m "phase-5: summarization — dependency summary, repo map, tech detection

- Dependency summarizer: requirements.txt, pyproject.toml, package.json, go.mod
- Repo map generator with depth limit and noise exclusion
- summarize_workspace: never touches human-owned files
- summarize command with --dry-run
- Unit tests with fixture-based assertions"
```

---

## Phase 6 — Skills System

**Goal**: The global skills system is fully operational. Agents can list, search, and view skills. Humans can propose new skills. The governance rules (no agent auto-merge) are enforced programmatically.

---

### Task 6.1 — Seed Built-In Skills

Create the following skills in `src/ai_workspace/data/skills/` (bundled with the package):
- `python-package/` — Python package structure workflow
- `terraform-module/` — Terraform module workflow
- `docker-service/` — Dockerfile + compose workflow
- `api-endpoint/` — REST endpoint implementation workflow
- `adr-creation/` — how to write a good ADR

Each skill needs a valid `skill.yaml` and a `notes.md`. Templates and examples directories should exist but can be empty (with `.gitkeep`).

On first global layer initialization, copy these built-in skills to `~/.ai-workspace/skills/`.

**Tests** (`tests/unit/test_builtin_skills.py`):
- Each built-in skill directory contains `skill.yaml`
- Each `skill.yaml` validates against the skill schema
- All five built-in skills are present

---

### Task 6.2 — Skills Manager (`src/ai_workspace/intelligence/skills.py`)

Implement:

```python
def list_skills(global_root: Path) -> list[SkillMetadata]:
    """Return all active (non-proposed) skills from ~/.ai-workspace/skills/."""

def list_proposed_skills(global_root: Path) -> list[SkillMetadata]:
    """Return all proposed skills (directories ending in -proposed)."""

def get_skill(global_root: Path, name: str) -> SkillMetadata:
    """Return a single skill by name. Raise SkillError if not found."""

def search_skills(global_root: Path, query: str) -> list[SkillMetadata]:
    """Case-insensitive search across name, description, tags."""

def propose_skill(global_root: Path, metadata: SkillMetadata) -> Path:
    """Write a proposed skill to <name>-proposed/. Raise SkillError if already exists."""

def accept_skill(global_root: Path, name: str) -> Path:
    """Rename <name>-proposed/ to <name>/. Raises SkillError if proposed does not exist."""

def rebuild_skills_index(global_root: Path) -> int:
    """Rebuild skills-index.yaml. Return count of indexed skills."""
```

Enforce governance: `propose_skill` must write to `<name>-proposed/` only. `accept_skill` performs the rename and rebuilds the index. Any direct write to a non-proposed skill directory must go through `accept_skill`.

`SkillMetadata` is a Pydantic model matching the skill schema from spec Section 7.

**Tests** (`tests/unit/test_skills.py`):
- `list_skills` returns built-in skills after initialization
- `list_skills` excludes proposed skills
- `list_proposed_skills` returns only proposed skills
- `get_skill` returns correct skill by name
- `get_skill` raises `SkillError` for unknown name
- `search_skills` finds by name substring
- `search_skills` finds by tag
- `search_skills` is case-insensitive
- `search_skills` returns empty list on no match
- `propose_skill` creates `<name>-proposed/` directory with `skill.yaml`
- `propose_skill` raises `SkillError` if proposed already exists
- `accept_skill` renames `<name>-proposed/` to `<name>/`
- `accept_skill` raises `SkillError` if proposed does not exist
- `rebuild_skills_index` returns correct count and writes valid YAML

---

### Task 6.3 — Skills Commands (`src/ai_workspace/cli/skills_cmd.py`)

Implement all four skills subcommands:

**`skills list`**: Rich table with columns: Name, Status, Tags (comma-joined), Description (truncated 60 chars). Show proposed skills at the bottom with `[proposed]` in the Status column.

**`skills search <query>`**: Same table format, filtered by query. Print "No skills found" if empty.

**`skills show <name>`**: Print full skill details in a Rich panel: name, version, description, tags, validation commands, related skills, notes (first 10 lines of `notes.md`).

**`skills propose`**: Interactive prompts for name, description, tags, validation commands. Write proposed skill. Print success with path.

**Tests** (`tests/integration/test_skills_cmd.py`):
- `skills list` exits 0 and shows built-in skills
- `skills search terraform` exits 0 and shows terraform-module
- `skills search zzznomatch` exits 0 and prints "No skills found"
- `skills show python-package` exits 0 and prints description
- `skills show unknown-skill` exits non-zero with error message
- `skills list` shows proposed skills when they exist

---

### Phase 6 Definition of Done

- [ ] Five built-in skills exist and validate against schema
- [ ] Built-in skills are copied to global layer on first init
- [ ] `list_skills`, `search_skills`, `get_skill` work correctly
- [ ] `propose_skill` writes to `-proposed` suffix directory only
- [ ] `accept_skill` performs rename and rebuilds index
- [ ] All four skills subcommands work
- [ ] Skills index is rebuilt after every mutation
- [ ] All unit and integration tests pass
- [ ] Coverage on `intelligence/skills.py` is 85%+
- [ ] `ruff` and `black` pass

### Phase 6 Commit

```
git add .
git commit -m "phase-6: skills system — list, search, show, propose with governance

- Five built-in skills bundled with package
- SkillMetadata Pydantic model with full validation
- Governance: propose writes to -proposed, accept renames
- skills list/search/show/propose commands
- Skills index rebuild on every mutation
- Unit and integration tests"
```

---

## Phase 7 — Security and Validation

**Goal**: `ai-workspace validate` and `ai-workspace validate security` are fully implemented. The security scanner runs `pip-audit` and `bandit`, detects secrets in templates, and checks workspace health. All output is clear and actionable.

---

### Task 7.1 — Workspace Validator (`src/ai_workspace/security/validator.py`)

Implement `validate_workspace(root: Path) -> list[ValidationResult]` where `ValidationResult` has:
- `check: str` — check name
- `status: Literal["pass", "warn", "fail"]`
- `message: str`

Checks to implement (from spec Section 11):
1. `workspace.yaml` exists and loads without validation error
2. `.ai/` directory exists
3. `start-here.md` exists and is non-empty
4. All four index files exist
5. All four index files parse as valid YAML
6. Index entries reference paths that exist on disk (warn, not fail)
7. No stale handoffs (> 30 days old with no newer one) — warn only
8. Active task file exists and is non-empty if `ai.tasks: true`

**Tests** (`tests/unit/test_validator.py`):
- All checks pass on a fully valid workspace (greenfield fixture after init)
- Missing `workspace.yaml` produces `fail` on check 1
- Missing `.ai/` produces `fail` on check 2
- Missing `start-here.md` produces `fail` on check 3
- Broken index YAML produces `fail` on check 5
- Stale-only handoff produces `warn` on check 7 (use a file with old mtime)
- Results list length equals number of checks

---

### Task 7.2 — Security Scanner (`src/ai_workspace/security/scanner.py`)

Implement `scan_security(root: Path) -> list[ValidationResult]`:

1. **`pip-audit` check**: Run `pip-audit --format=json` via `subprocess.run`. If not installed, return a `warn` result. If installed and finds CVEs, return `fail` with count. If clean, return `pass`.
2. **`bandit` check**: Run `bandit -r src/ -f json -q` via `subprocess.run` on the project's `src/` directory. If not installed, return `warn`. Parse output for HIGH severity findings. If any, return `fail`. If clean, return `pass`.
3. **Secret detection**: Scan all files in `.ai/` and `docs/` for the secret patterns from spec Section 14. Return `fail` with filename if any pattern matches.
4. **YAML safety**: Load all YAML files in `.ai/` with a YAML safe loader. If any fails or contains `!!python/object`, return `fail`.
5. **File permissions**: Check no files in `.ai/` are world-writable (`stat.S_IWOTH`). Return `warn` if any are.

For subprocess calls: always use `subprocess.run(..., capture_output=True, timeout=60)`. If the tool times out, return `warn` with a timeout message. Never let a scanner check crash the CLI.

**Tests** (`tests/security/test_scanner.py`):
- Secret detection finds fake AWS key (`AKIAIOSFODNN7EXAMPLE`) in a fixture file
- Secret detection finds fake GitHub token pattern
- Secret detection returns `pass` on clean files
- YAML safety check catches `!!python/object` tag
- YAML safety check passes on normal YAML
- File permissions check catches world-writable file (use `os.chmod(path, 0o777)`)
- `pip-audit` check returns `warn` (not `fail`) if pip-audit is not installed (mock subprocess)
- All checks complete even when one raises an exception (defensive catch)

---

### Task 7.3 — Validate and Validate Security Commands (`src/ai_workspace/cli/validate_cmd.py`)

**`validate`**:
1. Run `validate_workspace()`
2. Print Rich table: Check | Status (with color: green/yellow/red) | Message
3. Exit 1 if any result is `fail`, else exit 0

**`validate security`**:
1. Run `scan_security()`
2. Print same table format
3. Print summary: N passed, N warnings, N failed
4. Exit 1 if any result is `fail`, else exit 0

**Tests** (`tests/integration/test_validate_cmd.py`):
- `validate` on a valid workspace exits 0
- `validate` with missing `start-here.md` exits 1
- `validate security` on a clean workspace exits 0
- `validate security` with a secret-containing file exits 1
- Both commands print a Rich table
- Both commands exit 0 even when external tools (pip-audit, bandit) are absent

---

### Phase 7 Definition of Done

- [ ] `validate_workspace` implements all eight checks
- [ ] `scan_security` implements all five scanner checks
- [ ] Secret detection patterns from spec are all implemented and tested
- [ ] Scanner never crashes even when external tools are absent
- [ ] `validate` exits 1 on any `fail` result
- [ ] `validate security` exits 1 on any `fail` result
- [ ] Security tests include world-writable file, secret patterns, and YAML injection
- [ ] All tests pass
- [ ] Coverage on `security/` is 85%+
- [ ] `ruff` and `black` pass

### Phase 7 Commit

```
git add .
git commit -m "phase-7: security and validation — workspace health and security scanning

- validate_workspace: 8 checks with pass/warn/fail results
- scan_security: pip-audit, bandit, secret detection, YAML safety, permissions
- Secret patterns: AWS keys, GitHub tokens, password/api_key patterns
- Defensive error handling: scanner never crashes on missing tools
- validate and validate security commands with colored Rich output
- Security tests with chmod, pattern injection, YAML !!python/object"
```

---

## Phase 8 — Docs System, Handoffs, README, and Packaging

**Goal**: The remaining user-facing commands are implemented, the README is complete, the tool is installable from PyPI conventions, and the full test suite passes at 80%+ coverage. The tool is done.

---

### Task 8.1 — Documentation Commands (`src/ai_workspace/cli/docs_cmd.py`)

**`docs templates`**:
- List available templates from `~/.ai-workspace/templates/docs/` and the built-in bundled templates
- Rich table: Template Name | Description | Output Path

**`docs create <template-name>`**:
- Look up template by name
- Prompt for any required substitution values (e.g. title for ADR)
- Resolve output path (e.g. `architecture-overview` → `docs/architecture/architecture-overview.md`)
- Write file with metadata front matter pre-populated
- Refuse to overwrite without `--force`
- Update `docs-index.yaml` after creation

Built-in templates to support:
- `architecture-overview` → `docs/architecture/architecture-overview.md`
- `adr` → `docs/decisions/ADR-<next-number>-<slug>.md` (auto-increment ADR number from index)
- `runbook` → `docs/runbooks/<slug>.md`
- `onboarding` → `docs/onboarding/<slug>.md`
- `api-reference` → `docs/api/<slug>.md`

**Tests** (`tests/integration/test_docs_cmd.py`):
- `docs templates` exits 0 and lists at least five templates
- `docs create architecture-overview` creates the file at correct path
- `docs create adr` auto-increments ADR number correctly
- `docs create architecture-overview` twice without `--force` exits non-zero
- Created files contain valid YAML front matter
- `docs-index.yaml` is updated after `docs create`

---

### Task 8.2 — Handoff Command (`src/ai_workspace/cli/handoff_cmd.py` and `src/ai_workspace/workspace/handoff.py`)

**`handoff generate`**:
Interactive prompts for:
1. What was accomplished? (multiline — press Enter twice to end)
2. Current state? (single line)
3. Blockers? (single line, default "None")
4. Next steps? (single line)
5. Are tests passing? (y/n)

Then:
- Read current task title from `.ai/active-task/current-task.md` (first `#` heading)
- Build handoff filename: `YYYY-MM-DD-HH-MM-<slugified-task-name>.md`
- Write to `.ai/handoffs/`
- Update `task-index.yaml`
- Print success with file path

Implement `generate_handoff(root: Path, data: HandoffData) -> Path` in `handoff.py`.

**Tests** (`tests/integration/test_handoff_cmd.py`):
- `handoff generate` (with mocked prompts) creates a file in `.ai/handoffs/`
- Handoff filename contains current date
- Handoff file contains all sections from the spec template
- `task-index.yaml` is updated after handoff
- Running twice creates two separate files (no overwrite)

---

### Task 8.3 — Global Layer Auto-Initialization

On the first invocation of any command, if `~/.ai-workspace/` does not exist, the global layer must be silently initialized:
1. Create directory tree
2. Copy bundled skills
3. Copy bundled standards
4. Build global indexes
5. Write `config.yaml` with version and creation timestamp

This must happen transparently — no user action required, no prompts. Print a one-line Rich info message: `[dim]Initialized global workspace layer at ~/.ai-workspace/[/dim]`.

**Tests** (`tests/integration/test_global_init.py`):
- Any command run with a missing `~/.ai-workspace/` creates it (use tmp HOME via monkeypatch)
- After init, built-in skills are present in the skills directory
- `config.yaml` exists and contains version string
- Global indexes are written and valid

---

### Task 8.4 — Standards System

Implement five bundled standards files in `src/ai_workspace/data/standards/`:
- `python.md` — Python conventions: naming, structure, imports, type hints, docstrings
- `testing.md` — testing conventions: naming, fixtures, coverage, snapshot tests
- `documentation.md` — documentation conventions: front matter, headings, ADRs
- `security.md` — security conventions: secret handling, path validation, input sanitization
- `terraform.md` — Terraform conventions: module structure, naming, validation

Copy to `~/.ai-workspace/standards/` on global layer init.

No dedicated tests needed — covered by global init tests.

---

### Task 8.5 — Full Test Suite Pass and Coverage

Run the full test suite and enforce coverage:

```bash
pytest tests/ --cov=src/ai_workspace --cov-report=term-missing --cov-fail-under=80
```

If coverage is below 80% on any module, add targeted tests until it passes. Identify and close gaps in:
- Any command module with <80% coverage
- `workspace/generator.py`
- `workspace/adopter.py`
- `intelligence/skills.py`

Run `ruff check src/ tests/` — fix all warnings.
Run `black --check src/ tests/` — fix all formatting.
Run `bandit -r src/ -ll` — fix any HIGH severity findings.

---

### Task 8.6 — README

Write `README.md` covering all sections from spec Section 18. The README must be accurate — every command example must work exactly as written.

Required working examples to verify before commit:
```bash
pip install -e .
ai-workspace --help
ai-workspace init --file tests/fixtures/greenfield/workspace.yaml --dry-run
ai-workspace validate --help
ai-workspace skills list
```

---

### Task 8.7 — Packaging

Ensure `pyproject.toml` is complete for distribution:
- All metadata: name, version, description, authors, license, classifiers
- `[project.urls]`: Homepage, Repository
- `package_data` for bundled skills, standards, templates
- Verify `pip install -e .` works cleanly in a fresh virtual environment
- Verify `ai-workspace --help` works after install

Write `scripts/install.sh`:
```bash
#!/bin/bash
set -e
pip install ai-workspace
echo "ai-workspace installed successfully"
ai-workspace --version
```

---

### Phase 8 Definition of Done

- [ ] `docs templates` lists all five built-in templates
- [ ] `docs create` works for all five template types
- [ ] ADR auto-numbering is correct
- [ ] `docs create` updates `docs-index.yaml`
- [ ] `handoff generate` creates correctly named file with all sections
- [ ] Global layer auto-initializes on first any command
- [ ] Five standards files are bundled and copied on init
- [ ] Full test suite passes: `pytest tests/` exits 0
- [ ] Coverage is 80%+ overall (`--cov-fail-under=80` passes)
- [ ] `ruff check src/ tests/` exits 0
- [ ] `black --check src/ tests/` exits 0
- [ ] `bandit -r src/ -ll` exits 0 (no HIGH severity)
- [ ] README is complete and all code examples are accurate
- [ ] `pip install -e .` works in a clean virtualenv
- [ ] `ai-workspace --help` lists all commands after install
- [ ] Every command from spec Section 11 works end-to-end

### Phase 8 Final Commit

```
git add .
git commit -m "phase-8: complete — docs, handoffs, packaging, README, 80% coverage

- docs create: five templates with ADR auto-numbering
- handoff generate: timestamped file with all spec sections
- Global layer auto-init on first command invocation
- Five bundled standards files
- Full test suite: 80%+ coverage enforced
- ruff, black, bandit all passing
- README with accurate working examples
- pip install -e . verified in clean virtualenv"
```

---

## Final Verification Checklist

Run all of the following before declaring the tool complete:

```bash
# Install clean
python -m venv /tmp/ai-workspace-verify
/tmp/ai-workspace-verify/bin/pip install -e .

# Core commands
/tmp/ai-workspace-verify/bin/ai-workspace --help
/tmp/ai-workspace-verify/bin/ai-workspace skills list
/tmp/ai-workspace-verify/bin/ai-workspace validate --help

# Init a real workspace
mkdir /tmp/test-project && cd /tmp/test-project
/tmp/ai-workspace-verify/bin/ai-workspace init --file <path-to-greenfield-fixture>
ls .ai/
cat .ai/start-here.md

# Validate it
/tmp/ai-workspace-verify/bin/ai-workspace validate
/tmp/ai-workspace-verify/bin/ai-workspace validate security

# Rebuild indexes
/tmp/ai-workspace-verify/bin/ai-workspace index rebuild

# Summarize
/tmp/ai-workspace-verify/bin/ai-workspace summarize

# Full test suite
pytest tests/ --cov=src/ai_workspace --cov-fail-under=80
```

All commands must exit 0. No Python tracebacks visible to the user. Tool is done.

---

## Phase Summary

| Phase | What Gets Built | Key Exit Criteria |
|---|---|---|
| Bootstrap | Repo, pyproject.toml, fixtures | `pip install -e .` works |
| 1 | Paths, config schema, filesystem, CLI skeleton | All core unit tests pass |
| 2 | Workspace generation, `init` command | `init --file` produces valid `.ai/` |
| 3 | Index schemas, index builder, `index rebuild` | Indexes populated from fixture docs |
| 4 | Tech detector, adopter, `adopt` command | `adopt` works on existing Python repo |
| 5 | Dependency summary, repo map, `summarize` | `summarize` generates three files |
| 6 | Skills system, five built-in skills, skills commands | `skills list` shows built-in skills |
| 7 | Workspace validator, security scanner, `validate` | Secret detection and pip-audit working |
| 8 | Docs commands, handoffs, README, packaging | 80% coverage, every command works |
