# Benchmark Plan

## Question

Can the local policy core scan all reusable workflows and the fixed unsafe fixtures quickly while preserving exact input identity and rejecting any template finding?

## Command

```powershell
python tools/benchmark_v2.py --image ci-cd-templates:benchmark --runs 3 --warmup 1
```

The producer builds a non-root image from a clean commit and captures JSON from an offline container. It does not mount a writable host path into the measured process.

## Workload

- Three policy fixtures: one malformed, one intentionally unsafe, one secure.
- Five reusable workflows plus the repository orchestration workflow.
- One warmup followed by three serial measured runs.
- Local policy only for comparability; actionlint and zizmor remain release gates outside the timed section.

## Metrics

| Metric | Direction | Gate |
|---|---|---|
| `scan_time_ms` | lower is better | every raw sample preserved |
| `findings` | target | exactly `7` fixture findings |
| `template_findings` | target | exactly `0` |

Hosted job duration is intentionally excluded because it depends on runner queue, dependency caches, and consumer workload. Exact-head CI is the execution proof for the five templates.

## Provenance

V2 binds the source commit, immutable image, dependency constraints, V1 artifact, nine workload files, effective config, runtime, architecture, and three raw latency samples.
