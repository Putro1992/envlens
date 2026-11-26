"""Parsing and comparison logic for :mod:`envlens`.

The module deliberately depends only on the Python standard library so it can
be vendored into CI jobs and small container images without extra weight.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "Diagnostic",
    "EnvFile",
    "Change",
    "CheckReport",
    "DiffReport",
    "parse_env",
    "check",
    "diff",
    "lint",
    "REDACTED",
]

REDACTED = "<redacted>"
ERROR = "error"
WARNING = "warning"

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INLINE_COMMENT_RE = re.compile(r"\s+#.*$")
_SECRET_HINTS = (
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "TOKEN",
    "API_KEY",
    "PRIVATE_KEY",
    "ACCESS_KEY",
    "CREDENTIAL",
)
_WEAK_SECRETS = {
    "changeme", "change_me", "secret", "password", "test", "testing",
    "1234", "12345", "123456", "admin", "default", "placeholder", "xxx",
}


def _strip_inline_comment(text: str) -> str:
    """Remove a trailing ``# comment`` that sits outside quoted values."""
    quote = None
    for index, char in enumerate(text):
        if char in ("'", '"'):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        elif char == "#" and quote is None and (index == 0 or text[index - 1].isspace()):
            return text[:index]
    return text


@dataclass(frozen=True)
class Diagnostic:
    """A single problem found in an env file."""

    code: str
    message: str
    line: int = 0
    severity: str = WARNING
    source: str = ""

    def __str__(self) -> str:
        where = []
        if self.source:
            where.append(self.source)
        if self.line:
            where.append("line %d" % self.line)
        prefix = " ".join(where)
        return "%s: %s%s [%s]" % (
            self.severity,
            (prefix + ": ") if prefix else "",
            self.message,
            self.code,
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "severity": self.severity,
            "source": self.source,
        }


@dataclass
class EnvFile:
    """Parsed env file: ordered keys, their values, and parse diagnostics."""

    source: str
    values: Dict[str, str] = field(default_factory=dict)
    line_numbers: Dict[str, int] = field(default_factory=dict)
    diagnostics: List[Diagnostic] = field(default_factory=list)

    def __iter__(self):
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def __contains__(self, key: str) -> bool:
        return key in self.values

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.values.get(key, default)

    def keys(self):
        return self.values.keys()

    def items(self):
        return self.values.items()

    @property
    def errors(self) -> List[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == ERROR]


def parse_env(text: str, *, source: str = "<text>") -> EnvFile:
    """Parse dotenv-style text into an :class:`EnvFile`.

    Supports comments, blank lines, ``export KEY=value``, single/double quoted
    values and inline comments after unquoted values. Malformed lines are
    recorded as diagnostics instead of raising, so a whole file can be linted
    in one pass. Later definitions win, matching common dotenv implementations.
    """
    env = EnvFile(source=source)
    for lineno, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            env.diagnostics.append(
                Diagnostic(
                    "malformed-line",
                    "expected KEY=VALUE, got %r" % line[:60],
                    lineno,
                    ERROR,
                    source,
                )
            )
            continue

        key, _, raw_value = line.partition("=")
        key = key.strip()
        if not _KEY_RE.match(key):
            env.diagnostics.append(
                Diagnostic(
                    "invalid-key",
                    "invalid key %r (use letters, digits and underscores)" % key,
                    lineno,
                    ERROR,
                    source,
                )
            )
            continue

        value = _strip_inline_comment(raw_value.strip()).rstrip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        if key in env.values:
            env.diagnostics.append(
                Diagnostic(
                    "duplicate-key",
                    "duplicate key %r (first defined on line %d)"
                    % (key, env.line_numbers[key]),
                    lineno,
                    WARNING,
                    source,
                )
            )
        env.values[key] = value
        env.line_numbers[key] = lineno
    return env


def _normalize_ignore(ignore: Iterable[str]) -> set:
    return {k.strip() for k in (ignore or ()) if k and k.strip()}


@dataclass
class CheckReport:
    """Result of checking a target env file against a reference template."""

    reference: str
    target: str
    missing: List[str] = field(default_factory=list)
    extra: List[str] = field(default_factory=list)
    empty: List[str] = field(default_factory=list)
    diagnostics: List[Diagnostic] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing
            or self.extra
            or self.empty
            or any(d.severity == ERROR for d in self.diagnostics)
        )

    @property
    def issue_count(self) -> int:
        return len(self.missing) + len(self.extra) + len(self.empty) + len(
            [d for d in self.diagnostics if d.severity == ERROR]
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "ok": self.ok,
            "reference": self.reference,
            "target": self.target,
            "missing": self.missing,
            "extra": self.extra,
            "empty": self.empty,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }


