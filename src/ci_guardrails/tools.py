from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import Finding, ToolStatus

_ACTIONLINT_DIAGNOSTIC = re.compile(r"^(?P<path>.+?):(?P<line>\d+):(?P<column>\d+): (?P<message>.*?)(?: \[(?P<rule>[^\]]+)\])?$")


def _version(command: str) -> str | None:
    try:
        completed = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0] if output else None


def _run(command: list[str], cwd: Path) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.perf_counter()
    environment = dict(os.environ)
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "ZIZMOR_GITHUB_TOKEN"):
        environment.pop(key, None)
    # ZIZMOR_OFFLINE backs a boolean flag, so it must hold a value clap can parse
    # as a bool. "1" makes zizmor exit 2 with a usage error, which the scanner
    # then reports as a high-severity "<tool>" finding and fails --strict.
    environment.update({"NO_COLOR": "1", "CI": "1", "ZIZMOR_OFFLINE": "true"})
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=environment,
        timeout=60,
        check=False,
    )
    return completed, (time.perf_counter() - started) * 1000


def _relative(path: Path, cwd: Path) -> str:
    try:
        return path.resolve().relative_to(cwd.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _actionlint_findings(output: str, cwd: Path) -> list[Finding]:
    findings: list[Finding] = []
    for line in output.splitlines():
        match = _ACTIONLINT_DIAGNOSTIC.match(line.strip())
        if not match:
            continue
        raw_path = Path(match.group("path"))
        path = raw_path if raw_path.is_absolute() else cwd / raw_path
        try:
            display_path = path.resolve().relative_to(cwd.resolve()).as_posix()
        except ValueError:
            display_path = raw_path.as_posix()
        rule = match.group("rule") or "actionlint"
        findings.append(
            Finding(
                source="actionlint",
                rule_id=rule,
                severity="high",
                message=match.group("message"),
                path=display_path,
                line=int(match.group("line")),
                column=int(match.group("column")),
            )
        )
    return findings


def _find_string(value: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(value, dict):
        for key in keys:
            found = value.get(key)
            if isinstance(found, (str, int, float)):
                return str(found)
        for child in value.values():
            found = _find_string(child, keys)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_string(child, keys)
            if found:
                return found
    return None


def _zizmor_findings(output: str, cwd: Path) -> list[Finding]:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    findings: list[Finding] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        ident = str(item.get("ident") or "zizmor")
        desc = str(item.get("desc") or item.get("message") or ident)
        determinations = item.get("determinations")
        severity_value = determinations.get("severity") if isinstance(determinations, dict) else "medium"
        severity = str(severity_value).lower()
        if severity not in {"low", "medium", "high"}:
            severity = "medium"
        locations = item.get("locations")
        location: dict[str, Any] = locations[0] if isinstance(locations, list) and locations else {}
        path = _find_string(location, ("verbatim_path", "path", "file")) or "<unknown>"
        line_value = _find_string(location, ("row", "line"))
        line = int(line_value) + 1 if line_value and line_value.isdigit() else None
        try:
            path = Path(path).resolve().relative_to(cwd.resolve()).as_posix()
        except (OSError, ValueError):
            path = Path(path).as_posix()
        findings.append(
            Finding(
                source="zizmor",
                rule_id=ident,
                severity=severity,  # type: ignore[arg-type]
                message=desc,
                path=path,
                line=line,
                details={"url": item.get("url")} if item.get("url") else {},
            )
        )
    return findings


def run_external_tools(paths: Iterable[Path], cwd: Path) -> tuple[list[Finding], list[ToolStatus]]:
    findings: list[Finding] = []
    statuses: list[ToolStatus] = []
    path_args = [_relative(path, cwd) for path in sorted(paths)]
    for name, parser in (("actionlint", _actionlint_findings), ("zizmor", _zizmor_findings)):
        executable = shutil.which(name)
        if executable is None:
            statuses.append(ToolStatus(name, False, None, None, None, 0.0))
            continue
        if name == "actionlint":
            command = [executable, *path_args]
        else:
            command = [executable, "--format=json-v1", "--no-progress", "--color=never", *path_args]
        try:
            completed, duration_ms = _run(command, cwd)
            output = completed.stdout or ""
            parsed = parser(output, cwd)
            if not parsed and completed.returncode != 0 and completed.stderr.strip():
                parsed = [
                    Finding(
                        source=name,
                        rule_id="tool-error",
                        severity="high",
                        message=completed.stderr.strip().splitlines()[-1][:500],
                        path="<tool>",
                    )
                ]
            findings.extend(parsed)
            statuses.append(
                ToolStatus(
                    name,
                    True,
                    _version(executable),
                    " ".join(command),
                    completed.returncode,
                    duration_ms,
                )
            )
        except (OSError, subprocess.SubprocessError) as exc:
            statuses.append(ToolStatus(name, True, _version(executable), " ".join(command), None, 0.0, str(exc)))
    return findings, statuses
