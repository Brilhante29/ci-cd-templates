import unittest
from pathlib import Path
from unittest.mock import patch

from ci_guardrails.models import Finding, ToolStatus
from ci_guardrails.scanner import scan, workflow_files

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

    def test_file_selection_parse_failure_and_external_adapter_path(self) -> None:
        self.assertEqual([], workflow_files(ROOT / "README.md"))
        malformed = ROOT / "benchmarks" / "fixtures" / "malformed.yml"
        self.assertEqual([malformed], workflow_files(malformed))

        external = Finding("actionlint", "rule", "high", "message", "<tool>")
        status = ToolStatus("actionlint", True, "1.0", "actionlint", 1, 1.0)
        with patch(
            "ci_guardrails.scanner.run_external_tools",
            return_value=([external], [status]),
        ):
            result = scan(malformed, include_external=True)

        self.assertIn("yaml-parse", {finding.rule_id for finding in result.findings})
        self.assertIn("rule", {finding.rule_id for finding in result.findings})
        self.assertEqual((status,), result.tools)
