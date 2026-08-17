import json
import unittest
from pathlib import Path

from ci_guardrails.tools import _actionlint_findings, _zizmor_findings


class ToolParserTests(unittest.TestCase):
    def test_actionlint_diagnostic_is_normalized(self) -> None:
        findings = _actionlint_findings(
            ".github/workflows/ci.yml:12:5: invalid expression [expression]\n",
            Path.cwd(),
        )
        self.assertEqual("actionlint", findings[0].source)
        self.assertEqual("expression", findings[0].rule_id)
        self.assertEqual(12, findings[0].line)

    def test_zizmor_json_uses_symbolic_path_and_zero_based_row(self) -> None:
        payload = [{
            "ident": "template-injection",
            "desc": "code injection",
            "determinations": {"severity": "High"},
            "locations": [{
                "symbolic": {"key": {"Local": {"verbatim_path": "./.github/workflows/ci.yml"}}},
                "concrete": {"location": {"start_point": {"row": 6, "column": 8}}},
            }],
        }]
        findings = _zizmor_findings(json.dumps(payload), Path.cwd())
        self.assertEqual(".github/workflows/ci.yml", findings[0].path)
        self.assertEqual(7, findings[0].line)
        self.assertEqual("high", findings[0].severity)
