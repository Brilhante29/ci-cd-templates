# Architecture Decision

## Decision

Use two decoupled delivery planes:

1. Declarative reusable GitHub workflows own stack setup and build commands.
2. A modular Python pipeline owns workflow parsing, policy evaluation, optional analyzer adapters, and evidence.

## Forces

- High reuse and auditability across five stacks.
- Low runtime throughput and no persistence or asynchronous processing need.
- GitHub-hosted execution must be proved, while security validation must also run locally and offline.
- A consumer repository must depend on a versioned workflow ref, never this repository's Python package.

## Dependency Rule

Models and policies depend only on typed values. YAML loading and analyzer subprocesses are adapters. Scanner and benchmark compose inward dependencies. CLI, Docker, and GitHub Actions are delivery boundaries. Reusable workflows share no source import with the scanner.

## Rejected

- Microservices, API server, database, broker, Kubernetes, and cloud account: no measured requirement.
- Composite action only: cannot model complete stack jobs or call-level permissions.
- Dynamic shell-command inputs: create injection and comparability risks.
- MVC, MVVM, or layered web architecture: no UI or request lifecycle exists.
