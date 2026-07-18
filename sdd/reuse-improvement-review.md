# Reuse Improvement Review

Project: `24 - ci-cd-templates`

## Review points

- [x] after scaffold
- [x] after architecture decision
- [x] after first working slice
- [x] after benchmark result
- [x] before publication

## Findings

| Finding | Classification | Kit Area | Action | Status |
|---|---|---|---|---|
| A deterministic analyzer status and finding schema is reusable | `patch_now` | `contracts` | keep the source, severity, path, line, and fingerprint fields stable | recorded |
| A fixed fixture digest makes benchmark drift visible | `patch_now` | `metrics` | include digest, environment, and tool availability in benchmark JSON | recorded |
| Docker pinning is project-specific because analyzer versions change | `reject` | `templates` | do not move repository-specific pins into the shared kit | rejected |

## Patch-now decisions

- The project uses the existing portfolio benchmark JSON shape and extends it with scan findings and tool evidence.
- The project keeps the local-first, no-secret default path required by the component pack.

## Backlog decisions

- Add optional SARIF output if a later portfolio project needs code-scanning upload.

## Rejected improvements

- No shared policy database or hosted service was added; it would duplicate project logic and weaken offline proof.

## Final gate

- [x] Reusable improvements were patched or recorded.
- [x] Project-specific implementation was not moved into the kit.
- [x] Validation reflects the deterministic finding and benchmark contract.
