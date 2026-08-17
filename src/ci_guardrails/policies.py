from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from .models import Finding
from .yaml_loader import WorkflowDocument

_SHA_REF = re.compile(r"^[0-9a-fA-F]{40}$")
_UNTRUSTED_CONTEXTS = (
    "github.event.pull_request.title",
    "github.event.pull_request.body",
    "github.event.pull_request.head.ref",
    "github.event.issue.title",
    "github.event.issue.body",
    "github.event.comment.body",
    "github.head_ref",
)


def _finding(
    document: WorkflowDocument,
    rule_id: str,
    severity: str,
    message: str,
    path: tuple[str | int, ...] = (),
    details: dict[str, Any] | None = None,
) -> Finding:
    return Finding(
        source="policy",
        rule_id=rule_id,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        path=document.path.as_posix(),
        line=document.line_for(*path),
        details=details or {},
    )


def _as_mapping(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _iter_jobs(document: WorkflowDocument) -> Iterable[tuple[str, dict[str, Any]]]:
    jobs = _as_mapping(document.data.get("jobs")) or {}
    for job_id, job in jobs.items():
        if isinstance(job_id, str) and isinstance(job, dict):
            yield job_id, job


def _iter_steps(job: dict[str, Any]) -> Iterable[tuple[int, dict[str, Any]]]:
    steps = job.get("steps")
    if not isinstance(steps, list):
        return
    for index, step in enumerate(steps):
        if isinstance(step, dict):
            yield index, step


def _trigger_names(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    if isinstance(value, dict):
        return {key for key in value if isinstance(key, str)}
    return set()


def _check_action_ref(
    document: WorkflowDocument, value: Any, path: tuple[str | int, ...]
) -> list[Finding]:
    if not isinstance(value, str):
        return [_finding(document, "action-ref-type", "high", "action `uses` must be a string", path)]
    if value.startswith(("./", "docker://")):
        return []
    if "@" not in value:
        return [_finding(document, "unpinned-action", "high", f"action is not pinned: {value}", path)]
    action, ref = value.rsplit("@", 1)
    if not action or not _SHA_REF.fullmatch(ref):
        return [
            _finding(
                document,
                "unpinned-action",
                "high",
                f"action must use a full 40-character commit SHA: {value}",
                path,
            )
        ]
    return []


def validate_workflow(document: WorkflowDocument) -> list[Finding]:
    findings: list[Finding] = []
    data = document.data
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        findings.append(_finding(document, "workflow-name", "high", "workflow needs a non-empty `name`", ("name",)))

    if "on" not in data:
        findings.append(_finding(document, "workflow-trigger", "high", "workflow needs an `on` trigger", ("on",)))
    else:
        triggers = _trigger_names(data["on"])
        if "pull_request_target" in triggers:
            findings.append(
                _finding(
                    document,
                    "dangerous-trigger",
                    "high",
                    "`pull_request_target` requires an explicit security exception; use `pull_request` by default",
                    ("on", "pull_request_target"),
                )
            )

    permissions = data.get("permissions")
    if permissions is None:
        findings.append(
            _finding(
                document,
                "missing-permissions",
                "high",
                "declare least-privilege top-level `permissions`",
                ("permissions",),
            )
        )
    elif permissions == "write-all":
        findings.append(
            _finding(document, "write-all-permissions", "high", "`permissions: write-all` is forbidden", ("permissions",))
        )
    elif not isinstance(permissions, dict):
        findings.append(
            _finding(document, "permissions-type", "high", "top-level `permissions` must be a mapping", ("permissions",))
        )

    jobs = _as_mapping(data.get("jobs"))
    if not jobs:
        findings.append(_finding(document, "jobs-required", "high", "workflow needs at least one job", ("jobs",)))
        return findings

    for job_id, job in _iter_jobs(document):
        job_path = ("jobs", job_id)
        if not job.get("uses") and not job.get("runs-on"):
            findings.append(
                _finding(document, "job-runner-required", "high", "job needs `runs-on` or reusable-workflow `uses`", job_path)
            )
        if job.get("uses"):
            findings.extend(_check_action_ref(document, job["uses"], job_path + ("uses",)))
        if not job.get("uses") and "timeout-minutes" not in job:
            findings.append(
                _finding(
                    document,
                    "job-timeout",
                    "medium",
                    "set a bounded `timeout-minutes` for every job",
                    job_path,
                )
            )
        for index, step in _iter_steps(job):
            step_path = job_path + ("steps", index)
            if "uses" in step:
                findings.extend(_check_action_ref(document, step["uses"], step_path + ("uses",)))
                if step["uses"] == "actions/checkout" or (
                    isinstance(step["uses"], str) and step["uses"].startswith("actions/checkout@")
                ):
                    with_values = _as_mapping(step.get("with")) or {}
                    if with_values.get("persist-credentials") is not False:
                        findings.append(
                            _finding(
                                document,
                                "checkout-credentials",
                                "medium",
                                "set `persist-credentials: false` on checkout",
                                step_path + ("with", "persist-credentials"),
                            )
                        )
            run = step.get("run")
            if isinstance(run, str):
                for context in _UNTRUSTED_CONTEXTS:
                    if context in run:
                        findings.append(
                            _finding(
                                document,
                                "script-injection",
                                "high",
                                f"untrusted event context `{context}` is interpolated into `run`",
                                step_path + ("run",),
                                {"context": context},
                            )
                        )
                        break
            if "credentials" in step or "credentials" in (_as_mapping(step.get("with")) or {}):
                findings.append(
                    _finding(
                        document,
                        "inline-credentials",
                        "high",
                        "workflow steps must use GitHub secrets or OIDC, not inline credentials",
                        step_path,
                    )
                )
    return findings
