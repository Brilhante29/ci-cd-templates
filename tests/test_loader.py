from pathlib import Path
import tempfile
import unittest

from ci_guardrails.yaml_loader import load_workflow


class LoaderTests(unittest.TestCase):
    def test_on_key_and_boolean_values_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.yml"
            path.write_text("name: demo\non: [push]\npermissions: {}\njobs: {}\n", encoding="utf-8")
            document = load_workflow(path)
        self.assertIn("on", document.data)
        self.assertNotIn(True, document.data)

    def test_parse_errors_include_location(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.yml"
            path.write_text("jobs: [", encoding="utf-8")
            with self.assertRaises(Exception) as context:
                load_workflow(path)
        self.assertIn("invalid YAML", str(context.exception))
