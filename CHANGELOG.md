# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-11

### Added
- File operation tools (Read, Write, Edit, Glob, Grep, WebFetch) to agent
- Tool usage visibility in console output
- Documentation lookup support for CA*/IDE* diagnostic codes via WebFetch
- Compact parameter logging for debugging
- Claude Code settings configuration (`.claude/settings.json`)
- Bump-version skill for synchronized version management

### Changed
- Enable bypassPermissions mode to avoid permission prompts
- Terminology: "error" → "diagnostic" throughout codebase (group_by parameter, function names)
- Console log level from INFO to WARNING
- Suppress markdown_it logger noise (DEBUG/INFO)
- Disable thinking tokens (max_thinking_tokens=0) for cleaner output
- Remove spinner from interactive mode
- Compact CLAUDE.md (70% reduction, focus on essential info)
- System prompt enhanced with include parameter documentation and default severity 'warn'

### Fixed
- Include parameter handling: string '[]' and empty lists treated as None
- Diagnostics parameter handling: 'all' and '[]' strings properly processed

## [0.1.2] - 2025-01-10

### Added
- Diagnostic filtering by specific IDs using `--diagnostics` flag
- Severity filtering using `--severity` flag (error, hidden, info, warn)
- Error grouping now shows metadata line with key, message, and count
- Summary mode now includes diagnostic messages when grouped by error
- Python .gitignore file
- Comprehensive documentation (CLAUDE.md, quick_start.md)

### Changed
- Renamed package from tda to tde (Tech-Debt Extractor)
- Updated terminology from "violation/error" to "diagnostic" throughout
- TOON format for error grouping: metadata + locations
- Split into two packages: tde (extractor) and tda (agent)
- Created uv workspace architecture

### Fixed
- Spinner only appears in interactive terminals
- Clean output when piped or redirected
