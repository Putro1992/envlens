# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | Yes |

## Reporting a vulnerability

Please **do not** open a public issue for a security problem. Use GitHub's
private vulnerability reporting on this repository ("Security" → "Report a
vulnerability"), or contact the maintainer directly.

Include a reproduction, the affected version, and the impact. You can expect
an acknowledgement within a few days. Once fixed, we will publish a release
and credit the reporter unless they prefer to stay anonymous.

## Scope

envlens is designed to avoid leaking values in its own output: `diff` redacts
by default and `lint` never prints values. Reports about accidental value
disclosure, path traversal, or unsafe parsing are in scope. Reports that a
user put a real secret in a committed `.env` file are not a vulnerability in
this tool.
