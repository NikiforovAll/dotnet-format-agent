# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **uv workspace** containing two Python packages:

1. **tde** (Tech-Debt Extractor) - CLI tool that runs `dotnet format` and outputs diagnostics in TOON format
2. **tda** (Tech-Debt Agent) - AI agent using claude-agent-sdk that wraps tde tools for conversational analysis

The workspace uses a unified lockfile and shared dependencies. Both packages use Python 3.12+.

## Architecture

### Workspace Structure

```
techdebt-agent/
├── pyproject.toml          # Workspace root with [tool.uv.workspace]
├── uv.lock                 # Unified lockfile for entire workspace
└── src/
    ├── tde/                # Package 1: Extractor
    │   ├── pyproject.toml
    │   └── src/tde/
    │       ├── runner.py   # Executes dotnet format, manages temp JSON reports
    │       ├── parser.py   # Parses JSON into Diagnostic TypedDict
    │       ├── formatter.py # Converts diagnostics to TOON format
    │       └── cli.py      # Click CLI with 'style' and 'analyzers' commands
    └── tda/                # Package 2: Agent
        ├── pyproject.toml  # Depends on tde via workspace = true
        └── src/tda/
            ├── tools.py    # @tool decorated functions wrapping tde
            ├── agent.py    # Creates SDK MCP server with tools
            └── cli.py      # Anyio-based CLI for agent queries
```

### Key Design Patterns

**TDE Package:**
- Uses Click for CLI with command groups (`style`, `analyzers`)
- `DotnetFormatRunner` creates temp JSON files, runs subprocess, cleans up
- Rich Console with automatic TTY detection for spinners (non-interactive mode = clean output)
- `--no-restore` hardcoded for performance
- Terminology: "diagnostic" (not "violation" or "error")

**TDA Package:**
- Uses `claude-agent-sdk` with `@tool` decorator pattern
- Tools call tde modules directly (not subprocess)
- MCP server created via `create_sdk_mcp_server()`
- Workspace dependency on tde ensures code reuse
- System prompt defined in `system_prompt.prompty` using Microsoft Prompty format
- `prompty` library loads and parses the system prompt at runtime
- System prompt uses `SystemPromptPreset` with `append` to preserve base Claude Code behavior
- **Important**: `append` field doesn't support multiline strings; prompts are collapsed to single line
- For `claude-agent-sdk` documentation, use Context7: `/anthropics/claude-agent-sdk-python`

**Data Flow:**
```
dotnet format --report temp.json
  → runner.py executes subprocess
    → parser.py: JSON → list[Diagnostic]
      → formatter.py: Diagnostic → TOON string
        → CLI outputs to stdout
```

## Common Commands

### Development

```bash
# Install workspace (both packages)
uv sync

# Run specific package
uv run --package tde tde --help
uv run --package tda tda --help

# Update dependencies
uv lock
```

### TDE (Extractor) Usage

```bash
# Extract style diagnostics
uv run --package tde tde style /path/to/dotnet/project

# Extract with options
uv run --package tde tde style /path/to/project --group-by file --summary
uv run --package tde tde analyzers /path/to/project --include "**/*.cs"

# Filter specific diagnostics
uv run --package tde tde style /path/to/project --diagnostics IDE0055 --diagnostics IDE1006
uv run --package tde tde analyzers /path/to/project --diagnostics CA1031

# Filter by severity
uv run --package tde tde style /path/to/project --severity error
uv run --package tde tde analyzers /path/to/project --severity warn
```

### TDA (Agent) Usage

```bash
# Query agent about diagnostics
uv run --package tda tda "Give me a summary of style diagnostics in ../path/to/project"

# With working directory
uv run --package tda tda "What are the most common analyzer diagnostics?" --cwd /path/to/project
```

## Important Notes

### Terminology
Always use "diagnostic" (not "violation", "error", or "issue") throughout the codebase. This was a deliberate design decision to align with .NET terminology.

### Workspace Dependencies
When adding dependencies:
- Add to individual package's `pyproject.toml`
- For cross-package deps, use `[tool.uv.sources]` with `workspace = true`
- Run `uv lock` after changes to update unified lockfile

### TOON Format
Output uses TOON (Terminal Object Notation) for 30-60% token reduction vs JSON. The `python-toon` library handles encoding. Structure varies by grouping:
- `group_by="error"`: Groups by rule ID with metadata line showing `{key, message, count}` followed by locations with `{location, severity}`
- `group_by="file"`: Groups by file path with full details for each diagnostic
- `summary=True`:
  - With `group_by="error"` (default): Shows `{key, message, count}`
  - With `group_by="file"`: Shows `{key, count}`

**Error grouping format:**
```
IDE0055:
{key,message,count}: IDE0055,Fix formatting,2
[2,]{location,severity}:
 file.cs:10,45,Warning
 ...
```

**Summary format (by error):**
```
[3,]{key,message,count}:
 IDE0055,Fix formatting,12
 CA1031,Do not catch general exception types,5
 ...
```

### Testing TDE Changes
To test changes to tde without affecting tda:
```bash
uv run --package tde tde style /path/to/test/project --summary
```

### Dotnet Format Integration
- Always use `--verify-no-changes` flag (exit code 2 = violations found)
- Always use `--verbosity quiet` (we parse JSON, not stdout)
- Always use `--report <temp-file>` for structured output
- Handle both list-based and dict-based JSON structures (dotnet format varies)
- Supports `--diagnostics` flag for filtering specific diagnostic IDs (same as dotnet format)
- Supports `--severity` flag for filtering by severity level: error, hidden, info, warn

### Agent Tools
When adding new tde functionality that should be accessible via tda:
1. Add to tde package first
2. Create `@tool` decorated function in `tda/tools.py`
3. Register in `tda/agent.py` server
4. Add to `allowed_tools` list in `tda/cli.py`

Tool naming convention: `extract_<type>_diagnostics`

### Rich Console
The spinner only appears in interactive terminals. When piped or redirected, output is clean (no ANSI codes). This is automatic via `console.is_terminal` check.

## Prerequisites

- Python 3.12+
- .NET SDK with `dotnet format` installed
- uv package manager
