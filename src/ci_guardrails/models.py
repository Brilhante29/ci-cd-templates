from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Severity = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class Finding:
    source: str
    rule_id: str
    severity: Severity
    message: str
    path: str
    line: int | None = None
    column: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def sort_key(self) -> tuple[str, int, int, str, str]:
        return (
            self.path,
            self.line or 0,
            self.column or 0,
            self.source,
            self.rule_id,
        )

    def fingerprint(self) -> str:
        return ":".join(
            [self.source, self.rule_id, self.path, str(self.line or 0), str(self.column or 0)]
        )

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "source": self.source,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "fingerprint": self.fingerprint(),
        }
        if self.details:
            result["details"] = self.details
        return result


@dataclass(frozen=True)
class ToolStatus:
    name: str
    available: bool
    version: str | None
    command: str | None
    exit_code: int | None
    duration_ms: float
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "version": self.version,
            "command": self.command,
            "exit_code": self.exit_code,
            "duration_ms": round(self.duration_ms, 3),
            "error": self.error,
        }


@dataclass(frozen=True)
class ScanResult:
    root: str
    files: tuple[str, ...]
    findings: tuple[Finding, ...]
    tools: tuple[ToolStatus, ...]
    duration_ms: float
    deterministic: bool

    def counts(self) -> dict[str, int]:
        return {
            "total": len(self.findings),
            "high": sum(f.severity == "high" for f in self.findings),
            "medium": sum(f.severity == "medium" for f in self.findings),
            "low": sum(f.severity == "low" for f in self.findings),
        }

    def source_counts(self) -> dict[str, int]:
        return {
            source: sum(f.source == source for f in self.findings)
            for source in sorted({f.source for f in self.findings})
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "root": self.root,
            "deterministic": self.deterministic,
            "files": list(self.files),
            "findings": [finding.as_dict() for finding in self.findings],
            "counts": self.counts(),
            "counts_by_source": self.source_counts(),
            "tools": [tool.as_dict() for tool in self.tools],
            "duration_ms": round(self.duration_ms, 3),
        }
