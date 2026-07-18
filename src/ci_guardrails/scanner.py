from __future__ import annotations

import time
from pathlib import Path

from .models import Finding, ScanResult, ToolStatus
from .policies import validate_workflow
from .tools import run_external_tools
from .yaml_loader import WorkflowParseError, load_workflow


def workflow_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in {".yml", ".yaml"} else []
    return sorted(
        path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalise_finding(finding: Finding) -> Finding:
    display_path = finding.path
    if not display_path.startswith("<"):
        display_path = _display_path(Path(display_path))
    if display_path == finding.path:
        return finding
    return Finding(
        source=finding.source,
        rule_id=finding.rule_id,
        severity=finding.severity,
        message=finding.message,
        path=display_path,
        line=finding.line,
        column=finding.column,
        details=finding.details,
    )


def scan(root: Path, include_external: bool = True, deterministic: bool = True) -> ScanResult:
    started = time.perf_counter()
    root = root.resolve()
    files = workflow_files(root)
    findings: list[Finding] = []
    parseable: list[Path] = []
    for path in files:
        try:
            document = load_workflow(path)
        except WorkflowParseError as exc:
            findings.append(
                Finding(
                    source="policy",
                    rule_id="yaml-parse",
                    severity="high",
                    message=str(exc),
                    path=_display_path(path),
                    line=exc.line,
                    column=exc.column,
                )
            )
            continue
        findings.extend(validate_workflow(document))
        parseable.append(path)

    statuses: list[ToolStatus] = []
    if include_external and files:
        external_findings, statuses = run_external_tools(parseable or files, Path.cwd())
        findings.extend(external_findings)
    findings = [_normalise_finding(finding) for finding in findings]
    findings.sort(key=Finding.sort_key)
    relative_files = tuple(_display_path(path) for path in files)
    return ScanResult(
        root=_display_path(root),
        files=relative_files,
        findings=tuple(findings),
        tools=tuple(statuses),
        duration_ms=(time.perf_counter() - started) * 1000,
        deterministic=deterministic,
    )
