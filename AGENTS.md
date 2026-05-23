# AGENTS.md

## Development Guidelines

All development work in this project should ideally be run via `uv` using script mode.

### Script Mode Usage

Use `uv run` to execute scripts and commands:

```bash
# Run a Python script
uv run python script.py

# Run a command with dependencies
uv run my-command --flag value

# Run with specific Python version
uv run --python 3.12 python script.py
```

### Benefits

- **Isolation**: Each script runs in an isolated environment
- **Reproducibility**: Dependencies are explicitly managed via `pyproject.toml`
- **Speed**: `uv` provides fast package resolution and installation
- **Consistency**: All developers use the same tooling

### Project Setup

Ensure your `pyproject.toml` defines the necessary dependencies and scripts:

```toml
[project]
name = "stubby"
version = "0.1.0"
dependencies = [
    # list dependencies here
]

[tool.uv]
# configure uv settings if needed
```
