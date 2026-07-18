# Intent

## Project

#24 ci-cd-templates

## Outcome

Before merge, a maintainer can run one local command that detects malformed workflows, over-broad token permissions, unpinned actions, dangerous triggers, and untrusted shell interpolation. The command emits deterministic JSON and can use actionlint and zizmor when they are installed.

## Portfolio impact

This project strengthens the delivery-observability-infra program by making workflow quality measurable and reproducible without GitHub credentials or a hosted service.

## Non-goals

No GitHub API calls, hosted findings store, automatic workflow mutation, or secret-dependent demo path.
