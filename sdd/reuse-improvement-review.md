# Reuse Improvement Review

## Finding

The kit selects language stacks but does not yet define the minimum executable CI contract that every stack profile must satisfy.

## Patch After Publication

- Add a `ci-profile-v1` contract covering workflow identity, runtime, commands, permission policy, timeout, action pinning, checkout persistence, and exact-head execution evidence.
- Add a `github-actions-reusable-workflow` skill mirrored for Codex and Claude.
- Add Delivery macro guidance that separates static validation latency from hosted consumer build duration.
- Reuse the negative policy fixtures without moving stack-specific commands into a universal script.

## Rejected

- A generated universal workflow with arbitrary command inputs: unsafe and semantically weaker than five explicit profiles.
- Organization-wide secrets or GitHub API dependency: incompatible with the local-first default.
- Copying analyzer binaries or repository-specific version pins into every project.

The promotion remains source-compatible: projects consume workflow files by immutable GitHub ref and consume the kit only for decisions, skills, and contracts.
