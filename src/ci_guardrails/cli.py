from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .benchmark import run_benchmark, write_result
from .scanner import scan
from .validation import validate_project


def _root_from_file() -> Path:
    current = Path.cwd()
    if (current / "project.yaml").is_file():
        return current
    return Path(__file__).resolve().parents[2]


def _print_scan(result: object, output: Path | None) -> None:
    encoded = json.dumps(result.as_dict(), indent=2, sort_keys=True)  # type: ignore[attr-defined]
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


def _severity_threshold(value: str) -> int:
    return {"never": 99, "low": 1, "medium": 2, "high": 3, "any": 1}[value]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ci-guardrails", description="Guardrails for GitHub Actions workflows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="scan YAML workflows and optional external analyzers")
    scan_parser.add_argument("path", nargs="?", default=".github/workflows")
    scan_parser.add_argument("--output", type=Path)
    scan_parser.add_argument("--no-external", action="store_true")
    scan_parser.add_argument("--deterministic", action="store_true", default=False)
    scan_parser.add_argument("--fail-on", choices=("never", "low", "medium", "high", "any"), default="high")

    benchmark_parser = subparsers.add_parser("benchmark", help="measure a fixed local fixture set")
    benchmark_parser.add_argument("--fixtures", type=Path, default=Path("benchmarks/fixtures"))
    benchmark_parser.add_argument("--templates", type=Path, default=Path(".github/workflows"))
    benchmark_parser.add_argument("--output", type=Path, default=Path("benchmarks/results/guardrails-baseline.json"))
    benchmark_parser.add_argument("--stdout", action="store_true")
    benchmark_parser.add_argument("--runs", type=int, default=3)
    benchmark_parser.add_argument("--warmup", type=int, default=1)
    benchmark_parser.add_argument("--no-external", action="store_true")
    benchmark_parser.add_argument("--deterministic", action="store_true", default=True)

    validate_parser = subparsers.add_parser("validate", help="run the strict project release gate")
    validate_parser.add_argument("--root", type=Path, default=None)
    validate_parser.add_argument("--strict", action="store_true", default=False)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scan":
        scan_result = scan(
            Path(args.path),
            include_external=not args.no_external,
            deterministic=args.deterministic,
        )
        _print_scan(scan_result, args.output)
        threshold = _severity_threshold(args.fail_on)
        if args.fail_on == "any":
            return 1 if scan_result.findings else 0
        return (
            1
            if any(
                {"low": 1, "medium": 2, "high": 3}[finding.severity] >= threshold
                for finding in scan_result.findings
            )
            else 0
        )
    if args.command == "benchmark":
        benchmark_result = run_benchmark(
            args.fixtures,
            args.templates,
            args.runs,
            args.warmup,
            not args.no_external,
            args.deterministic,
        )
        write_result(
            benchmark_result,
            None if args.stdout else args.output,
            stdout=args.stdout,
        )
        if not args.stdout:
            print(
                json.dumps(
                    {
                        "output": args.output.as_posix(),
                        "findings": benchmark_result["findings"],
                    },
                    sort_keys=True,
                )
            )
        return 0
    root = args.root or _root_from_file()
    failures = validate_project(root, strict=args.strict)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print("strict project validation passed" if args.strict else "project validation passed")
    return 0
