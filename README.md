# dotnet-format-agent

A Python workspace containing two packages for code quality analysis:

- **tde** (Tech-Debt Extractor) - CLI tool that runs `dotnet format` and outputs diagnostics in TOON format
- **tda** (Tech-Debt Agent) - AI agent using claude-agent-sdk for conversational codebase analysis

## Prerequisites

- Python 3.12+
- .NET SDK with `dotnet format`
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

```bash
uv sync
```

## Usage

### TDE - Direct Extraction

```bash
# Extract style diagnostics
uv run --package tde tde style /path/to/dotnet/project

# Extract analyzer diagnostics with grouping
uv run --package tde tde analyzers /path/to/project --group-by file --summary
```

**Options:**
- `--group-by`: Group by `error` (default) or `file`
- `--summary`: Show only counts instead of full details
- `--include`: File patterns to include (can be specified multiple times)
- `--diagnostics`: Filter to specific diagnostic IDs (e.g., `IDE0055`, `CA1031`)
- `--severity`: Filter by severity level (`error`, `hidden`, `info`, `warn`)

### TDA - AI Agent

```bash
# Query agent about diagnostics
uv run --package tda tda "Give me a summary of style diagnostics in ../my-project"

# Specify working directory
uv run --package tda tda "What are the most common issues?" --cwd /path/to/project
```

## TOON Format

Output uses [TOON (Terminal Object Notation)](https://github.com/xaviviro/python-toon) for 30-60% fewer tokens vs JSON - optimized for LLM consumption.

## Development

See [CLAUDE.md](CLAUDE.md) for architecture details and development guidance.

## License

MIT
