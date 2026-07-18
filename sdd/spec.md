# Specification: ci-cd-templates

## Number and claim

- Number: #24
- Claim: validate GitHub Actions workflows before merge with deterministic local policies and optional external analyzers.
- User: a maintainer reviewing a pull request before merge.

## Problem

Workflow correctness spans YAML shape, GitHub Actions semantics, token permissions, third-party action pinning, and shell injection. A merge gate needs one command, stable findings, and a local fallback when external binaries are absent.

## Scope

In scope:

- Typed Python CLI with `scan`, `benchmark`, and strict `validate` commands.
- Safe YAML parsing with source locations and local policy findings.
- Optional `actionlint` and `zizmor` subprocess adapters with version/status evidence.
- Fixed local fixtures and JSON benchmark containing scan time, findings, fixture digest, and environment.
- Docker image with pinned analyzer versions and no credentials.
- GitHub Actions CI running the same strict gate.

Out of scope:

- Calling GitHub APIs or checking repository settings.
- Applying automatic fixes to workflows.
- Persisting findings in a hosted database.
- Replacing actionlint or zizmor's complete rule sets.

## Functional requirements

1. Find `.yml` and `.yaml` workflow files in stable path order.
2. Report malformed YAML without stopping the rest of the scan.
3. Enforce workflow name, trigger, jobs, least-privilege permissions, pinned actions, bounded jobs, safe checkout, and untrusted interpolation rules.
4. Add external findings only when the corresponding executable is available.
5. Emit deterministic file/finding order and machine-readable JSON.
6. Exit non-zero for high-severity findings by default.
7. Benchmark exactly the fixed fixture set and record the environment.

## Acceptance criteria

- `python -m unittest discover -s tests` passes.
- `python -m ci_guardrails benchmark --no-external` writes `benchmarks/results/guardrails-baseline.json`.
- `python -m ci_guardrails validate --strict` passes on the repository.
- Docker default command scans `.github/workflows` without a secret.
- CI uses full SHA references and calls the strict validator.
