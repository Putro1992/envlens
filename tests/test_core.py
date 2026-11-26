"""Unit tests for the envlens core library."""

import unittest

from envlens import check, diff, lint, parse_env


class ParseEnvTests(unittest.TestCase):
    def test_basic_keys_and_export(self):
        env = parse_env("A=1\nexport B=two\n")
        self.assertEqual(env.values, {"A": "1", "B": "two"})
        self.assertEqual(env.line_numbers, {"A": 1, "B": 2})

    def test_comments_and_blank_lines(self):
        env = parse_env("# header\n\nA=1 # inline\n")
        self.assertEqual(env.values, {"A": "1"})

    def test_quoted_values_keep_hashes(self):
        env = parse_env('A="hello # world" # trailing\nB=\'x # y\'\n')
        self.assertEqual(env.values, {"A": "hello # world", "B": "x # y"})

    def test_hash_without_whitespace_is_value(self):
        env = parse_env("URL=https://example.com/#frag\n")
        self.assertEqual(env.get("URL"), "https://example.com/#frag")

    def test_duplicate_key_is_diagnostic_and_last_wins(self):
        env = parse_env("A=1\nA=2\n", source="dup.env")
        self.assertEqual(env.get("A"), "2")
        self.assertEqual([d.code for d in env.diagnostics], ["duplicate-key"])
        self.assertEqual(env.diagnostics[0].source, "dup.env")

    def test_malformed_and_invalid_lines(self):
        env = parse_env("broken line\n1BAD=x\nGOOD=y\n")
        self.assertEqual(env.values, {"GOOD": "y"})
        self.assertEqual(
            [d.code for d in env.diagnostics], ["malformed-line", "invalid-key"]
        )
        self.assertTrue(all(d.severity == "error" for d in env.errors))

    def test_empty_value(self):
        env = parse_env("EMPTY=\n")
        self.assertEqual(env.get("EMPTY"), "")


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.reference = parse_env("DB_HOST=\nDB_PORT=\nAPI_KEY=\n", source=".env.example")

    def test_complete_target_passes(self):
        target = parse_env("DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=abc\n")
        self.assertTrue(check(self.reference, target).ok)

    def test_missing_extra_and_empty(self):
        target = parse_env("DB_HOST=localhost\nEXTRA=1\nAPI_KEY=\n")
        report = check(self.reference, target)
        self.assertFalse(report.ok)
        self.assertEqual(report.missing, ["DB_PORT"])
        self.assertEqual(report.extra, ["EXTRA"])
        self.assertEqual(report.empty, ["API_KEY"])
        self.assertEqual(report.issue_count, 3)

    def test_allow_empty_and_ignore(self):
        target = parse_env("DB_HOST=localhost\nEXTRA=1\nAPI_KEY=\n")
        report = check(self.reference, target, allow_empty=True, ignore=["EXTRA", "DB_PORT"])
        self.assertTrue(report.ok)

    def test_to_dict_is_serializable(self):
        import json
        report = check(self.reference, parse_env("DB_HOST=a\nDB_PORT=b\nAPI_KEY=c\n"))
        self.assertTrue(json.loads(json.dumps(report.to_dict()))["ok"])


class DiffTests(unittest.TestCase):
    def test_added_removed_changed(self):
        old = parse_env("A=1\nB=2\nC=3\n", source="old")
        new = parse_env("A=1\nB=9\nD=4\n", source="new")
        report = diff(old, new)
        self.assertEqual([c.key for c in report.added], ["D"])
        self.assertEqual([c.key for c in report.removed], ["C"])
        self.assertEqual([c.key for c in report.changed], ["B"])
        self.assertFalse(report.ok)

    def test_values_are_redacted_by_default(self):
        report = diff(parse_env("A=old-secret"), parse_env("A=new-secret"), ignore=[])
        data = report.to_dict()
        self.assertEqual(data["changes"][0]["old"], "<redacted>")
        self.assertEqual(data["changes"][0]["new"], "<redacted>")
        revealed = report.to_dict(reveal=True)
        self.assertEqual(revealed["changes"][0]["old"], "old-secret")

    def test_ignore_and_identical_files(self):
        self.assertTrue(diff(parse_env("A=1"), parse_env("A=1")).ok)
        self.assertTrue(diff(parse_env("A=1\nB=2"), parse_env("A=1\nB=3"), ignore=["B"]).ok)


class LintTests(unittest.TestCase):
    def test_weak_secret_and_empty_value(self):
        env = parse_env("API_KEY=test\nEMPTY=\nSAFE_TOKEN=abcdefghijklmnop\n")
        codes = [d.code for d in lint(env)]
        self.assertEqual(codes, ["weak-secret", "empty-value"])

    def test_clean_file(self):
        env = parse_env("API_KEY=abcdefghijklmnop\nDEBUG=true\n")
        self.assertEqual(lint(env), [])


if __name__ == "__main__":
    unittest.main()
