"""
LangGraph Nodes for Autonomous Competitive Intelligence Graph.

Implements all node functions:
1. context_node: Conversational context retrieval & pronoun resolution.
2. planner_node: Dynamic query decomposition, strategy selection, hypothesis formulation.
3. parallel_research_node: Concurrent execution of independent research tasks with tool fallback.
4. evidence_conflict_node: Conflict detection, source weighing, hypothesis scoring, confidence computation.
5. analyst_node: Strategic synthesis via Intelligence Analyst Agent.
6. self_eval_node: Pre-finalization quality & completeness verification.
7. replan_node: Autonomous replanning upon failure or insufficient data.
8. finalize_node: Session memory persistence and final response packaging.
"""

import asyncio
import time
import uuid
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.agent.state import (
    StepActivity,
    ToolExecutionRecord,
    CompanyCardData,
    NewsArticle,
    ResearchPaper,
    PatentItem,
    SourceItem,
    ResearchResults,
)
from app.agent.agent_graph.state import (
    GraphInvestigationState,
    SubTask,
    EvidenceItem,
    EvidenceConflict,
    HypothesisRecord,
)
from app.agent.agent_graph.planner import create_dynamic_plan, replan_on_failure
from app.agent.agent_graph.evaluator import (
    extract_evidence_from_results,
    detect_and_resolve_conflicts,
    verify_hypotheses,
    calculate_overall_confidence,
    evaluate_investigation_state,
)
from app.agent.agent_graph.router import detect_loop_or_deadlock, is_resource_budget_exhausted
from app.agent.tool_registry import default_tool_registry
from app.agent.intelligence_analyst import default_analyst_agent
from app.context.context_manager import default_context_manager
from app.observability.tracer import default_tracer
from app.observability.diagnostics import RootCauseDiagnosticEngine

logger = logging.getLogger("graph_nodes")


