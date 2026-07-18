from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class GithubActionsLoader(yaml.SafeLoader):
    """SafeLoader with YAML 1.2 boolean rules so the `on` key stays a string."""


GithubActionsLoader.yaml_implicit_resolvers = {
    key: list(value) for key, value in yaml.SafeLoader.yaml_implicit_resolvers.items()
}

for _initial in list("OoYyNn"):
    GithubActionsLoader.yaml_implicit_resolvers[_initial] = [
        resolver
        for resolver in GithubActionsLoader.yaml_implicit_resolvers.get(_initial, [])
        if resolver[0] != "tag:yaml.org,2002:bool"
    ]

GithubActionsLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


@dataclass(frozen=True)
class WorkflowDocument:
    path: Path
    data: dict[str, Any]
    line_map: dict[tuple[str | int, ...], int]

    def line_for(self, *parts: str | int) -> int | None:
        return self.line_map.get(tuple(parts))


class WorkflowParseError(ValueError):
    def __init__(self, path: Path, message: str, line: int | None = None, column: int | None = None):
        super().__init__(message)
        self.path = path
        self.line = line
        self.column = column


def _line_map(node: yaml.Node, path: tuple[str | int, ...] = ()) -> dict[tuple[str | int, ...], int]:
    result = {path: node.start_mark.line + 1}
    if isinstance(node, yaml.MappingNode):
        for key_node, value_node in node.value:
            key = key_node.value
            child_path = path + (key,)
            result[child_path] = key_node.start_mark.line + 1
            result.update(_line_map(value_node, child_path))
    elif isinstance(node, yaml.SequenceNode):
        for index, value_node in enumerate(node.value):
            child_path = path + (index,)
            result[child_path] = value_node.start_mark.line + 1
            result.update(_line_map(value_node, child_path))
    return result


def load_workflow(path: Path) -> WorkflowDocument:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise WorkflowParseError(path, "workflow is not valid UTF-8") from exc

    try:
        node = yaml.compose(raw, Loader=GithubActionsLoader)
        data = yaml.load(raw, Loader=GithubActionsLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        message = getattr(exc, "problem", None) or str(exc)
        raise WorkflowParseError(
            path,
            f"invalid YAML: {message}",
            mark.line + 1 if mark else None,
            mark.column + 1 if mark else None,
        ) from exc

    if node is None or not isinstance(data, dict):
        raise WorkflowParseError(path, "workflow document must be a YAML mapping")
    return WorkflowDocument(path=path, data=data, line_map=_line_map(node))
