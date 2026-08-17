# Benchmark Proof

Command:

```text
python -m ci_guardrails benchmark --fixtures benchmarks/fixtures --templates .github/workflows --runs 3 --warmup 1 --no-external
```

Evidence: `benchmarks/results/guardrails-baseline.json` and `benchmarks/publication/guardrails-baseline-v2.json`.

The input is the three-file policy fixture set plus five reusable workflows and the CI caller. Three measured runs produced a `104.945 ms` median (`103.531-152.502 ms`), detected all seven expected policy findings, and returned zero findings for the templates. V2 binds the result to source `8bfd94a1a8fd6186b717bc7be53d61e92d419b2d`, the Docker image digest, dependency lock digest, and V1 artifact digest. `--no-external` isolates the deterministic local policy baseline.
