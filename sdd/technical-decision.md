# Technical Decision

## Stack

- Python `3.12.13`, PyYAML `6.0.3`, jsonschema `4.26.0`.
- Ruff `0.16.3`, mypy `2.3.1`, coverage `7.15.4`.
- actionlint `1.7.12` with release-asset checksum; zizmor `1.26.1` offline.
- Go `1.26.0`, Node `24.13.0`, Java `21`, Gradle `9.3.1`, Terraform `1.14.8` in reusable workflows.
- Digest-pinned Python base image and non-root UID `10001`.

## Principles

- SRP: loader, policy, analyzer adapters, scanner, benchmark, CLI, and stack workflows own separate reasons to change.
- OCP: new policy functions and workflow profiles can be added without changing finding values.
- ISP: consumers choose one workflow profile; they do not install the scanner package.
- DIP: orchestration depends on policy and model values; subprocess details do not leak inward.
- LSP: not claimed because the design has no inheritance hierarchy.
- KISS/YAGNI: fixed safe commands, no service, persistence, broker, cloud account, or workflow generator.
- DRY: security requirements and evidence shape are shared; stack build commands stay separate where semantics differ.

## Supply Chain

All GitHub Actions use full official tag SHAs. The actionlint archive is checksum-verified. Python dependencies and the container base are version-pinned. Checkout credentials are never persisted.
