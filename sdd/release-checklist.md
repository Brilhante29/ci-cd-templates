# Release Checklist

- [x] Five reusable workflows exist and use `workflow_call`.
- [x] External actions are pinned to full SHAs.
- [x] Read-only permissions, bounded jobs, and non-persistent checkout are enforced.
- [x] Five repository-owned stack fixtures are called by CI.
- [x] Non-root offline Docker default returns zero findings.
- [x] Ruff, mypy, 18 tests, and at least 90% coverage pass.
- [ ] Source-locked three-run V1/V2 evidence is generated.
- [ ] README opens with canonical latency and correctness numbers.
- [ ] Exact final `main` GitHub Actions run passes all jobs.
- [ ] Reuse kit records publication and promotes `ci-profile-v1`.
