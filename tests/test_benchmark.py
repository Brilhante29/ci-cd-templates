import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ci_guardrails.benchmark import run_benchmark, write_result

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkTests(unittest.TestCase):
    def test_result_contains_reproducibility_and_findings(self) -> None:
        result = run_benchmark(
            ROOT / "benchmarks" / "fixtures",
            ROOT / ".github" / "workflows",
            runs=1,
            warmup=0,
            include_external=False,
        )
        self.assertEqual("scan_time_ms", result["metric"])
        self.assertEqual(1, result["repeat"])
        self.assertEqual(3, result["summary"]["fixture_workflows"])
        self.assertEqual(5, result["summary"]["reusable_workflows"])
        self.assertEqual(0, result["summary"]["template_findings"])
        self.assertGreater(result["findings"]["total"], 0)
        self.assertEqual(64, len(result["fixture"]["sha256"]))
        self.assertEqual(64, len(result["templates"]["sha256"]))

    def test_rejects_invalid_counts_and_missing_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "runs must"):
            run_benchmark(ROOT / "benchmarks" / "fixtures", runs=0)
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory)
            with self.assertRaisesRegex(ValueError, "no YAML fixtures"):
                run_benchmark(empty, ROOT / ".github" / "workflows", warmup=0)
            with self.assertRaisesRegex(ValueError, "no reusable workflows"):
                run_benchmark(ROOT / "benchmarks" / "fixtures", empty, warmup=0)

    def test_rejects_template_findings_and_writes_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            unsafe = target / "unsafe.yml"
            unsafe.write_text("name: unsafe\non: push\njobs: {}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "reusable workflows"):
                run_benchmark(
                    ROOT / "benchmarks" / "fixtures",
                    target,
                    runs=1,
                    warmup=1,
                    include_external=False,
                )
            output = target / "result.json"
            stream = io.StringIO()
            with redirect_stdout(stream):
                write_result({"value": 1}, output, stdout=True)
            self.assertEqual({"value": 1}, json.loads(output.read_text()))
            self.assertIn('"value": 1', stream.getvalue())
