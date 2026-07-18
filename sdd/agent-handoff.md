# Agent Handoff

Project: `24 - ci-cd-templates`

## Principal summary

- Objective: validate GitHub Actions workflows before merge.
- Portfolio program: `delivery-observability-infra`.
- Public proof claim: deterministic local guardrails plus optional actionlint/zizmor analysis.
- Primary benchmark: median `scan_time_ms` and total findings.
- Default runnable path: `docker run --rm ci-cd-templates`.

## Decisions and evidence

| Role | Decision | Evidence | Status |
|---|---|---|---|
| program-planner | delivery-observability-infra | `project.yaml` | complete |
| architecture-selector | modular pipeline | `sdd/architecture-decision.md` | complete |
| engineering-principles-reviewer | SOLID, DRY, KISS, YAGNI, and Demeter recorded | `sdd/technical-decision.md` | complete |
| stack-decision-agent | Python CLI with PyYAML and standard library | `project.yaml` | complete |
| api-style-agent | CLI with JSON contract | `sdd/technical-decision.md` | complete |
| cloud-local-first-agent | no cloud or credential path | `Dockerfile` | complete |
| messaging-agent | none | `project.yaml` | complete |
| language-profile-agent | typed Python package under `src/` | `pyproject.toml` | complete |
| benchmark-harness-agent | fixed fixtures, median, environment, digest | `sdd/benchmark-plan.md` | complete |
| security-reuse-reviewer | pinned tools, safe loader, no secrets | `REFERENCES.md` | complete |
| release-ci-publisher | strict validator and CI workflow | `.github/workflows/ci.yml` | complete |

## Local-first runtime

- Docker command: `docker build -t ci-cd-templates .; docker run --rm ci-cd-templates`.
- Local services: none.
- Cloud credentials: none.
- Config switch: `--no-external` selects policy-only mode.

## Boundaries

- Loader: safe YAML plus source locations.
- Policy: local rules and immutable findings.
- Adapters: actionlint and zizmor subprocesses.
- Application: scanner, benchmark, and strict validator.
- Delivery: CLI, Docker, and GitHub Actions.

## Benchmark handoff

- Metric: `scan_time_ms`.
- Unit: milliseconds.
- Higher or lower is better: lower time, while findings are a correctness count.
- Result: `benchmarks/results/guardrails-baseline.json`.
- Fixture: `benchmarks/fixtures/` with a recorded SHA-256 digest.

## Risks

- A new external-tool release can change findings; update the Docker pin and benchmark together.
- Docker daemon availability is required only to exercise the image, not for local policy tests.

## Publication gates

- [x] Docker path is documented.
- [x] Benchmark result exists.
- [x] README starts with number, claim, and benchmark.
- [x] References are documented.
- [x] No credential is required by the default path.
- [x] Strict validation and unit tests are wired.
