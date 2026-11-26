"""envlens - a zero-dependency lens for ``.env`` files.

Public API:
    parse_env, check, diff, lint, EnvFile, CheckReport, DiffReport, Diagnostic
"""

from .core import (
    CheckReport,
    Change,
    Diagnostic,
    DiffReport,
    EnvFile,
    check,
    diff,
    lint,
    parse_env,
)

__version__ = "0.1.0"

__all__ = [
    "CheckReport",
    "Change",
    "Diagnostic",
    "DiffReport",
    "EnvFile",
    "check",
    "diff",
    "lint",
    "parse_env",
    "__version__",
]
