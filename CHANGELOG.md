# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- GitHub Actions annotation output
- Configurable lint rules

## [0.1.0] - 2026-11-26

### Added
- `parse_env` with comments, inline comments, `export` prefixes and quoted values
- `check` command with missing / extra / empty key detection and JSON output
- `diff` command with key-level changes and redacted values by default
- `lint` command for empty values, duplicate keys and weak-looking secrets
- CI matrix across Python 3.9-3.13 on Linux, macOS and Windows
- PyPI release workflow using trusted publishing
- 22 unit and CLI tests

[Unreleased]: https://github.com/Putro1992/envlens/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Putro1992/envlens/releases/tag/v0.1.0
