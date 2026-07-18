from pathlib import Path
import unittest

from ci_guardrails.benchmark import run_benchmark


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkTests(unittest.TestCase):
    def test_result_contains_reproducibility_and_findings(self) -> None:
        result = run_benchmark(ROOT / "benchmarks" / "fixtures", runs=1, warmup=0, include_external=False)
        self.assertEqual("scan_time_ms", result["metric"])
        self.assertEqual(1, result["repeat"])
        self.assertEqual(3, result["summary"]["workflow_files"])
        self.assertGreater(result["findings"]["total"], 0)
        self.assertEqual(64, len(result["fixture"]["sha256"]))
