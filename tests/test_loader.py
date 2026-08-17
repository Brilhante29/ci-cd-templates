import tempfile
import unittest
from pathlib import Path

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

    def test_non_mapping_and_invalid_utf8_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sequence = root / "sequence.yml"
            sequence.write_text("- not-a-workflow\n", encoding="utf-8")
            with self.assertRaisesRegex(Exception, "must be a YAML mapping"):
                load_workflow(sequence)

            invalid = root / "invalid.yml"
            invalid.write_bytes(b"\xff\xfe")
            with self.assertRaisesRegex(Exception, "not valid UTF-8"):
                load_workflow(invalid)