def check(
    reference: EnvFile,
    target: EnvFile,
    *,
    allow_empty: bool = False,
    ignore: Iterable[str] = (),
) -> CheckReport:
    """Check that ``target`` declares every key in ``reference`` and nothing more."""
    ignored = _normalize_ignore(ignore)
    return CheckReport(
        reference=reference.source,
        target=target.source,
        missing=[k for k in reference if k not in target and k not in ignored],
        extra=[k for k in target if k not in reference and k not in ignored],
        empty=(
            []
            if allow_empty
            else [k for k in target if target.values[k] == "" and k not in ignored]
        ),
        diagnostics=list(reference.diagnostics) + list(target.diagnostics),
    )


@dataclass(frozen=True)
class Change:
    """One key-level difference between two env files."""

    key: str
    kind: str  # added | removed | changed
    old: Optional[str] = None
    new: Optional[str] = None
    line: int = 0

    def to_dict(self, *, reveal: bool = False) -> Dict[str, object]:
        def show(value):
            if value is None or reveal:
                return value
            return REDACTED

        return {
            "key": self.key,
            "kind": self.kind,
            "line": self.line,
            "old": show(self.old),
            "new": show(self.new),
        }

    def render(self, *, reveal: bool = False) -> str:
        def show(value):
            if value is None:
                return "(absent)"
            return repr(value) if reveal else REDACTED

        return "%-7s %s: %s -> %s" % (
            self.kind.upper(),
            self.key,
            show(self.old),
            show(self.new),
        )


@dataclass
class DiffReport:
    """Key-level differences between two env files."""

    old_source: str
    new_source: str
    changes: List[Change] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.changes

    def to_dict(self, *, reveal: bool = False) -> Dict[str, object]:
        return {
            "ok": self.ok,
            "old": self.old_source,
            "new": self.new_source,
            "counts": {
                "added": len(self.added),
                "removed": len(self.removed),
                "changed": len(self.changed),
            },
            "changes": [c.to_dict(reveal=reveal) for c in self.changes],
        }

    @property
    def added(self) -> List[Change]:
        return [c for c in self.changes if c.kind == "added"]

    @property
    def removed(self) -> List[Change]:
        return [c for c in self.changes if c.kind == "removed"]

    @property
    def changed(self) -> List[Change]:
        return [c for c in self.changes if c.kind == "changed"]


def diff(
    old: EnvFile,
    new: EnvFile,
    *,
    ignore: Iterable[str] = (),
) -> DiffReport:
    """Compare two env files by key. Values are never included unless revealed."""
    ignored = _normalize_ignore(ignore)
    changes: List[Change] = []
    for key in old:
        if key in ignored:
            continue
        if key not in new:
            changes.append(Change(key, "removed", old=old.get(key), line=old.line_numbers[key]))
        elif old.get(key) != new.get(key):
            changes.append(
                Change(key, "changed", old=old.get(key), new=new.get(key),
                       line=new.line_numbers[key])
            )
    for key in new:
        if key in ignored:
            continue
        if key not in old:
            changes.append(Change(key, "added", new=new.get(key), line=new.line_numbers[key]))
    return DiffReport(old_source=old.source, new_source=new.source, changes=changes)


def _looks_like_secret(key: str) -> bool:
    upper = key.upper()
    return any(hint in upper for hint in _SECRET_HINTS)


def lint(
    env: EnvFile,
    *,
    min_secret_length: int = 8,
) -> List[Diagnostic]:
    """Return parse problems plus empty values and weak-looking secrets."""
    diagnostics = list(env.diagnostics)
    for key, value in env.items():
        line = env.line_numbers.get(key, 0)
        if value == "":
            diagnostics.append(
                Diagnostic("empty-value", "key %r has an empty value" % key,
                           line, WARNING, env.source)
            )
            continue
        if _looks_like_secret(key) and (
            len(value) < min_secret_length or value.lower() in _WEAK_SECRETS
        ):
            diagnostics.append(
                Diagnostic(
                    "weak-secret",
                    "key %r looks like a secret but has a weak value" % key,
                    line,
                    WARNING,
                    env.source,
                )
            )
    return sorted(diagnostics, key=lambda d: (d.line, d.code))
