"""Workflow engine entrypoint delegating to compiled LangGraph state machine."""

import json
from pathlib import Path

from backend.workflow.graph import build_dispute_graph, dispute_graph, run_workflow
from backend.workflow.nodes import POLICY_PATH


def load_policy(path: Path = POLICY_PATH) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


__all__ = ["run_workflow", "build_dispute_graph", "dispute_graph", "load_policy"]

