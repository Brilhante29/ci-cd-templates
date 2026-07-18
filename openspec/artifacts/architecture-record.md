# Architecture Record

Decision: modular pipeline in a typed Python package.

```text
files -> safe loader -> local policies -> optional analyzers -> findings -> benchmark JSON
```

The dependency direction is inward. Policies depend on the workflow document and finding model; external process details stay in `tools.py`; CLI, Docker, and CI are delivery adapters. No database, message bus, cloud SDK, or API server is needed.

Rejected: microservices, a GitHub-only action, and a database-backed findings service. Each adds operational cost without improving local pre-merge proof.
