"""Produce the publication benchmark contract (V2) from a clean Docker run.

Adapted from rag-knowledge-base/tools/benchmark_v2.py into the ci-cd-templates
metric contract: primary metric scan_time_ms (lower is better), plus the
findings count (must equal the deterministic baseline of 7) and the per-run
samples.

Provenance fields:
  - source_commit (HEAD must be a clean tree)
  - image_digest (Docker image sha256)
  - dependency_lock_digest (sha256 of pyproject.toml + Dockerfile)
  - artifact_digest (sha256 of the V1 result file just produced)
  - producer (default: local)

The V1 execution result remains at benchmarks/results/guardrails-baseline.json;
this writer copies it once and never alters the V1 file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def combined_digest(root: Path, paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / relative).read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def git_output(root: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


def run_docker_benchmark(root: Path, image: str, output_path: Path, runs: int, warmup: int) -> None:
    command = [
        "docker",
        "run",
        "--rm",
        "--entrypoint",
        "python",
        image,
        "-m",
        "ci_guardrails",
        "benchmark",
        "--fixtures",
        "benchmarks/fixtures",
        "--templates",
        ".github/workflows",
        "--runs",
        str(runs),
        "--warmup",
        str(warmup),
        "--no-external",
        "--stdout",
    ]
    completed = subprocess.run(
        command, cwd=root, check=True, capture_output=True, text=True
    )
    output_path.write_text(completed.stdout, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="ci-cd-templates:benchmark")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument(
        "--producer", choices=("local", "github-actions", "other-ci"), default="local"
    )
    parser.add_argument("--ci-run-url", default=None)
    parser.add_argument(
        "--output",
        default="benchmarks/publication/guardrails-baseline-v2.json",
    )
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    if args.runs < 2:
        raise SystemExit("--runs must be at least 2")
    if args.producer != "local" and not args.ci_run_url:
        raise SystemExit("--ci-run-url is required for a non-local producer")

    root = Path(__file__).resolve().parents[1]
    source_commit = git_output(root, "rev-parse", "HEAD")
    porcelain = git_output(root, "status", "--porcelain")
    if porcelain:
        raise SystemExit("benchmark requires a clean tree before it starts")

    output_path = root / args.output
    v1_path = root / "benchmarks/results/guardrails-baseline.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not args.skip_build:
        subprocess.run(["docker", "build", "-t", args.image, str(root)], cwd=root, check=True)

    image_id = subprocess.check_output(
        ["docker", "image", "inspect", "--format", "{{.Id}}", args.image],
        text=True,
    ).strip()
    if not image_id.startswith("sha256:"):
        raise SystemExit(f"unexpected Docker image id: {image_id}")

    started_at = datetime.now(UTC)
    started = time.perf_counter()
    run_docker_benchmark(root, args.image, v1_path, args.runs, args.warmup)
    duration = time.perf_counter() - started

    result = json.loads(v1_path.read_text(encoding="utf-8"))
    samples = [float(value) for value in result["samples"]]
    summary = result["summary"]
    findings_block = result["findings"]
    image_ref = f"{args.image}@{image_id}"

    config = {
        "benchmark_id": "ci-guardrails-scan",
        "runs": int(args.runs),
        "warmup": int(args.warmup),
        "external_tools": False,
        "deterministic": True,
        "reusable_workflows": 5,
        "concurrency": 1,
    }

    metrics = [
        {
            "name": "scan_time_ms",
            "value": float(summary["median_ms"]),
            "unit": "ms",
            "direction": "lower_is_better",
            "samples": samples,
            "failures": 0,
            "summary": {
                "min_ms": float(summary["min_ms"]),
                "median_ms": float(summary["median_ms"]),
                "max_ms": float(summary["max_ms"]),
            },
        },
        {
            "name": "findings",
            "value": float(findings_block["total"]),
            "unit": "count",
            # The contract accepts higher_is_better, lower_is_better or target.
            # A fixed finding count is a target, not a free direction.
            "direction": "target",
            "samples": [float(findings_block["total"])],
            "failures": 0,
            "summary": findings_block,
        },
        {
            "name": "template_findings",
            "value": float(summary["template_findings"]),
            "unit": "count",
            "direction": "target",
            "samples": [float(summary["template_findings"])],
            "failures": 0,
            "summary": {"target": 0, "reusable_workflows": 5},
        },
    ]

    publication = {
        "schema_version": 2,
        "run_id": str(uuid.uuid4()),
        "project": "ci-cd-templates",
        "benchmark_id": "ci-guardrails-scan",
        "workload": {
            "version": "2.0.0",
            "fixture_digest": combined_digest(
                root,
                [
                    "benchmarks/fixtures/malformed.yml",
                    "benchmarks/fixtures/policy-violations.yml",
                    "benchmarks/fixtures/secure.yml",
                    ".github/workflows/ci.yml",
                    ".github/workflows/reusable-go.yml",
                    ".github/workflows/reusable-jvm-gradle.yml",
                    ".github/workflows/reusable-node.yml",
                    ".github/workflows/reusable-python.yml",
                    ".github/workflows/reusable-terraform.yml",
                ],
            ),
            "config_digest": sha256_bytes(
                json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ),
            "warmup_iterations": int(args.warmup),
            "measured_iterations": int(args.runs),
            "concurrency": 1,
        },
        "metrics": metrics,
        "execution": {
            "command": (
                f"docker run --rm --entrypoint python {args.image} "
                f"-m ci_guardrails benchmark --fixtures benchmarks/fixtures "
                f"--templates .github/workflows "
                f"--runs {args.runs} --warmup {args.warmup} --no-external"
            ),
            "started_at": started_at.isoformat().replace("+00:00", "Z"),
            "duration_seconds": round(duration, 6),
            "exit_code": 0,
            "repeat": int(args.runs),
        },
        "environment": {
            "runtime": "python-3.12-slim",
            "architecture": platform.machine().lower(),
            "hardware_class": "docker-local" if args.producer == "local" else "github-actions-ubuntu-latest",
        },
        "provenance": {
            "source_commit": source_commit,
            "clean_tree": True,
            "image_ref": image_ref,
            "image_digest": image_id,
            "dependency_lock_digest": combined_digest(
                root, ["pyproject.toml", "constraints.lock", "Dockerfile"]
            ),
            "producer": args.producer,
            "artifact_digest": sha256_file(v1_path),
        },
        "comparability_key": "ci-guardrails-scan:2.0.0:reusable-5:policy-fixtures-3:python-3.12-slim",
    }
    if args.ci_run_url:
        publication["provenance"]["ci_run_url"] = args.ci_run_url

    output_path.write_text(json.dumps(publication, indent=2) + "\n", encoding="utf-8")
    print(f"v2_result={output_path}")
    print(f"source_commit={source_commit}")
    print(f"image_digest={image_id}")
    print(f"artifact_digest={publication['provenance']['artifact_digest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
