# envlens

[![CI](https://github.com/YOUR_USERNAME/envlens/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/envlens/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/envlens.svg)](https://pypi.org/project/envlens/)
[![Python versions](https://img.shields.io/pypi/pyversions/envlens.svg)](https://pypi.org/project/envlens/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**A zero-dependency lens for `.env` files.** Verify a deployment config against its
template, diff two configs key by key, and audit for weak secrets — without ever
printing secret values by accident.

It is a single small Python package (standard library only) with a CLI and a
typed library API. Useful in CI, in containers, and in local development.

## Why

Every project has a `.env.example` that silently rots: a key is added to production
but not to the template, a value is left blank, a token is set to `test`. `envlens`
turns that drift into a **non-zero exit code** with a precise, readable message.
Unlike a plain `diff`, it compares *keys*, understands dotenv syntax, and redacts
values by default — so pasting its output into an issue is safe.

## Features

- `check` — detect missing keys, unexpected keys, and empty values
- `diff` — added / removed / changed keys, values hidden unless `--show-values`
- `lint` — duplicate or malformed lines, empty values, weak-looking secrets
- JSON output for every command (`--json`) and CI-friendly exit codes
- Dotenv syntax: comments, inline comments, `export KEY=value`, quoted values
- Zero runtime dependencies, typed API, Python 3.9+

## Install

```bash
python -m pip install envlens
```

Or run it from a checkout with no install at all:

```bash
PYTHONPATH=src python3 -m envlens --help
```

## Quick start

Given the two files in [`examples/`](examples):

```dotenv
# .env.example
DB_HOST=
DB_PORT=
API_KEY=
DEBUG=false
```

```bash
$ envlens check examples/.env.example examples/.env
OK: examples/.env matches examples/.env.example
```

```bash
$ envlens lint examples/.env
OK: examples/.env looks clean
```

```bash
$ envlens diff examples/.env.example examples/.env
4 change(s) between examples/.env.example and examples/.env:
  CHANGED DB_HOST: <redacted> -> <redacted>
  CHANGED DB_PORT: <redacted> -> <redacted>
  CHANGED API_KEY: <redacted> -> <redacted>
  CHANGED DEBUG: <redacted> -> <redacted>
  (values hidden; pass --show-values to reveal)
```

A failing check is explicit and machine-readable:

```bash
$ envlens check examples/.env.example examples/broken.env --json
{
  "diagnostics": [],
  "empty": [
    "API_KEY"
  ],
  "extra": [
    "LEGACY_FLAG"
  ],
  "missing": [
    "DB_PORT",
    "DEBUG"
  ],
  "ok": false,
  "reference": "examples/.env.example",
  "target": "examples/broken.env"
}
$ echo $?
1
```

## Commands

| Command | Purpose | Notable flags |
| --- | --- | --- |
| `check REFERENCE TARGET` | Validate a real env file against a template | `--allow-empty`, `--ignore KEY,...`, `--json`, `-q` |
| `diff OLD NEW` | Compare two env files by key | `--show-values`, `--ignore KEY,...`, `--json` |
| `lint FILE` | Find empty values and weak-looking secrets | `--strict`, `--min-secret-length N`, `--json` |

Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | No problems found |
| `1` | Problems found (check / diff / `lint --strict`) |
| `2` | Could not read a file or invalid usage |

## Use it in CI

```yaml
- name: Validate environment template
  run: |
    cp .env.example .env.ci
    # fill required values in .env.ci in your pipeline
    python -m pip install envlens
    envlens check .env.example .env.ci
```

Because `check` exits `1` on drift, it fails the job automatically. Add
`--json` if you want to archive the result as a CI artifact.

## Library usage

```python
from envlens import parse_env, check, diff, lint, REDACTED

template = parse_env(open(".env.example").read(), source=".env.example")
config = parse_env(open(".env").read(), source=".env")

report = check(template, config)
if not report.ok:
    print(report.missing, report.extra, report.empty)

changes = diff(template, config)
for change in changes.changes:
    print(change.key, change.kind)          # values stay hidden
print(changes.to_dict(reveal=True))          # opt-in disclosure

issues = lint(config, min_secret_length=12)
```

`parse_env` never raises on a bad line: it records `Diagnostic` objects with a
code, message, line number and severity, so tools can report a whole file at once.

## Security notes

- `diff` redacts every value by default. Revealing requires the explicit
  `--show-values` flag or `reveal=True` in the API.
- `lint` never prints a secret value; it only says that a value looks weak.
- `check` prints key names, not values — key names are generally not secret.
- Please do not put real production secrets in files you commit. `.env` is in
  this repository's `.gitignore` for a reason.

## Development

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
PYTHONPATH=src python3 -m envlens --help
```

The project intentionally keeps **zero runtime dependencies**. New features
should be implementable with the standard library; tests use `unittest`.

## Contributing

Contributions are welcome — start with [`CONTRIBUTING.md`](CONTRIBUTING.md) and
the open issues labeled `good first issue`. Please report security problems
privately as described in [`SECURITY.md`](SECURITY.md).

## Roadmap

- [ ] `--format json|text|github` annotation output for GitHub Actions
- [ ] Custom rules via a small config file
- [ ] Optional `.env` writer preserving comments
- [ ] More secret-shape heuristics contributed by users

## License

MIT © Dhani Putro Nugroho. See [LICENSE](LICENSE).
