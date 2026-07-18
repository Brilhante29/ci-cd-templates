# Architecture Decision

## Status

Accepted

## Context

Project #24 is a pre-merge guardrail for workflow files. The proof target is a reproducible scan time plus a finding count over a fixed fixture set. The system must work without GitHub, credentials, a database, or a long-running service.

Problem forces:

- Domain complexity: medium. Several rules share one finding contract.
- Integration pressure: medium. actionlint and zizmor are external processes.
- UI state complexity: none.
- Data reproducibility: high. Fixture content and tool versions are evidence.
- Auditability: high. Every finding includes source, rule, path, and location.
- Throughput/async pressure: low. A merge-sized workflow set is small.
- Independent deployability: medium. Docker packages the CLI and analyzers.

## Decision

Chosen architecture: modular pipeline.

```text
files
  -> yaml_loader
  -> policies
  -> optional tool adapters
  -> normalized findings
  -> deterministic report
```

The pipeline matches the problem's data flow and keeps each proof step testable. `models.py` defines contracts, `yaml_loader.py` owns YAML behavior, `policies.py` owns repository rules, `tools.py` owns process integration, `scanner.py` composes them, and the CLI/benchmark/validation modules are delivery adapters.

Dependency rule: domain-like models and policy functions depend on standard values only. The scanner composes adapters. The CLI, Docker image, and subprocess tools depend inward and are never imported by policies.

## Rejected alternatives

| Alternative | Why rejected |
|---|---|
| Microservices | Network, deployment, and persistence failure modes do not help a local static-analysis problem. |
| Composite GitHub Action only | It cannot prove the same behavior from a clean local checkout. |
| Database-backed findings service | Adds storage and credentials without improving the benchmark. |

## Testing strategy

- Unit tests isolate YAML boolean handling and every core security policy family.
- Scanner tests prove sorted deterministic output and malformed-file tolerance.
- Benchmark tests prove the result schema fields, fixture digest, and finding count.
- The strict validator wires docs, manifest, tests, benchmark evidence, and the project workflow together.

## Consequences

Positive:

- One local command is useful before merge and in CI.
- Missing external binaries are explicit in JSON instead of silently changing the contract.
- The fixed fixture digest makes benchmark input drift visible.

Tradeoffs:

- External finding counts can change with analyzer versions; Docker pins the versions used for the packaged path.
- Scan time is machine-dependent; the environment and samples are recorded rather than hidden.

Migration path: add a new analyzer through the `tools.py` adapter contract or add a policy module without changing the CLI JSON shape.
