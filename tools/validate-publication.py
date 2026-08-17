from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "benchmarks/results/guardrails-baseline.json"
V2_PATH = ROOT / "benchmarks/publication/guardrails-baseline-v2.json"
FIXTURE_PATHS = [
    "benchmarks/fixtures/malformed.yml",
    "benchmarks/fixtures/policy-violations.yml",
    "benchmarks/fixtures/secure.yml",
]
WORKFLOW_PATHS = [
    ".github/workflows/ci.yml",
    ".github/workflows/reusable-go.yml",
    ".github/workflows/reusable-jvm-gradle.yml",
    ".github/workflows/reusable-node.yml",
    ".github/workflows/reusable-python.yml",
    ".github/workflows/reusable-terraform.yml",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def git_blob(commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
        capture_output=True,
        check=False,
    )
    require(completed.returncode == 0, f"source commit lacks {path}")
    return completed.stdout


def combined_source_digest(commit: str, paths: list[str]) -> str:
    value = hashlib.sha256()
    for path in paths:
        value.update(path.encode("utf-8"))
        value.update(b"\0")
        value.update(git_blob(commit, path))
        value.update(b"\0")
    return "sha256:" + value.hexdigest()


def source_set_digest(commit: str, root: str, paths: list[str]) -> str:
    value = hashlib.sha256()
    prefix = root.rstrip("/") + "/"
    for path in paths:
        value.update(path.removeprefix(prefix).encode("utf-8"))
        value.update(git_blob(commit, path))
    return value.hexdigest()


def main() -> None:
    manifest = (ROOT / "project.yaml").read_text(encoding="utf-8")
    if re.search(r"(?m)^status:\s*published\s*$", manifest) is None:
        print("publication_evidence=not-applicable")
        return

    require(V1_PATH.is_file(), "published project requires V1 evidence")
    require(V2_PATH.is_file(), "published project requires V2 evidence")
    v1 = json.loads(V1_PATH.read_text(encoding="utf-8"))
    v2 = json.loads(V2_PATH.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / ".portfolio/contracts/benchmark-result-v2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(v2)

    require(v2["project"] == "ci-cd-templates", "unexpected V2 project")
    require(v2["execution"]["repeat"] == 3, "publication requires three runs")
    metrics = {metric["name"]: metric for metric in v2["metrics"]}
    require(metrics["scan_time_ms"]["value"] == v1["value"], "V1/V2 latency mismatch")
    require(metrics["scan_time_ms"]["samples"] == v1["samples"], "V1/V2 samples mismatch")
    require(metrics["findings"]["value"] == 7, "policy fixture finding count drifted")
    require(metrics["template_findings"]["value"] == 0, "templates contain findings")
    require(all(metric["failures"] == 0 for metric in metrics.values()), "V2 contains failures")
    require(v1["summary"]["reusable_workflows"] == 5, "expected five reusable workflows")
    require(v1["summary"]["template_findings"] == 0, "V1 templates contain findings")

    commit = v2["provenance"]["source_commit"]
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "invalid source commit")
    require(
        v2["workload"]["fixture_digest"]
        == combined_source_digest(commit, FIXTURE_PATHS + WORKFLOW_PATHS),
        "source fixture/workflow digest mismatch",
    )
    require(
        v1["fixture"]["sha256"]
        == source_set_digest(commit, "benchmarks/fixtures", FIXTURE_PATHS),
        "V1 fixture digest mismatch",
    )
    require(
        v1["templates"]["sha256"]
        == source_set_digest(commit, ".github/workflows", WORKFLOW_PATHS),
        "V1 template digest mismatch",
    )
    require(
        v2["provenance"]["dependency_lock_digest"]
        == combined_source_digest(commit, ["pyproject.toml", "constraints.lock", "Dockerfile"]),
        "dependency lock digest mismatch",
    )
    require(
        v2["provenance"]["artifact_digest"] == digest(V1_PATH.read_bytes()),
        "V1 artifact digest mismatch",
    )
    for field in ("image_digest", "artifact_digest"):
        require(
            re.fullmatch(r"sha256:[0-9a-f]{64}", v2["provenance"][field]) is not None,
            f"invalid {field}",
        )
    require(
        v2["provenance"]["image_ref"].endswith(v2["provenance"]["image_digest"]),
        "image reference and digest disagree",
    )
    require(
        "publication_result_path: benchmarks/publication/guardrails-baseline-v2.json"
        in manifest,
        "project manifest does not point to V2 evidence",
    )
    serialized = json.dumps({"v1": v1, "v2": v2})
    for forbidden in ("C:\\Users\\", "github" + "_pat_", "gh" + "p_"):
        require(forbidden not in serialized, f"forbidden value in evidence: {forbidden}")
    print("publication_evidence=passed")


if __name__ == "__main__":
    main()
