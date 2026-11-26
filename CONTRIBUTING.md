# Contributing to envlens

Thanks for helping improve envlens. This project is intentionally small, so a
good contribution is usually **one focused change with tests**.

## Getting set up

```bash
git clone https://github.com/Putro1992/envlens.git
cd envlens
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

Python 3.9+ is required. There are no runtime dependencies.

## Ground rules

- **Zero runtime dependencies.** Use the standard library; argue first if a
  feature truly needs a dependency.
- **Secrets stay secret.** Never reveal values in default output, examples,
  tests, or issues. Use obviously fake values such as `abcdefghijklmnop`.
- **Tests for behaviour changes.** Add a `unittest` case in `tests/`; run the
  whole suite before opening a PR.
- **Type hints** on public functions, and a docstring explaining *why* for
  anything non-obvious.
- Keep the CLI exit codes stable: `0` ok, `1` issues found, `2` read/usage error.

## Pull requests

1. Fork and create a branch: `git checkout -b fix/quoted-inline-comment`.
2. Make the change and add tests.
3. Run `python -m unittest discover -s tests -v` and a CLI smoke test.
4. Open a PR describing the problem, the fix, and how you verified it.
5. Link the issue if there is one (`Closes #123`).

Use conventional commit subjects where practical: `fix:`, `feat:`, `docs:`,
`test:`, `refactor:`, `chore:`.

## Reporting bugs

Use the bug report template and include:
- Python version and OS,
- a minimal `.env` file that reproduces the problem (fake values only),
- the exact command and actual vs expected output.

## Releasing (maintainers)

1. Update the version in `pyproject.toml` **and** `src/envlens/__init__.py`.
2. Add a section to `CHANGELOG.md`.
3. Merge to `main`, then tag: `git tag -a v0.1.0 -m v0.1.0 && git push --tags`.
4. Publish a GitHub release — `release.yml` builds and uploads to PyPI via
   trusted publishing (configure the PyPI publisher for the repo once).

## Code of conduct

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
