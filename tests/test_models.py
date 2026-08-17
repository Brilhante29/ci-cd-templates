import unittest

from ci_guardrails.models import Finding, ScanResult, ToolStatus


class ModelTests(unittest.TestCase):
    def test_findings_and_scan_result_serialize_stably(self) -> None:
        finding = Finding(
            source="policy",
            rule_id="rule",
            severity="high",
            message="message",
            path="workflow.yml",
            line=2,
            column=3,
            details={"context": "unsafe"},
        )
        tool = ToolStatus("actionlint", True, "1.0", "actionlint x", 0, 1.23456)
        result = ScanResult(
            root=".",
            files=("workflow.yml",),
            findings=(finding,),
            tools=(tool,),
            duration_ms=2.34567,
            deterministic=True,
        )

        payload = result.as_dict()

        self.assertEqual("policy:rule:workflow.yml:2:3", finding.fingerprint())
        self.assertEqual("unsafe", payload["findings"][0]["details"]["context"])
        self.assertEqual({"total": 1, "high": 1, "medium": 0, "low": 0}, result.counts())
        self.assertEqual({"policy": 1}, result.source_counts())
        self.assertEqual(1.235, payload["tools"][0]["duration_ms"])
        self.assertEqual(2.346, payload["duration_ms"])

    def test_empty_details_are_omitted(self) -> None:
        finding = Finding("policy", "rule", "low", "message", "workflow.yml")
        self.assertNotIn("details", finding.as_dict())
        self.assertEqual(("workflow.yml", 0, 0, "policy", "rule"), finding.sort_key())
