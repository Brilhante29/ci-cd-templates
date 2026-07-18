# Benchmark Proof

Command:

```text
python -m ci_guardrails benchmark --fixtures benchmarks/fixtures --runs 3 --warmup 1
```

Evidence: `benchmarks/results/guardrails-baseline.json`.

The input is the three-file repository-owned fixture set. The result includes the SHA-256 fixture digest, median and sample `scan_time_ms`, findings by source/severity, Python/platform/tool versions, and whether external analyzers were enabled. `--no-external` isolates the deterministic local policy baseline.
