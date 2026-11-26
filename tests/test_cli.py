"""CLI tests: exit codes, JSON output and secret redaction."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from envlens.cli import EXIT_ERROR, EXIT_ISSUES, EXIT_OK, main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.example = self.root / ".env.example"
        self.example.write_text("DB_HOST=\nAPI_KEY=\n", encoding="utf-8")
        self.env = self.root / ".env"
        self.env.write_text("DB_HOST=localhost\nAPI_KEY=test\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_check_ok_and_issue_exit_codes(self):
        code, out, _ = self.run_cli("check", str(self.example), str(self.env))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("OK:", out)
        self.env.write_text("DB_HOST=localhost\n", encoding="utf-8")
        code, out, _ = self.run_cli("check", str(self.example), str(self.env))
        self.assertEqual(code, EXIT_ISSUES)
        self.assertIn("FAIL:", out)

    def test_check_quiet_and_json(self):
        code, out, _ = self.run_cli("check", str(self.example), str(self.env), "--quiet")
        self.assertEqual((code, out), (EXIT_OK, ""))
        code, out, _ = self.run_cli("check", str(self.example), str(self.env), "--json")
        self.assertEqual(code, EXIT_OK)
        self.assertTrue(json.loads(out)["ok"])

    def test_diff_redacts_unless_show_values(self):
        other = self.root / "old.env"
        other.write_text("DB_HOST=previous\nAPI_KEY=topsecret\n", encoding="utf-8")
        code, out, _ = self.run_cli("diff", str(other), str(self.env), "--json")
        self.assertEqual(code, EXIT_ISSUES)
        self.assertNotIn("topsecret", out)
        self.assertIn("<redacted>", out)
        code, out, _ = self.run_cli(
            "diff", str(other), str(self.env), "--json", "--show-values"
        )
        self.assertIn("topsecret", out)

    def test_lint_strict(self):
        code, out, _ = self.run_cli("lint", str(self.env))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("weak-secret", out)
        code, _, _ = self.run_cli("lint", str(self.env), "--strict")
        self.assertEqual(code, EXIT_ISSUES)

    def test_missing_file_returns_error_code(self):
        code, _, err = self.run_cli("check", str(self.example), str(self.root / "nope"))
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("cannot read", err)

    def test_version(self):
        out = io.StringIO()
        with self.assertRaises(SystemExit) as ctx, redirect_stdout(out):
            main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("envlens 0.1.0", out.getvalue())


if __name__ == "__main__":
    unittest.main()
