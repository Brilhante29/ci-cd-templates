from pathlib import Path
import unittest

from ci_guardrails.scanner import scan


ROOT = Path(__file__).resolve().parents[1]


class ScannerTests(unittest.TestCase):
    def test_fixture_scan_is_sorted_and_deterministic_without_external_tools(self) -> None:
        result = scan(ROOT / "benchmarks" / "fixtures", include_external=False, deterministic=True)
        self.assertEqual(list(result.files), sorted(result.files))
        self.assertGreaterEqual(result.counts()["total"], 5)
        self.assertEqual((), result.tools)
        self.assertEqual(result.findings, tuple(sorted(result.findings, key=lambda item: item.sort_key())))

    def test_missing_directory_is_empty(self) -> None:
        result = scan(ROOT / "does-not-exist", include_external=False)
        self.assertEqual((), result.files)
        self.assertEqual((), result.findings)
