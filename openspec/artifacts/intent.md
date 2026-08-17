# Intent

## Project

#24 ci-cd-templates

## Outcome

Before merge, a maintainer can call one of five executable stack workflows and run one local command that detects malformed workflows, over-broad token permissions, unpinned actions, dangerous triggers, and untrusted shell interpolation. The command emits deterministic JSON and can use actionlint and offline zizmor when installed.

## Portfolio impact

This project starts the delivery-observability-infra program by making CI reuse executable and workflow quality measurable without GitHub credentials or a hosted service in the default path.

## Non-goals

No GitHub API calls, hosted findings store, automatic workflow mutation, or secret-dependent demo path.
