# Benchmark Plan

## Hypothesis

A fixed set of local workflows can be scanned before merge with a measurable time and finding count, and the input can be fingerprinted so changes are visible.

## Command

```powershell
python -m ci_guardrails benchmark --fixtures benchmarks/fixtures --runs 3 --warmup 1
```

Use `--no-external` to compare the deterministic local policy engine across machines. The Docker command keeps external analyzer versions pinned.

## Fixed input

- Directory: `benchmarks/fixtures`
- Files: `secure.yml`, `policy-violations.yml`, `malformed.yml`
- Source: repository-owned fixtures
- License: project license
- Random seed: not applicable; no random sampling
- Input digest: recorded as SHA-256 in the result JSON

## Metrics

| Metric | Unit | Source | Why it matters |
|---|---:|---|---|
| `scan_time_ms` | milliseconds | monotonic wall clock around each scan | pre-merge feedback cost |
| `findings` | count | normalized final scan | guardrail signal |
| `findings.by_source` | count by source | policy/actionlint/zizmor | tool contribution and drift |

The reported value is the median of three measured scans after one warmup. `timestamp`, Python version, OS, tool versions, samples, and fixture digest are included in JSON.

## Reproducibility limits

Finding order and local-policy findings are deterministic. Timing depends on CPU, filesystem, Python, and analyzer availability; these are recorded in `environment`. Docker is the reference environment for pinned external tools.
