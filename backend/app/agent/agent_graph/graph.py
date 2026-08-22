"""
LangGraph StateGraph Definition for Autonomous Competitive Intelligence.

Assembles the dynamic multi-agent execution graph with:
- State channels
- Nodes for Context, Planning, Parallel Research, Evidence Evaluation, Synthesis, Self-Eval, Replanning, Finalization
- Dynamic conditional routing edges
- Recovery loops
- Checkpointing
"""

import logging
from langgraph.graph import StateGraph, START, END

from app.agent.agent_graph.state import GraphInvestigationState
from app.agent.agent_graph.nodes import (
    context_node,
    planner_node,
    parallel_research_node,
    evidence_conflict_node,
    analyst_node,
    self_eval_node,
    replan_node,
    finalize_node,
)
from app.agent.agent_graph.router import (
    route_after_planner,
    route_after_research,
    route_after_self_eval,
)
from app.agent.agent_graph.checkpoint import get_checkpointer

logger = logging.getLogger("investigation_graph")


def build_investigation_graph() -> StateGraph:
    """Constructs and returns the uncompiled LangGraph StateGraph."""
    builder = StateGraph(GraphInvestigationState)

    # 1. Register Nodes
    builder.add_node("context_node", context_node)
    builder.add_node("planner_node", planner_node)
    builder.add_node("parallel_research_node", parallel_research_node)
    builder.add_node("evidence_conflict_node", evidence_conflict_node)
    builder.add_node("analyst_node", analyst_node)
    builder.add_node("self_eval_node", self_eval_node)
    builder.add_node("replan_node", replan_node)
    builder.add_node("finalize_node", finalize_node)

    # 2. Add Fixed Edges
    builder.add_edge(START, "context_node")
    builder.add_edge("context_node", "planner_node")
    builder.add_edge("evidence_conflict_node", "analyst_node")
    builder.add_edge("analyst_node", "self_eval_node")
    builder.add_edge("replan_node", "parallel_research_node")
    builder.add_edge("finalize_node", END)

    # 3. Add Dynamic Conditional Edges
    builder.add_conditional_edges(
        "planner_node",
        route_after_planner,
        {
            "parallel_research_node": "parallel_research_node",
            "evidence_conflict_node": "evidence_conflict_node",
            "finalize_node": "finalize_node",
        },
    )

    builder.add_conditional_edges(
        "parallel_research_node",
        route_after_research,
        {
            "evidence_conflict_node": "evidence_conflict_node",
            "replan_node": "replan_node",
            "analyst_node": "analyst_node",
        },
    )

    builder.add_conditional_edges(
        "self_eval_node",
        route_after_self_eval,
        {
            "finalize_node": "finalize_node",
            "replan_node": "replan_node",
        },
    )

    return builder


def get_compiled_graph():
    """Compiles the StateGraph with checkpointer."""
    checkpointer = get_checkpointer()
    builder = build_investigation_graph()
    return builder.compile(checkpointer=checkpointer)


# Compiled singleton graph
investigation_graph = get_compiled_graph()
