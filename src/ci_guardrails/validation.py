from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from .scanner import scan

_PLACEHOLDER = re.compile(r"<[^>]+>|\bpending\b|\bTODO\b", re.IGNORECASE)


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a mapping")
    return value


def _require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate_project(root: Path, strict: bool = True) -> list[str]:
    root = root.resolve()
    failures: list[str] = []
    required = [
        "README.md",
        "REFERENCES.md",
        "project.yaml",
        "pyproject.toml",
        "constraints.lock",
        "Dockerfile",
        "sdd/spec.md",
        "sdd/architecture-decision.md",
        "sdd/technical-decision.md",
        "sdd/benchmark-plan.md",
        "sdd/agent-handoff.md",
        "sdd/reuse-improvement-review.md",
        ".github/workflows/ci.yml",
    ]
    for relative in required:
        _require((root / relative).is_file(), f"missing required file: {relative}", failures)

    readme = root / "README.md"
    if readme.is_file():
        content = readme.read_text(encoding="utf-8")
        _require(
            content.startswith("# CI/CD Templates: "),
            "README must open with the descriptive project title",
            failures,
        )
        _require("scan_time_ms" in content and "findings" in content, "README must report benchmark metrics", failures)

    for relative in ("project.yaml", "sdd/spec.md", "sdd/architecture-decision.md", "sdd/technical-decision.md", "sdd/benchmark-plan.md", "sdd/agent-handoff.md", "sdd/reuse-improvement-review.md"):
        path = root / relative
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            if relative == "project.yaml":
                content = re.sub(
                    r"(?m)^\s*evidence_status:\s*pending\s*$", "", content
                )
            _require(not _PLACEHOLDER.search(content), f"placeholder remains in {relative}", failures)

    manifest_path = root / "project.yaml"
    if manifest_path.is_file():
        try:
            manifest = _read_yaml(manifest_path)
            _require(manifest.get("id") == 24, "project.yaml id must be 24", failures)
            status = manifest.get("status")
            _require(
                status in {"implemented", "benchmarked", "published"},
                "project.yaml status is invalid",
                failures,
            )
            _require(manifest.get("benchmark", {}).get("primary_metric") == "scan_time_ms", "benchmark metric mismatch", failures)
            _require(manifest.get("release", {}).get("no_secret_default_path") is True, "default path must not require secrets", failures)
        except (OSError, TypeError, yaml.YAMLError) as exc:
            failures.append(f"project.yaml is invalid: {exc}")

    results_dir = root / "benchmarks" / "results"
    result_files = sorted(results_dir.glob("*.json")) if results_dir.is_dir() else []
    manifest_status = "missing"
    if manifest_path.is_file():
        try:
            manifest_status = _read_yaml(manifest_path).get("status", "missing")
        except (OSError, TypeError, yaml.YAMLError):
            pass
    if manifest_status == "published":
        _require(bool(result_files), "published project requires benchmark JSON", failures)
    for path in result_files:
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
            _require(result.get("metric") == "scan_time_ms", f"benchmark metric mismatch in {path.name}", failures)
            _require(isinstance(result.get("value"), (int, float)), f"benchmark value missing in {path.name}", failures)
            _require(isinstance(result.get("environment"), dict), f"benchmark environment missing in {path.name}", failures)
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"invalid benchmark JSON {path.name}: {exc}")

    dockerfile = root / "Dockerfile"
    if dockerfile.is_file():
        docker_content = dockerfile.read_text(encoding="utf-8").upper()
        for forbidden in ("AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN", "PASSWORD=", "PRIVATE_KEY"):
            _require(forbidden not in docker_content, f"Dockerfile contains credential material: {forbidden}", failures)

    workflow_dir = root / ".github" / "workflows"
    if workflow_dir.is_dir():
        result = scan(workflow_dir, include_external=True, deterministic=True)
        threshold = {"high": 3, "medium": 2, "low": 1}
        if strict:
            for finding in result.findings:
                if threshold.get(finding.severity, 0) >= 2:
                    failures.append(f"workflow guardrail: {finding.path}:{finding.line or 0}: {finding.message}")

    if strict and (root / "tests").is_dir():
        commands = (
            ("ruff", [sys.executable, "-m", "ruff", "check", "src", "tests", "tools"]),
            ("mypy", [sys.executable, "-m", "mypy", "src"]),
            (
                "coverage tests",
                [sys.executable, "-m", "coverage", "run", "-m", "unittest", "discover", "-s", "tests", "-v"],
            ),
            ("coverage report", [sys.executable, "-m", "coverage", "report", "--fail-under=90"]),
        )
        environment = {**os.environ, "PYTHONPATH": str(root / "src")}
        for label, command in commands:
            completed = subprocess.run(
                command,
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                output = completed.stderr or completed.stdout
                failures.append(f"{label} failed: {output[-1000:]}")
    return failures
