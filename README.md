# #24 ci-cd-templates

**Status:** scaffold

**Proves:** pipelines reutilizaveis.

**Benchmark target:** build_time_seconds.

**Stack:** github-actions, docker-buildx, trivy, k6.

## Next milestone

Implement the smallest Docker-runnable version and produce the first JSON benchmark under enchmarks/results/.

## Run

`ash
docker build -t ci-cd-templates .
docker run --rm ci-cd-templates
`

## Benchmark

`ash
docker run --rm ci-cd-templates benchmark
`

| Metric | Value | Unit |
|---|---:|---|
| build_time_seconds | pending | pending |

## Architecture

Defined in sdd/spec.md before implementation.

## References

See REFERENCES.md.