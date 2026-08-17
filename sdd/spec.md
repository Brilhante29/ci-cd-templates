# Specification: ci-cd-templates

## Problem

Portfolio repositories repeat GitHub Actions setup and often discover malformed YAML, broad permissions, mutable action tags, or stack-specific build failures only after merge.

## Claim

The repository provides five executable reusable workflows for Python, Go, Node, JVM/Gradle, and Terraform, plus one deterministic offline guardrail that validates their security and structure.

## Functional Requirements

1. Every reusable workflow is callable through `workflow_call`, read-only, time-bounded, and pins external actions to full commit SHAs.
2. The repository CI calls all five workflows against repository-owned fixtures.
3. The scanner parses YAML safely, normalizes findings, and supports optional actionlint and offline zizmor adapters.
4. The policy core rejects dangerous triggers, broad permissions, mutable action refs, persisted checkout credentials, inline credentials, and untrusted shell interpolation.
5. The benchmark scans three policy fixtures and all six repository workflows, preserving samples, digests, environment, and zero template findings.

## Non-Goals

- Hosted CI orchestration, workflow mutation, organization secrets, cloud services, database, broker, or GitHub API dependency in the default path.
- Claiming that static validation latency equals a consumer project's hosted build duration.
- Supporting arbitrary commands supplied by untrusted workflow inputs.

## Acceptance

- `docker run --rm --network none ci-cd-templates` returns zero findings.
- The five self-test jobs pass on the exact final GitHub `main` SHA.
- Ruff, mypy, 18 tests, and at least 90% unit coverage pass.
- Three-run V1/V2 evidence is source-locked and reports seven expected fixture findings and zero template findings.
