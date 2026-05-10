# ai-workspace — Install & Try Everything

## Install

```bash
git clone <repo-url> ai-workspace
cd ai-workspace
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Verify:

```bash
.venv/bin/ai-workspace --help
```

---

## 1. Initialize a new project

```bash
mkdir /tmp/my-project && cd /tmp/my-project

# From a YAML file (non-interactive)
cat > workspace.yaml << 'EOF'
workspace:
  name: my-project
  type: single
language:
  primary: python
documentation:
  enabled: true
  structure: standard
ai:
  enabled: true
  adr: true
  handoffs: true
  tasks: true
EOF

ai-workspace init --file workspace.yaml
```

Inspect what was created:

```bash
ls .ai/
ls .ai/indexes/
cat .ai/start-here.md
```

Dry-run mode (nothing written):

```bash
ai-workspace init --file workspace.yaml --dry-run
```

---

## 2. Adopt an existing project

```bash
# Use the python-api fixture as a stand-in for a real project
cp -r <repo>/tests/fixtures/python-api /tmp/existing-project
cd /tmp/existing-project

ai-workspace adopt
```

Check what was detected and suggested:

```bash
cat .ai/generated/tech-detection.yaml
cat .ai/generated/repo-map-generated.md
```

Dry-run (detect only, write nothing):

```bash
ai-workspace adopt --dry-run
```

---

## 3. Rebuild indexes

```bash
cd /tmp/my-project
ai-workspace index rebuild
cat .ai/indexes/docs-index.yaml
```

---

## 4. Summarize the project

```bash
ai-workspace summarize
cat .ai/generated/dependency-summary.md
cat .ai/generated/repo-map-generated.md
```

---

## 5. Skills

```bash
# List all built-in skills
ai-workspace skills list

# Search by keyword or tag
ai-workspace skills search python
ai-workspace skills search terraform

# Show full details
ai-workspace skills show python-package
ai-workspace skills show adr-creation

# Propose a new skill (written to <name>-proposed/)
ai-workspace skills propose --name my-skill --description "My custom workflow" --tags "python,custom"

# Accept a proposed skill (renames <name>-proposed/ to <name>/)
ai-workspace skills accept my-skill
```

---

## 6. Documentation

```bash
# List available templates
ai-workspace docs templates

# Create an architecture overview
ai-workspace docs create architecture-overview --force

# Create an ADR (auto-numbered)
ai-workspace docs create adr --title "Use PostgreSQL"
ai-workspace docs create adr --title "Use Redis for caching"

# Check the files
ls docs/decisions/
cat docs/decisions/ADR-001-use-postgresql.md
```

---

## 7. Standards

```bash
# List all standards (shows global + any workspace overrides)
ai-workspace standards list

# View a standard
ai-workspace standards show python
ai-workspace standards show testing

# Create a workspace-level override (appended to global standard)
ai-workspace standards override python
cat .ai/standards/python.md

# Edit the override file, then view the merged result
echo -e "\n## Project Rule\n\nAll functions must have docstrings." >> .ai/standards/python.md
ai-workspace standards show python
# → shows global python standard + your project rule at the bottom
```

---

## 8. Validate

```bash
# Workspace health checks
ai-workspace validate

# Security scan (secrets, YAML safety, permissions, pip-audit, bandit)
ai-workspace validate security
```

Trigger a failure to see it in action:

```bash
echo 'api_key = "AKIAIOSFODNN7EXAMPLE1234"' >> .ai/notes.md
ai-workspace validate security
# → exits 1, shows secret-detection: fail
rm .ai/notes.md
```

---

## 9. Generate a handoff

```bash
ai-workspace handoff generate
# → prompts for: accomplished, current state, blockers, next steps, files modified, decisions made, tests passing

ls .ai/handoffs/
cat .ai/handoffs/*.md
```

---

## 10. Full workflow end-to-end

```bash
mkdir /tmp/demo && cd /tmp/demo

cat > workspace.yaml << 'EOF'
workspace:
  name: demo-app
  type: single
language:
  primary: python
documentation:
  enabled: true
  structure: standard
ai:
  enabled: true
  adr: true
  handoffs: true
  tasks: true
EOF

ai-workspace init --file workspace.yaml
ai-workspace summarize
ai-workspace index rebuild
ai-workspace docs create adr --title "Use SQLite for local dev"
ai-workspace standards override python
ai-workspace validate
ai-workspace validate security
ai-workspace skills list
ai-workspace handoff generate
```

---

## Run the test suite

```bash
cd <repo>
.venv/bin/python -m pytest tests/ -q
# → 197 passed, 83% coverage
```
