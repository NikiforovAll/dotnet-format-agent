# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
