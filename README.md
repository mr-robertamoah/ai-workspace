# ai-workspace

`ai-workspace` is a Python CLI for creating and maintaining an AI-native
engineering workspace so humans and AI agents can collaborate with durable
project context.

## Current Status

The repository currently includes:

- Bootstrap project structure
- Phase 1 core foundation
- CLI command scaffolding aligned with the implementation spec

## Development

Create a virtual environment and install the project in editable mode:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Run the unit tests:

```bash
.venv/bin/python -m pytest tests/unit
```
