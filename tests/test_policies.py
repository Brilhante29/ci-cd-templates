import tempfile
import unittest
from pathlib import Path

from ci_guardrails.policies import validate_workflow
from ci_guardrails.yaml_loader import load_workflow


class PolicyTests(unittest.TestCase):
    def _findings(self, content: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.yml"
            path.write_text(content, encoding="utf-8")
            return validate_workflow(load_workflow(path))

    def test_secure_workflow_has_no_local_findings(self) -> None:
        findings = self._findings(
            """name: secure
on: [push]
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
        with:
          persist-credentials: false
"""
        )
        self.assertEqual([], findings)

    def test_high_risk_workflow_reports_security_rules(self) -> None:
        findings = self._findings(
            """name: unsafe
on:
  pull_request_target: {}
permissions: write-all
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo '${{ github.event.pull_request.body }}'
"""
        )
        rule_ids = {finding.rule_id for finding in findings}
        self.assertTrue({"dangerous-trigger", "write-all-permissions", "unpinned-action", "script-injection"} <= rule_ids)

    def test_local_reusable_workflow_call_does_not_require_caller_timeout(self) -> None:
        findings = self._findings(
            """name: caller
on: [push]
permissions:
  contents: read
jobs:
  verify:
    uses: ./.github/workflows/reusable-python.yml
"""
        )
        self.assertEqual([], findings)

    def test_structural_and_credential_rules_are_reported(self) -> None:
        findings = self._findings(
            """name: ""
permissions: read-all
jobs:
  broken:
    steps:
      - uses: 123
      - uses: actions/checkout@1111111111111111111111111111111111111111
      - credentials: plaintext
"""
        )
        rule_ids = {finding.rule_id for finding in findings}
        self.assertTrue(
            {
                "workflow-name",
                "workflow-trigger",
                "permissions-type",
                "job-runner-required",
                "job-timeout",
                "action-ref-type",
                "checkout-credentials",
                "inline-credentials",
            }
            <= rule_ids
        )

    def test_missing_jobs_permissions_and_unpinned_action_are_reported(self) -> None:
        findings = self._findings("name: unsafe\non: push\n")
        self.assertEqual(
            {"missing-permissions", "jobs-required"},
            {finding.rule_id for finding in findings},
        )

        findings = self._findings(
            """name: unsafe
on: [push]
permissions: {}
jobs:
  test:
    runs-on: ubuntu-24.04
    timeout-minutes: 1
    steps:
      - uses: actions/checkout
"""
        )
        self.assertIn("unpinned-action", {finding.rule_id for finding in findings})
