"""
Conditional Router, Loop/Deadlock Detector, and Resource Guard for LangGraph.

Evaluates state transitions dynamically:
- Chooses next branch based on planner output, tool results, and evidence health.
- Enforces tool call and iteration budgets.
- Detects repeated failing actions, tool retries, and identical planning loops.
- Routes safely to fallback, replan, analyst, or finalize.
"""

import logging
from typing import Any, Dict, Literal
from app.agent.agent_graph.state import GraphInvestigationState

logger = logging.getLogger("graph_router")

MAX_REPEATED_ACTIONS = 2
MAX_TOOL_CALL_BUDGET = 10
MAX_ITERATIONS_DEFAULT = 5


def is_resource_budget_exhausted(state: GraphInvestigationState) -> bool:
    """Checks if tool call limits or iteration limits have been reached."""
    tool_calls = state.get("tool_call_count", 0)
    max_tool_calls = state.get("max_tool_calls", MAX_TOOL_CALL_BUDGET)
    iterations = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", MAX_ITERATIONS_DEFAULT)

    if tool_calls >= max_tool_calls:
        logger.warning(f"Tool budget exhausted ({tool_calls}/{max_tool_calls}). Forcing synthesis.")
        return True
        
    if iterations >= max_iterations:
        logger.warning(f"Iteration limit reached ({iterations}/{max_iterations}). Forcing synthesis.")
        return True

    return False


def detect_loop_or_deadlock(state: GraphInvestigationState) -> bool:
    """
    Detects infinite execution loops or deadlocks:
    1. Repeated identical failing tool calls.
    2. Repeated identical planning states without progress.
    """
    repeated_actions = state.get("repeated_action_count", {})
    for action_key, count in repeated_actions.items():
        if count >= MAX_REPEATED_ACTIONS:
            logger.warning(f"Deadlock/Loop detected for action '{action_key}' (occurred {count} times). Triggering circuit breaker.")
            return True

    # Check if last 3 actions in history are identical
    history = state.get("action_history", [])
    if len(history) >= 4 and len(set(history[-3:])) == 1:
        logger.warning(f"Repeated action pattern detected in history: {history[-3:]}. Breaking loop.")
        return True

    return False


def route_after_planner(
    state: GraphInvestigationState
) -> Literal["parallel_research_node", "evidence_conflict_node", "finalize_node"]:
    """
    Dynamic routing after the planner creates the initial plan and subtasks.
    """
    subtasks = state.get("subtasks", [])
    if not subtasks:
        logger.info("Planner produced no subtasks; routing directly to evidence evaluation.")
        return "evidence_conflict_node"

    if is_resource_budget_exhausted(state):
        return "evidence_conflict_node"

    # Default: execute planned research subtasks (in parallel where independent)
    return "parallel_research_node"


def route_after_research(
    state: GraphInvestigationState
) -> Literal["evidence_conflict_node", "replan_node", "analyst_node"]:
    """
    Dynamic routing following research execution:
    - If critical tool errors occurred and alternatives exist, route to replan.
    - If deadlock detected, break out immediately.
    - Otherwise, route to evidence conflict & hypothesis evaluation.
    """
    if detect_loop_or_deadlock(state):
        logger.info("Deadlock guard triggered; bypassing further queries to preserve stability.")
        return "evidence_conflict_node"

    if is_resource_budget_exhausted(state):
        return "evidence_conflict_node"

    tool_errors = state.get("tool_errors", [])
    remaining_tasks = state.get("remaining_tasks", [])
    subtasks = state.get("subtasks", [])
    
    # Check if all subtasks failed and no evidence was gathered
    evidence = state.get("evidence", [])
    if tool_errors and not evidence and not remaining_tasks:
        # Check if we can replan with alternative tools
        unavailable = state.get("unavailable_tools", [])
        if len(unavailable) < 3 and state.get("iteration_count", 0) < state.get("max_iterations", 5):
            return "replan_node"

    return "evidence_conflict_node"


def route_after_self_eval(
    state: GraphInvestigationState
) -> Literal["finalize_node", "replan_node"]:
    """
    Dynamic routing after self-evaluation:
    - If passed -> finalize and produce output.
    - If failed and budget remains -> replan.
    - If budget exhausted or deadlock -> finalize safely.
    """
    if detect_loop_or_deadlock(state):
        logger.info("Self-evaluation: deadlock detected; proceeding to finalize.")
        return "finalize_node"

    if is_resource_budget_exhausted(state):
        logger.info("Self-evaluation: resource limit reached; proceeding to finalize.")
        return "finalize_node"

    eval_result = state.get("self_evaluation") or {}
    passed = eval_result.get("passed", True)
    suggested_replan = eval_result.get("suggested_replan", False)

    if not passed and suggested_replan:
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 5)
        if iteration_count < max_iterations - 1:
            logger.info(f"Self-evaluation requested replan (iteration {iteration_count}/{max_iterations}). Routing to replan.")
            return "replan_node"

    return "finalize_node"
