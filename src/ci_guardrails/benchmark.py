from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .scanner import scan, workflow_files
from .tools import _version


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _fixture_digest(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _command_line(include_external: bool) -> str:
    suffix = "" if include_external else " --no-external"
    return (
        "python -m ci_guardrails benchmark --fixtures benchmarks/fixtures "
        "--templates .github/workflows --runs 3 --warmup 1" + suffix
    )


def _environment() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(aliased=True),
        "processor": platform.processor() or "unknown",
        "actionlint": _version("actionlint") or "unavailable",
        "zizmor": _version("zizmor") or "unavailable",
        "ci": os.environ.get("CI", "false"),
    }


def run_benchmark(
    fixtures: Path,
    templates: Path = Path(".github/workflows"),
    runs: int = 3,
    warmup: int = 1,
    include_external: bool = True,
    deterministic: bool = True,
) -> dict[str, Any]:
    if runs < 1 or warmup < 0:
        raise ValueError("runs must be >= 1 and warmup must be >= 0")
    fixtures = fixtures.resolve()
    templates = templates.resolve()
    fixture_files = workflow_files(fixtures)
    template_files = workflow_files(templates)
    if not fixture_files:
        raise ValueError(f"no YAML fixtures found under {fixtures}")
    if not template_files:
        raise ValueError(f"no reusable workflows found under {templates}")
    for _ in range(warmup):
        scan(fixtures, include_external=include_external, deterministic=deterministic)
        template_scan = scan(
            templates, include_external=include_external, deterministic=deterministic
        )
        if template_scan.findings:
            raise ValueError("reusable workflows contain guardrail findings")

    samples: list[float] = []
    final_fixture_scan = None
    final_template_scan = None
    for _ in range(runs):
        started = time.perf_counter()
        final_fixture_scan = scan(
            fixtures, include_external=include_external, deterministic=deterministic
        )
        final_template_scan = scan(
            templates, include_external=include_external, deterministic=deterministic
        )
        samples.append((time.perf_counter() - started) * 1000)
    assert final_fixture_scan is not None and final_template_scan is not None
    if final_template_scan.findings:
        raise ValueError("reusable workflows contain guardrail findings")

    median_ms = statistics.median(samples)
    return {
        "schema_version": 1,
        "project": "#24 ci-cd-templates",
        "metric": "scan_time_ms",
        "value": round(median_ms, 3),
        "unit": "ms",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "command": _command_line(include_external),
        "repeat": runs,
        "warmup": warmup,
        "samples": [round(sample, 3) for sample in samples],
        "summary": {
            "min_ms": round(min(samples), 3),
            "median_ms": round(median_ms, 3),
            "max_ms": round(max(samples), 3),
            "fixture_workflows": len(fixture_files),
            "reusable_workflows": len(template_files) - 1,
            "scanned_workflows": len(fixture_files) + len(template_files),
            "findings": len(final_fixture_scan.findings),
            "template_findings": len(final_template_scan.findings),
        },
        "findings": {
            "total": len(final_fixture_scan.findings),
            "by_source": final_fixture_scan.source_counts(),
            "by_severity": final_fixture_scan.counts(),
        },
        "environment": _environment(),
        "fixture": {
            "path": _display_path(fixtures),
            "sha256": _fixture_digest(fixtures, fixture_files),
            "files": [path.relative_to(fixtures).as_posix() for path in fixture_files],
        },
        "templates": {
            "path": _display_path(templates),
            "sha256": _fixture_digest(templates, template_files),
            "files": [path.relative_to(templates).as_posix() for path in template_files],
            "findings": len(final_template_scan.findings),
        },
        "deterministic": deterministic,
        "external_tools": include_external,
    }


def write_result(result: dict[str, Any], output: Path | None, stdout: bool = False) -> None:
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if stdout:
        print(encoded, end="")
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