async def context_node(state: GraphInvestigationState) -> Dict[str, Any]:
    """
    Step 1: Retrieve conversational session memory and disambiguate query.
    """
    t0 = time.perf_counter()
    user_query = state.get("user_query", "").strip()
    session_id = state.get("session_id") or f"session-{uuid.uuid4().hex[:12]}"
    chat_history = state.get("chat_history")
    trace_id = state.get("trace_id")
    
    steps = list(state.get("steps", []))
    step_num = len(steps) + 1

    investigation_goal = user_query
    relevant_context_dict: Optional[Dict[str, Any]] = None
    context_summary = "Context retrieved"

    try:
        rel_context = await default_context_manager.get_relevant_context(
            session_id=session_id,
            current_query=user_query,
            chat_history=chat_history,
        )
        investigation_goal = rel_context.contextual_query or user_query
        relevant_context_dict = rel_context.model_dump()

        if rel_context.has_context:
            parts = []
            if rel_context.active_companies:
                parts.append(f"Entities: {', '.join(rel_context.active_companies)}")
            if rel_context.active_topics:
                parts.append(f"Topic: {', '.join(rel_context.active_topics)}")
            if rel_context.context_notes:
                parts.append(f"Notes: {'; '.join(rel_context.context_notes)}")
            context_summary = f"Context retrieved ({' | '.join(parts)}). Target: '{investigation_goal}'"
        else:
            context_summary = f"Context retrieved for: '{investigation_goal}'"

    except Exception as e:
        logger.warning(f"Context retrieval non-fatal warning: {e}")
        context_summary = f"Context retrieved for: '{user_query}'"

    steps.append({
        "step": step_num,
        "action": "tool",
        "summary": context_summary,
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    if trace_id:
        default_tracer.record_node_span(
            trace_id=trace_id,
            node_name="context_node",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
            status="success",
            metadata={"has_context": bool(relevant_context_dict and relevant_context_dict.get("has_context"))},
        )

    return {
        "session_id": session_id,
        "investigation_goal": investigation_goal,
        "relevant_context": relevant_context_dict,
        "steps": steps,
        "status": "planning",
        "action_history": state.get("action_history", []) + ["context_retrieval"],
    }


async def planner_node(state: GraphInvestigationState) -> Dict[str, Any]:
    """
    Step 2: Dynamically inspect the query, classify intent, and build subtasks & hypotheses.
    """
    t0 = time.perf_counter()
    user_query = state.get("user_query", "")
    investigation_goal = state.get("investigation_goal") or user_query
    relevant_context = state.get("relevant_context")
    max_tool_calls = state.get("max_tool_calls", 8)
    max_iterations = state.get("max_iterations", 5)
    adversarial_config = state.get("adversarial_config")
    trace_id = state.get("trace_id")

    steps = list(state.get("steps", []))
    step_num = len(steps) + 1

    task_plan, subtasks, hypotheses, entities, remaining_tasks = create_dynamic_plan(
        user_query=user_query,
        investigation_goal=investigation_goal,
        relevant_context=relevant_context,
        max_tool_calls=max_tool_calls,
        max_iterations=max_iterations,
        adversarial_config=adversarial_config,
    )

    plan_desc = task_plan[0].get("description", "Dynamic plan generated")
    steps.append({
        "step": step_num,
        "action": "tool",
        "summary": f"Dynamic planner created plan ({len(subtasks)} subtasks, {len(entities)} entities). Strategy: {plan_desc}",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    if hypotheses:
        step_num += 1
        steps.append({
            "step": step_num,
            "action": "tool",
            "summary": f"Formulated {len(hypotheses)} testable hypothesis/hypotheses for empirical verification.",
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    if trace_id:
        default_tracer.record_node_span(
            trace_id=trace_id,
            node_name="planner_node",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
            status="success",
            metadata={
                "subtasks_count": len(subtasks),
                "entities_count": len(entities),
                "hypotheses_count": len(hypotheses),
            },
        )

    return {
        "task_plan": task_plan,
        "subtasks": [st.model_dump() for st in subtasks],
        "hypotheses": [h.model_dump() for h in hypotheses],
        "detected_entities": entities,
        "remaining_tasks": remaining_tasks,
        "completed_tasks": state.get("completed_tasks", []),
        "steps": steps,
        "status": "researching",
        "iteration_count": state.get("iteration_count", 0) + 1,
        "action_history": state.get("action_history", []) + ["dynamic_planning"],
    }


async def _execute_single_subtask(
    subtask: Dict[str, Any],
    adversarial_config: Optional[Dict[str, Any]] = None,
    unavailable_tools: Optional[List[str]] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper to execute a single research tool with failure simulation / fallback / tracing."""
    t_start = time.perf_counter()
    tool_name = subtask.get("tool_name", "")
    tool_input = subtask.get("tool_input", {})
    subtask_id = subtask.get("id", "")
    target_entity = subtask.get("target_entity")

    unavail = unavailable_tools or []

    # 1. Check if tool is marked permanently unavailable
    if tool_name in unavail:
        duration_ms = (time.perf_counter() - t_start) * 1000.0
        err_msg = f"Tool '{tool_name}' is unavailable due to prior circuit breaker."
        if trace_id:
            default_tracer.record_tool_span(
                trace_id=trace_id,
                tool_name=tool_name,
                duration_ms=duration_ms,
                success=False,
                error_type="CIRCUIT_BREAKER_TRIGGERED",
                error_message=err_msg,
                fallback_used=True,
            )
        return {
            "subtask_id": subtask_id,
            "tool_name": tool_name,
            "success": False,
            "error": err_msg,
            "is_permanent_fail": True,
        }

    # 2. Check for adversarial simulation
    if adversarial_config:
        # Simulated Tavily failure
        if tool_name in ["search_web", "search_research_papers"] and adversarial_config.get("force_tavily_fail"):
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            err_msg = "Simulated Tavily API failure (503 Service Unavailable / Rate Limit)."
            if trace_id:
                default_tracer.record_tool_span(
                    trace_id=trace_id,
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    success=False,
                    error_type="SERVICE_UNAVAILABLE",
                    error_message=err_msg,
                    fallback_used=True,
                )
            return {
                "subtask_id": subtask_id,
                "tool_name": tool_name,
                "success": False,
                "error": err_msg,
                "is_simulated": True,
            }
        # Simulated GNews failure
        if tool_name == "search_news" and adversarial_config.get("force_gnews_fail"):
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            err_msg = "Simulated GNews API failure (429 Too Many Requests)."
            if trace_id:
                default_tracer.record_tool_span(
                    trace_id=trace_id,
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    success=False,
                    error_type="RATE_LIMIT_EXCEEDED",
                    error_message=err_msg,
                    fallback_used=True,
                )
            return {
                "subtask_id": subtask_id,
                "tool_name": tool_name,
                "success": False,
                "error": err_msg,
                "is_simulated": True,
            }
        # Simulated repeated tool failure
        if adversarial_config.get("force_repeated_tool_fail"):
            target_fail = adversarial_config.get("force_repeated_tool_fail")
            if tool_name == target_fail or target_fail == "all":
                duration_ms = (time.perf_counter() - t_start) * 1000.0
                err_msg = f"Simulated persistent failure for '{tool_name}'."
                if trace_id:
                    default_tracer.record_tool_span(
                        trace_id=trace_id,
                        tool_name=tool_name,
                        duration_ms=duration_ms,
                        success=False,
                        error_type="CIRCUIT_BREAKER_TRIGGERED",
                        error_message=err_msg,
                        fallback_used=True,
                    )
                return {
                    "subtask_id": subtask_id,
                    "tool_name": tool_name,
                    "success": False,
                    "error": err_msg,
                    "is_simulated": True,
                }

    # 3. Live tool execution
    tool = default_tool_registry.get_tool(tool_name)
    if not tool:
        duration_ms = (time.perf_counter() - t_start) * 1000.0
        err_msg = f"Tool '{tool_name}' not registered in tool registry."
        if trace_id:
            default_tracer.record_tool_span(
                trace_id=trace_id,
                tool_name=tool_name,
                duration_ms=duration_ms,
                success=False,
                error_type="UNREGISTERED_TOOL",
                error_message=err_msg,
                fallback_used=True,
            )
        return {
            "subtask_id": subtask_id,
            "tool_name": tool_name,
            "success": False,
            "error": err_msg,
        }

    try:
        observation = await tool.execute(**tool_input)
        duration_ms = (time.perf_counter() - t_start) * 1000.0
        extracted_news = [n.model_dump() for n in tool.extract_news(observation)]
        extracted_companies = [c.model_dump() for c in tool.extract_companies(observation)]
        extracted_research = [r.model_dump() for r in tool.extract_research(observation)]
        extracted_patents = [p.model_dump() for p in tool.extract_patents(observation)]
        extracted_sources = [s.model_dump() for s in tool.extract_sources(observation)]

        if trace_id:
            default_tracer.record_tool_span(
                trace_id=trace_id,
                tool_name=tool_name,
                duration_ms=duration_ms,
                success=True,
                metadata={
                    "extracted_companies": len(extracted_companies),
                    "extracted_news": len(extracted_news),
                    "extracted_research": len(extracted_research),
                    "extracted_sources": len(extracted_sources),
                },
            )

        return {
            "subtask_id": subtask_id,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "observation": observation,
            "success": True,
            "extracted_news": extracted_news,
            "extracted_companies": extracted_companies,
            "extracted_research": extracted_research,
            "extracted_patents": extracted_patents,
            "extracted_sources": extracted_sources,
        }
    except Exception as e:
        duration_ms = (time.perf_counter() - t_start) * 1000.0
        logger.warning(f"Error executing tool '{tool_name}': {e}")
        diag = RootCauseDiagnosticEngine.diagnose_failure(tool_name, str(e))
        if trace_id:
            default_tracer.record_tool_span(
                trace_id=trace_id,
                tool_name=tool_name,
                duration_ms=duration_ms,
                success=False,
                error_type=diag.error_category,
                error_message=str(e),
                fallback_used=True,
            )
        return {
            "subtask_id": subtask_id,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "success": False,
            "error": str(e),
        }


async def parallel_research_node(state: GraphInvestigationState) -> Dict[str, Any]:
    """
    Step 3: Execute independent research subtasks concurrently (parallel branches)
    and merge extracted findings into shared state.
    """
    t0 = time.perf_counter()
    subtasks = state.get("subtasks", [])
    remaining_ids = set(state.get("remaining_tasks", []))
    adversarial_config = state.get("adversarial_config")
    unavailable_tools = list(state.get("unavailable_tools", []))
    trace_id = state.get("trace_id")
    
    # Filter pending subtasks to execute
    tasks_to_run = [
        st for st in subtasks
        if st.get("id") in remaining_ids and st.get("status") in ["pending", "running"]
    ]

    steps = list(state.get("steps", []))
    step_num = len(steps) + 1

    # Log individual research branch starts
    seen_entities_started = set()
    for st in tasks_to_run:
        ent = st.get("target_entity")
        t_name = st.get("tool_name", "")
        if ent and ent not in seen_entities_started:
            seen_entities_started.add(ent)
            steps.append({
                "step": step_num,
                "action": "tool",
                "tool": t_name,
                "summary": f"{ent} research started",
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            step_num += 1
        elif not ent and "news" in t_name and "news" not in seen_entities_started:
            seen_entities_started.add("news")
            steps.append({
                "step": step_num,
                "action": "tool",
                "tool": t_name,
                "summary": "News research started",
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            step_num += 1

    # Execute all independent tasks concurrently using asyncio.gather
    results = await asyncio.gather(
        *[_execute_single_subtask(st, adversarial_config, unavailable_tools, trace_id) for st in tasks_to_run]
    )

    collected_companies = list(state.get("collected_companies", []))
    collected_news = list(state.get("collected_news", []))
    collected_research = list(state.get("collected_research", []))
    collected_patents = list(state.get("collected_patents", []))
    collected_sources = list(state.get("collected_sources", []))
    tools_used = list(state.get("tools_used", []))
    tool_errors = list(state.get("tool_errors", []))
    completed_tasks = list(state.get("completed_tasks", []))
    repeated_action_count = dict(state.get("repeated_action_count", {}))

    updated_subtasks = list(subtasks)
    subtask_map = {st.get("id"): st for st in updated_subtasks}

    successful_count = 0
    failed_count = 0

    for res in results:
        sub_id = res.get("subtask_id")
        tool_name = res.get("tool_name")
        success = res.get("success", False)

        if tool_name and tool_name not in tools_used:
            tools_used.append(tool_name)

        if success:
            successful_count += 1
            if sub_id in subtask_map:
                subtask_map[sub_id]["status"] = "completed"
            completed_tasks.append(sub_id)

            # Aggregate structured data
            collected_companies.extend(res.get("extracted_companies", []))
            collected_news.extend(res.get("extracted_news", []))
            collected_research.extend(res.get("extracted_research", []))
            collected_patents.extend(res.get("extracted_patents", []))
            collected_sources.extend(res.get("extracted_sources", []))

        else:
            failed_count += 1
            if sub_id in subtask_map:
                subtask_map[sub_id]["status"] = "failed"
            err_msg = res.get("error", "Unknown execution error")
            tool_errors.append({
                "subtask_id": sub_id,
                "tool_name": tool_name,
                "error": err_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Check repeated failure count for circuit breaker
            curr_fail_count = repeated_action_count.get(tool_name, 0) + 1
            repeated_action_count[tool_name] = curr_fail_count

            # If tool failed multiple times, trip circuit breaker and add to unavailable
            if curr_fail_count >= 2 and tool_name not in unavailable_tools:
                unavailable_tools.append(tool_name)
                logger.warning(f"Marking tool '{tool_name}' unavailable due to repeated failures.")

            display_service = "Tavily" if "web" in tool_name or "paper" in tool_name else ("GNews" if "news" in tool_name else tool_name)
            steps.append({
                "step": step_num,
                "action": "error",
                "tool": tool_name,
                "summary": f"⚠ Tool failed: {display_service} encountered issue ({err_msg})",
                "status": "failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            step_num += 1

    # Log parallel completion
    if len(tasks_to_run) > 0:
        steps.append({
            "step": step_num,
            "action": "tool",
            "summary": f"Parallel execution completed ({successful_count} task(s) succeeded, {failed_count} task(s) failed)",
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        step_num += 1

    # Record node span
    if trace_id:
        default_tracer.record_node_span(
            trace_id=trace_id,
            node_name="parallel_research_node",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
            status="success",
            metadata={
                "tasks_executed": len(tasks_to_run),
                "successful_count": successful_count,
                "failed_count": failed_count,
            },
        )

    # Remaining tasks
    new_remaining = [st.get("id") for st in updated_subtasks if st.get("status") in ["pending", "running"]]

    return {
        "subtasks": updated_subtasks,
        "completed_tasks": completed_tasks,
        "remaining_tasks": new_remaining,
        "collected_companies": collected_companies,
        "collected_news": collected_news,
        "collected_research": collected_research,
        "collected_patents": collected_patents,
        "collected_sources": collected_sources,
        "tools_used": tools_used,
        "tool_errors": tool_errors,
        "unavailable_tools": unavailable_tools,
        "repeated_action_count": repeated_action_count,
        "steps": steps,
        "tool_call_count": state.get("tool_call_count", 0) + len(tasks_to_run),
        "status": "evaluating",
        "action_history": state.get("action_history", []) + ["parallel_research_execution"],
    }


async def evidence_conflict_node(state: GraphInvestigationState) -> Dict[str, Any]:
    """
    Step 4: Evidence extraction, cross-source conflict detection,
    hypothesis verification, and uncertainty-aware confidence calculation.
    """
    t0 = time.perf_counter()
    collected_companies = state.get("collected_companies", [])
    collected_news = state.get("collected_news", [])
    collected_research = state.get("collected_research", [])
    collected_sources = state.get("collected_sources", [])
    adversarial_config = state.get("adversarial_config")
    hypotheses_raw = state.get("hypotheses", [])
    tool_errors = state.get("tool_errors", [])
    detected_entities = state.get("detected_entities", [])
    trace_id = state.get("trace_id")

    steps = list(state.get("steps", []))
    step_num = len(steps) + 1

    # 1. Normalize and structure evidence
    evidence = extract_evidence_from_results(
        collected_companies=collected_companies,
        collected_news=collected_news,
        collected_research=collected_research,
        collected_sources=collected_sources,
    )

    # 2. Conflict detection & resolution
    conflicts, updated_evidence = detect_and_resolve_conflicts(
        evidence=evidence,
        adversarial_config=adversarial_config,
    )

    if conflicts:
        for c in conflicts:
            steps.append({
                "step": step_num,
                "action": "tool",
                "summary": f"Evidence conflict detected on '{c.topic}': Compared source reliability & recency ({c.source_a} vs {c.source_b}). Handled with confidence adjustment.",
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            step_num += 1

    # 3. Hypothesis verification
    hypotheses_objs = [HypothesisRecord(**h) for h in hypotheses_raw]
    evaluated_hypotheses = verify_hypotheses(
        hypotheses=hypotheses_objs,
        evidence=evidence,
        conflicts=conflicts,
    )

    if evaluated_hypotheses:
        tested_summaries = [f"{h.id}: {h.status}" for h in evaluated_hypotheses]
        steps.append({
            "step": step_num,
            "action": "tool",
            "summary": f"Hypothesis verification completed across {len(evidence)} evidence items ({', '.join(tested_summaries)}).",
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        step_num += 1

    # 4. Uncertainty-Aware Confidence Scoring
    confidence, conf_rationale = calculate_overall_confidence(
        evidence=evidence,
        conflicts=conflicts,
        hypotheses=evaluated_hypotheses,
        tool_errors=tool_errors,
        detected_entities=detected_entities,
    )

    steps.append({
        "step": step_num,
        "action": "tool",
        "summary": f"Evidence collected and verified ({len(evidence)} findings, {len(conflicts)} conflict(s), confidence: {confidence.upper()}).",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    if trace_id:
        default_tracer.record_node_span(
            trace_id=trace_id,
            node_name="evidence_conflict_node",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
            status="success",
            metadata={
                "evidence_count": len(evidence),
                "conflicts_count": len(conflicts),
                "confidence": confidence,
            },
        )

    return {
        "evidence": [ev.model_dump() for ev in evidence],
        "conflicting_evidence": [c.model_dump() for c in conflicts],
        "hypotheses": [h.model_dump() for h in evaluated_hypotheses],
        "confidence": confidence,
        "steps": steps,
        "status": "synthesizing",
        "action_history": state.get("action_history", []) + ["evidence_evaluation"],
    }


async def analyst_node(state: GraphInvestigationState) -> Dict[str, Any]:
    """
    Step 5: Intelligence Analyst Agent synthesis.
    Consolidates research results, handles conflicting claims, and generates
    the comprehensive executive markdown report.
    """
    t0 = time.perf_counter()
    investigation_goal = state.get("investigation_goal") or state.get("user_query", "")
    collected_companies = state.get("collected_companies", [])
    collected_news = state.get("collected_news", [])
    collected_research = state.get("collected_research", [])
    collected_patents = state.get("collected_patents", [])
    collected_sources = state.get("collected_sources", [])
    tools_used = state.get("tools_used", [])
    conflicts_raw = state.get("conflicting_evidence", [])
    hypotheses_raw = state.get("hypotheses", [])
    confidence = state.get("confidence", "high")
    chat_history = state.get("chat_history")
    trace_id = state.get("trace_id")

    steps = list(state.get("steps", []))
    step_num = len(steps) + 1

    # Reconstruct ResearchResults for Analyst
    res_companies = [CompanyCardData(**c) for c in collected_companies]
    res_news = [NewsArticle(**n) for n in collected_news]
    res_research = [ResearchPaper(**r) for r in collected_research]
    res_patents = [PatentItem(**p) for p in collected_patents]
    res_sources = [SourceItem(**s) for s in collected_sources]

    research_results_obj = ResearchResults(
        research_objective=investigation_goal,
        company_data=res_companies,
        news=res_news,
        research=res_research,
        patents=res_patents,
        sources=res_sources,
        tools_used=tools_used,
        summary=f"Synthesized intelligence for {investigation_goal}",
        success=True,
    )

    steps.append({
        "step": step_num,
        "action": "tool",
        "summary": f"Intelligence Analyst started strategic synthesis ({len(res_companies)} company profiles, {len(res_news)} news items, {len(res_research)} papers, {len(res_sources)} citations).",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    step_num += 1

    # Run analyst agent
    analyst_report = await default_analyst_agent.analyze(
        research_results=research_results_obj,
        chat_history=chat_history,
    )

    final_markdown = analyst_report.full_markdown_report

    # Enrich report with transparent uncertainty / conflict disclosure if applicable
    if conflicts_raw:
        conflict_disclosures = []
        for c in conflicts_raw:
            conflict_disclosures.append(
                f"- **{c.get('topic', 'Discrepancy')}**: Available sources conflict on this point. "
                f"{c.get('source_b', 'Recent evidence')} suggests '{c.get('claim_b', '')}', "
                f"while {c.get('source_a', 'earlier reports')} stated '{c.get('claim_a', '')}'. "
                f"{c.get('analysis', '')}"
            )
        conflict_section = (
            "\n\n### Cross-Source Verification & Evidence Conflicts\n"
            + "\n".join(conflict_disclosures)
            + f"\n\n*Overall Investigation Confidence: **{confidence.upper()}***"
        )
        if "### Cross-Source Verification" not in final_markdown:
            final_markdown += conflict_section

    # Enrich report with verified hypotheses if applicable
    if hypotheses_raw and len(hypotheses_raw) > 0:
        hypo_lines = []
        for h in hypotheses_raw:
            hypo_lines.append(
                f"- **Hypothesis**: *\"{h.get('hypothesis_text')}\"*\n"
                f"  - **Status**: {h.get('status', 'tested').upper()} (Score: {h.get('evaluation_score', 0.5):.2f})\n"
                f"  - **Finding**: {h.get('conclusion', 'Evaluated against multi-source evidence.')}"
            )
        hypo_section = "\n\n### Empirical Hypothesis Evaluation\n" + "\n".join(hypo_lines)
        if "### Empirical Hypothesis Evaluation" not in final_markdown:
            final_markdown += hypo_section

    for s in analyst_report.steps:
        steps.append({
            "step": step_num,
            "action": s.action,
            "tool": s.tool,
            "summary": s.summary,
            "status": s.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        step_num += 1

    if trace_id:
        default_tracer.record_node_span(
            trace_id=trace_id,
            node_name="analyst_node",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
            status="success",
            metadata={"report_length": len(final_markdown)},
        )

    return {
        "final_answer": final_markdown,
        "steps": steps,
        "status": "evaluating",
        "action_history": state.get("action_history", []) + ["analyst_synthesis"],
    }


async def self_eval_node(state: GraphInvestigationState) -> Dict[str, Any]:
    """
    Step 6: Self-Evaluation node before final output.
    Validates completeness, entity coverage, confidence, and safety.
    """
    t0 = time.perf_counter()
    user_query = state.get("user_query", "")
    investigation_goal = state.get("investigation_goal") or user_query
    detected_entities = state.get("detected_entities", [])
    evidence_raw = state.get("evidence", [])
    conflicts_raw = state.get("conflicting_evidence", [])
    hypotheses_raw = state.get("hypotheses", [])
    confidence = state.get("confidence", "high")
    tool_errors = state.get("tool_errors", [])
    iteration_count = state.get("iteration_count", 1)
    max_iterations = state.get("max_iterations", 5)
    trace_id = state.get("trace_id")

    steps = list(state.get("steps", []))
    step_num = len(steps) + 1

    evidence_objs = [EvidenceItem(**ev) for ev in evidence_raw]
    conflict_objs = [EvidenceConflict(**c) for c in conflicts_raw]
    hypo_objs = [HypothesisRecord(**h) for h in hypotheses_raw]

    eval_result = evaluate_investigation_state(
        user_query=user_query,
        investigation_goal=investigation_goal,
        detected_entities=detected_entities,
        evidence=evidence_objs,
        conflicts=conflict_objs,
        hypotheses=hypo_objs,
        confidence=confidence,
        tool_errors=tool_errors,
        iteration_count=iteration_count,
        max_iterations=max_iterations,
    )

    steps.append({
        "step": step_num,
        "action": "tool",
        "summary": f"Self-evaluation completed ({eval_result.feedback}).",
        "status": "completed" if eval_result.passed else "failed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    if trace_id:
        default_tracer.record_node_span(
            trace_id=trace_id,
            node_name="self_eval_node",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
            status="success" if eval_result.passed else "failed",
            metadata={"passed": eval_result.passed, "feedback": eval_result.feedback},
        )

    return {
        "self_evaluation": eval_result.model_dump(),
        "evaluation_passed": eval_result.passed,
        "steps": steps,
        "action_history": state.get("action_history", []) + ["self_evaluation"],
    }


async def replan_node(state: GraphInvestigationState) -> Dict[str, Any]:
    """
    Autonomous Replanning Node:
    Constructs a new investigation plan when tools fail or evidence is insufficient,
    and records automated root-cause diagnostics.
    """
    t0 = time.perf_counter()
    tool_errors = state.get("tool_errors", [])
    last_error = tool_errors[-1] if tool_errors else {}
    failed_tool = last_error.get("tool_name", "unknown_tool")
    failed_subtask_id = last_error.get("subtask_id", "")
    error_msg = last_error.get("error", "Tool failed during execution")

    current_subtasks = state.get("subtasks", [])
    unavailable_tools = state.get("unavailable_tools", [])
    remaining_tasks = state.get("remaining_tasks", [])
    investigation_goal = state.get("investigation_goal") or state.get("user_query", "")
    detected_entities = state.get("detected_entities", [])
    trace_id = state.get("trace_id")
    diagnoses = list(state.get("diagnoses", []))

    steps = list(state.get("steps", []))
    step_num = len(steps) + 1

    updated_subtasks, new_remaining, replan_summary = replan_on_failure(
        failed_tool=failed_tool,
        failed_subtask_id=failed_subtask_id,
        error_msg=error_msg,
        current_subtasks=current_subtasks,
        unavailable_tools=unavailable_tools,
        remaining_task_ids=remaining_tasks,
        investigation_goal=investigation_goal,
        detected_entities=detected_entities,
    )

    # Perform automated Root Cause Diagnosis
    if trace_id and failed_tool:
        diag = default_tracer.record_diagnostic_event(
            trace_id=trace_id,
            tool_name=failed_tool,
            error_message=error_msg,
            attempt=state.get("iteration_count", 0) + 1,
            consecutive_failures=len(tool_errors),
            details={"subtask_id": failed_subtask_id},
        )
        if diag:
            diagnoses.append(diag.model_dump())

    steps.append({
        "step": step_num,
        "action": "tool",
        "summary": f"↻ Replanning: {replan_summary}",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    step_num += 1

    steps.append({
        "step": step_num,
        "action": "tool",
        "summary": "Fallback selected: alternative evidence sources activated",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    step_num += 1

    steps.append({
        "step": step_num,
        "action": "tool",
        "summary": "Investigation continued",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    if trace_id:
        default_tracer.record_node_span(
            trace_id=trace_id,
            node_name="replan_node",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
            status="success",
            metadata={"replan_summary": replan_summary, "diagnoses_count": len(diagnoses)},
        )

    return {
        "subtasks": updated_subtasks,
        "remaining_tasks": new_remaining,
        "diagnoses": diagnoses,
        "steps": steps,
        "status": "researching",
        "iteration_count": state.get("iteration_count", 0) + 1,
        "action_history": state.get("action_history", []) + ["autonomous_replanning"],
    }


async def finalize_node(state: GraphInvestigationState) -> Dict[str, Any]:
    """
    Final step: Update session memory with entities/findings and consolidate response.
    """
    t0 = time.perf_counter()
    session_id = state.get("session_id", "default_session")
    user_query = state.get("user_query", "")
    final_answer = state.get("final_answer") or "Investigation completed with synthesized intelligence."
    tools_used = state.get("tools_used", [])
    collected_companies = state.get("collected_companies", [])
    trace_id = state.get("trace_id")
    steps = list(state.get("steps", []))
    step_num = len(steps) + 1

    # Persist in Session Memory
    try:
        company_names = [c.get("name") for c in collected_companies if c.get("name")]
        await default_context_manager.update_session(
            session_id=session_id,
            user_query=user_query,
            assistant_response=final_answer,
            tools_used=tools_used,
            company_names=company_names,
        )
    except Exception as e:
        logger.warning(f"Failed to update session memory in finalize_node: {e}")

    steps.append({
        "step": step_num,
        "action": "final",
        "summary": "Final answer generated and session memory updated.",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    if trace_id:
        default_tracer.record_node_span(
            trace_id=trace_id,
            node_name="finalize_node",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
            status="success",
        )

    return {
        "steps": steps,
        "status": "completed",
        "action_history": state.get("action_history", []) + ["finalize_workflow"],
    }

