"""LangGraph StateGraph builder for DisputeGuard."""

from langgraph.graph import END, START, StateGraph

from backend.domain.models import Dispute, EvidenceDocument
from backend.workflow.nodes import (
    decide_node,
    economics_node,
    evidence_scoring_node,
    extract_node,
    ingest_node,
    policy_evaluate_node,
    validate_node,
)
from backend.workflow.state import DisputeState


def build_dispute_graph():
    """Construct the compiled LangGraph execution graph."""
    graph = StateGraph(DisputeState)

    # 1. Register Nodes
    graph.add_node("ingest", ingest_node)
    graph.add_node("extract", extract_node)
    graph.add_node("validate", validate_node)
    graph.add_node("policy_evaluate", policy_evaluate_node)
    graph.add_node("evidence_scoring", evidence_scoring_node)
    graph.add_node("economics", economics_node)
    graph.add_node("decide", decide_node)

    # 2. Wire Linear & Conditional Edges
    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "extract")
    graph.add_edge("extract", "validate")
    graph.add_edge("validate", "policy_evaluate")
    graph.add_edge("policy_evaluate", "evidence_scoring")
    graph.add_edge("evidence_scoring", "economics")
    graph.add_edge("economics", "decide")
    graph.add_edge("decide", END)

    return graph.compile()


# Compiled singleton instance
dispute_graph = build_dispute_graph()


def run_workflow(
    dispute: Dispute,
    documents: list[EvidenceDocument],
    policy: dict | None = None,
) -> dict:
    """
    Entrypoint compatible with existing API routes and test suites.
    Executes the compiled LangGraph state machine.
    """
    initial_state: DisputeState = {
        "dispute": dispute,
        "documents": documents,
        "policy": policy or {},
    }

    final_state = dispute_graph.invoke(initial_state)

    return {
        "decision": final_state["decision"],
        "claims": final_state["claims"],
        "issues": [issue.__dict__ for issue in final_state["issues"]],
        "missing_evidence": final_state["missing_evidence"],
        "policy_id": final_state.get("policy_id", "merchandise_not_received_v1"),
    }
