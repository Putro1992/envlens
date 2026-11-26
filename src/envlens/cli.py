"""Command line interface for :mod:`envlens`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__
from .core import CheckReport, Diagnostic, EnvFile, check, diff, lint, parse_env

__all__ = ["build_parser", "main", "render_check", "render_diff", "render_lint"]

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2


def _read(path: str) -> Optional[str]:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        print("envlens: cannot read %s: %s" % (path, exc), file=sys.stderr)
        return None


def _parse(path: str) -> Optional[EnvFile]:
    text = _read(path)
    if text is None:
        return None
    return parse_env(text, source=path)


def _keys(value: str) -> List[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def render_check(report: CheckReport) -> str:
    """Render a check report as human-readable text."""
    if report.ok:
        lines = ["OK: %s matches %s" % (report.target, report.reference)]
    else:
        lines = [
            "FAIL: %s vs %s (%d issue(s))"
            % (report.target, report.reference, report.issue_count)
        ]
    if report.missing:
        lines.append("  missing keys: " + ", ".join(report.missing))
    if report.extra:
        lines.append("  unexpected keys: " + ", ".join(report.extra))
    if report.empty:
        lines.append("  empty values: " + ", ".join(report.empty))
    for diagnostic in report.diagnostics:
        lines.append("  " + str(diagnostic))
    return "\n".join(lines)


def render_diff(report, *, reveal: bool = False) -> str:
    """Render a diff report as human-readable text."""
    if report.ok:
        return "OK: no key differences between %s and %s" % (
            report.old_source, report.new_source
        )
    lines = [
        "%d change(s) between %s and %s:"
        % (len(report.changes), report.old_source, report.new_source)
    ]
    lines.extend("  " + change.render(reveal=reveal) for change in report.changes)
    if not reveal:
        lines.append("  (values hidden; pass --show-values to reveal)")
    return "\n".join(lines)


def render_lint(path: str, diagnostics: List[Diagnostic]) -> str:
    """Render lint diagnostics as human-readable text."""
    if not diagnostics:
        return "OK: %s looks clean" % path
    lines = ["%d issue(s) in %s:" % (len(diagnostics), path)]
    lines.extend("  " + str(diagnostic) for diagnostic in diagnostics)
    return "\n".join(lines)


def _cmd_check(args: argparse.Namespace) -> int:
    reference = _parse(args.reference)
    target = _parse(args.target)
    if reference is None or target is None:
        return EXIT_ERROR
    report = check(
        reference,
        target,
        allow_empty=args.allow_empty,
        ignore=_keys(args.ignore),
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    elif not args.quiet:
        print(render_check(report))
    return EXIT_OK if report.ok else EXIT_ISSUES


def _cmd_diff(args: argparse.Namespace) -> int:
    old = _parse(args.old)
    new = _parse(args.new)
    if old is None or new is None:
        return EXIT_ERROR
    report = diff(old, new, ignore=_keys(args.ignore))
    if args.json:
        print(json.dumps(report.to_dict(reveal=args.show_values), indent=2, sort_keys=True))
    else:
        print(render_diff(report, reveal=args.show_values))
    return EXIT_OK if report.ok else EXIT_ISSUES


def _cmd_lint(args: argparse.Namespace) -> int:
    env = _parse(args.file)
    if env is None:
        return EXIT_ERROR
    diagnostics = lint(env, min_secret_length=args.min_secret_length)
    if args.json:
        print(json.dumps([d.to_dict() for d in diagnostics], indent=2, sort_keys=True))
    else:
        print(render_lint(args.file, diagnostics))
    if not diagnostics:
        return EXIT_OK
    return EXIT_ISSUES if args.strict else EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser (useful for docs and tests)."""
    parser = argparse.ArgumentParser(
        prog="envlens",
        description=(
            "A zero-dependency lens for .env files: verify, diff and audit "
            "configuration without leaking secrets."
        ),
    )
    parser.add_argument("--version", action="version", version="envlens " + __version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    cmd_check = subparsers.add_parser(
        "check", help="verify a .env file against a .env.example template"
    )
    cmd_check.add_argument("reference", help="template file, e.g. .env.example")
    cmd_check.add_argument("target", help="file to verify, e.g. .env")
    cmd_check.add_argument("--allow-empty", action="store_true", help="allow blank values")
    cmd_check.add_argument("--ignore", default="", help="comma-separated keys to skip")
    cmd_check.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    cmd_check.add_argument("-q", "--quiet", action="store_true", help="suppress text output")
    cmd_check.set_defaults(func=_cmd_check)

    cmd_diff = subparsers.add_parser("diff", help="compare two env files key by key")
    cmd_diff.add_argument("old", help="older / baseline env file")
    cmd_diff.add_argument("new", help="newer env file")
    cmd_diff.add_argument("--ignore", default="", help="comma-separated keys to skip")
    cmd_diff.add_argument(
        "--show-values", action="store_true", help="reveal values (hidden by default)"
    )
    cmd_diff.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    cmd_diff.set_defaults(func=_cmd_diff)

    cmd_lint = subparsers.add_parser("lint", help="find empty values and weak-looking secrets")
    cmd_lint.add_argument("file", help="env file to audit")
    cmd_lint.add_argument("--strict", action="store_true", help="exit 1 when issues are found")
    cmd_lint.add_argument(
        "--min-secret-length", type=int, default=8, help="minimum length for secret values"
    )
    cmd_lint.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    cmd_lint.set_defaults(func=_cmd_lint)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point returning a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except BrokenPipeError:
        return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
