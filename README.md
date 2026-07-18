# #24 ci-cd-templates

Status: benchmarked

Claim: validate GitHub Actions workflows before merge with deterministic local policies and optional actionlint/zizmor analysis.

Benchmark result: the fixed fixture set is scanned in `scan_time_ms`; the committed JSON records the measured median and the total findings for the exact environment.

| Metric | Result | Unit |
|---|---:|---|
| scan_time_ms | 18.431 | milliseconds |
| findings | 7 | count |

The baseline uses three local fixtures with five high-severity and two medium-severity policy findings. The exact Python/platform/tool environment and fixture SHA-256 are in `benchmarks/results/guardrails-baseline.json`.

## 1. Problem

Workflow failures are often found after merge because YAML syntax, permissions, action references, and shell interpolation are reviewed by different tools. This project provides one local command that returns stable JSON and fails the merge gate on high-risk findings.

## 2. Run Locally

```powershell
python -m pip install -e .
python -m ci_guardrails scan .github/workflows --deterministic
python -m ci_guardrails validate --strict
```

The local policy engine has no credential or network requirement. `actionlint` and `zizmor` are used automatically when present and are reported as unavailable otherwise.

## 3. Docker

```powershell
docker build -t ci-cd-templates .
docker run --rm ci-cd-templates
docker run --rm ci-cd-templates validate --strict
docker run --rm ci-cd-templates benchmark --stdout
```

The image pins `actionlint 1.7.12` and `zizmor 1.26.1`; it contains no credentials and does not contact GitHub at runtime.

## 4. CLI Contract

| Command | Purpose | Exit behavior |
|---|---|---|
| `scan PATH` | Parse workflows, apply local policies, and run available analyzers | non-zero at high findings by default |
| `benchmark` | Scan `benchmarks/fixtures` three times and write JSON | zero when the fixture set is readable |
| `validate --strict` | Check docs, manifest, benchmark evidence, tests, and project workflows | non-zero on release-gate failures |

Use `--no-external` for an analyzer-independent baseline. Deterministic mode sorts files and findings and fixes the fixture selection; measured time remains environment-dependent and is recorded in the result.

## 5. Guardrails

- YAML must be a workflow mapping with `name`, `on`, and `jobs`.
- Top-level permissions are required and `write-all` is forbidden.
- Actions and reusable workflows must use a full 40-character commit SHA.
- `pull_request_target` and untrusted event interpolation into `run` are high-risk.
- Jobs have bounded timeouts and checkout must disable persisted credentials.
- Docker is the delivery boundary; no cloud service or secret is needed for the default path.

## 6. Architecture

```text
workflow files -> safe YAML loader -> local policies -> actionlint/zizmor adapters -> sorted findings -> JSON benchmark
```

The architecture is a modular pipeline. Policy code is independently testable; subprocess integration is isolated in `tools.py`; the CLI only composes modules.

## 7. Evidence

- Specification and scope: `sdd/spec.md`
- Architecture record: `sdd/architecture-decision.md`
- Stack and principles: `sdd/technical-decision.md`
- Benchmark protocol: `sdd/benchmark-plan.md`
- OpenSpec artifacts: `openspec/artifacts/`
- Release validation: `tools/validate-project.ps1` and `ci-guardrails validate --strict`
- Reuse decisions: `sdd/reuse-improvement-review.md`

## 8. License and References

See `LICENSE` and `REFERENCES.md`.
