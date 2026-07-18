# Technical Decision

## Selected stack

Python 3.10+, PyYAML, `unittest`, Docker, actionlint 1.7.12, and zizmor 1.26.1.

Python is the smallest typed runtime that supports safe YAML parsing, subprocess control, JSON output, and fast fixture-driven tests. PyYAML is used for parsed data and composed-node source locations. The standard library handles the rest to keep the default path local and auditable.

## Interfaces

- API style: CLI.
- Contract: JSON scan and benchmark objects emitted by `models.py` and `benchmark.py`.
- Messaging: none.
- Storage: none.
- Cloud: none. The image runs without network after build and needs no credentials.

## Engineering principles

- SRP: loader, policies, tool adapters, scanner, benchmark, and validator have separate reasons to change.
- OCP: external tools are optional adapters and policy findings use one immutable model.
- LSP: unavailable tools and available tools both return a `ToolStatus`; scan composition stays valid.
- ISP: policy code receives only a `WorkflowDocument`; tool adapters receive paths and a working directory.
- DIP: CLI depends on scanner and benchmark functions, not on subprocess details.
- DRY: finding construction, severity ordering, path ordering, and JSON serialization are centralized.
- KISS: one process, one fixture set, and one output contract are enough to prove the claim.
- YAGNI: no database, API server, hosted dashboard, auto-fixer, or cloud adapter is included.
- Law of Demeter: policies access direct workflow/job/step mappings and do not traverse framework objects.

## Security boundaries

- `yaml_loader.py` uses `SafeLoader` and changes only YAML boolean resolution so GitHub's `on` key is not converted to `True`.
- External analyzers receive file paths, not credentials or tokens.
- Docker uses pinned versions and does not copy `.git`, `.portfolio`, or `.portfolio-control` into the image.
- The CI workflow uses full commit SHAs and `persist-credentials: false`.

## Rejected options

| Option | Reason |
|---|---|
| Rust | A binary is attractive, but Python reduces policy and fixture iteration cost for this portfolio project. |
| actionlint-only | It does not express the repository-specific least-privilege and shell-input policy. |
| zizmor-only | It does not replace structural YAML and project release validation. |
| GitHub API integration | It would require credentials and make the default benchmark non-local. |
