# Benchmark Proof

Command:

```text
python -m ci_guardrails benchmark --fixtures benchmarks/fixtures --templates .github/workflows --runs 3 --warmup 1 --no-external
```

Evidence: `benchmarks/results/guardrails-baseline.json`.

The input is the three-file policy fixture set plus five reusable workflows and the CI caller. The result includes both SHA-256 input digests, all `scan_time_ms` samples, findings by source/severity, zero template findings, and the pinned runtime. `--no-external` isolates the deterministic local policy baseline.
