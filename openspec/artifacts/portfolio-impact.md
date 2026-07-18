# Portfolio Impact

The reusable asset is a small guardrail contract: source, rule, severity, path, line, message, fingerprint, tool availability, fixture digest, and environment. The result can be consumed by CI logs, later SARIF output, or a portfolio benchmark without coupling policies to GitHub Actions transport.

The repository also demonstrates a repeatable pattern for local-first delivery tooling: fixed fixtures, pinned Docker tools, strict validation, and a benchmark JSON committed as evidence.
