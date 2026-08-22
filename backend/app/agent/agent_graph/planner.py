"""
Dynamic Planner and Autonomous Replanning Engine for LangGraph.

Inspects user query and retrieved conversational context to construct a
dynamic, query-tailored investigation plan with prioritized subtasks,
rather than executing a fixed static sequence.
Supports dynamic hypothesis formulation and autonomous replanning on failure.
"""

import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple
from app.services.gnews_service import detect_company
from app.agent.agent_graph.state import SubTask, HypothesisRecord

logger = logging.getLogger("graph_planner")

# Recognized major enterprise/tech entities
KNOWN_COMPANIES = [
    "NVIDIA", "AMD", "INTEL", "MICROSOFT", "GOOGLE", "APPLE",
    "AMAZON", "META", "OPENAI", "ANTHROPIC", "TESLA", "QUALCOMM",
    "TSMC", "BROADCOM", "IBM", "ORACLE", "SALESFORCE", "ADOBE",
    "CISCO", "ARM", "ASML", "SNOWFLAKE", "PALANTIR"
]


def extract_entities_from_query(query: str) -> List[str]:
    """Identify explicit company/organization entities in the query."""
    upper_query = query.upper()
    tokens = [t.strip(",.!?\"'();:") for t in upper_query.split()]
    found: List[str] = []
    
    # Priority for known companies
    for comp in KNOWN_COMPANIES:
        if comp in tokens or f" {comp} " in f" {upper_query} ":
            if comp not in found:
                found.append(comp)

    # Fallback to detector
    if not found:
        detected = detect_company(query)
        if detected:
            found.append(detected.upper())

    return found


def classify_query_intent(query: str, entities: List[str]) -> Tuple[str, str]:
    """
    Classifies query into an intent category and execution strategy:
    - 'single_company': Single entity research & profile
    - 'multi_comparison': Multi-entity comparative intelligence
    - 'scientific_research': Frontier papers, models, scientific topics
    - 'market_overview': Broad industry trends and market analysis
    """
    lower = query.lower()
    
    is_research_paper = any(k in lower for k in [
        "paper", "papers", "research on", "arxiv", "openreview", "academic",
        "benchmark", "survey", "reasoning", "mechanistic", "architecture"
    ])
    
    is_comparison = any(k in lower for k in [
        "compare", "comparison", "versus", "vs", "difference", "against",
        "head to head", "competing", "better than"
    ]) or len(entities) >= 2

    if is_research_paper and len(entities) == 0:
        return "scientific_research", "Academic Paper Search -> Technical Web -> Academic Synthesis"
    elif is_comparison or len(entities) >= 2:
        return "multi_comparison", "Parallel Entity Intelligence -> Cross-Source News -> Conflict/Hypothesis Verification -> Comparative Analyst"
    elif len(entities) == 1:
        return "single_company", "Company Profile & Financials -> Recent News -> Web Signals -> Intelligence Analyst"
    else:
        return "market_overview", "Live Web Search -> Industry News -> Strategic Analyst"


def generate_initial_hypotheses(query: str, entities: List[str], intent: str) -> List[HypothesisRecord]:
    """Generate testable analytical hypotheses for comparative or analytical queries."""
    hypotheses: List[HypothesisRecord] = []
    
    if intent == "multi_comparison" and len(entities) >= 2:
        e1, e2 = entities[0], entities[1]
        hypotheses.append(
            HypothesisRecord(
                id=f"hypo-{uuid.uuid4().hex[:6]}",
                hypothesis_text=f"{e1} holds strong competitive positioning in enterprise market share relative to {e2}.",
                target_entities=[e1, e2],
                supporting_evidence=[],
                contradicting_evidence=[],
                evaluation_score=0.5,
                status="formulated",
            )
        )
        if any(w in query.lower() for w in ["chip", "chips", "hardware", "gpu", "accelerator"]):
            hypotheses.append(
                HypothesisRecord(
                    id=f"hypo-{uuid.uuid4().hex[:6]}",
                    hypothesis_text=f"{e2}'s latest silicon hardware targets high memory bandwidth and open software ecosystems to challenge {e1}.",
                    target_entities=[e1, e2],
                    supporting_evidence=[],
                    contradicting_evidence=[],
                    evaluation_score=0.5,
                    status="formulated",
                )
            )
    elif "reasoning" in query.lower() or "llm" in query.lower():
        hypotheses.append(
            HypothesisRecord(
                id=f"hypo-{uuid.uuid4().hex[:6]}",
                hypothesis_text="Recent frontier research focuses on inference-time compute scaling and test-time reasoning search.",
                target_entities=[],
                supporting_evidence=[],
                contradicting_evidence=[],
                evaluation_score=0.5,
                status="formulated",
            )
        )

    return hypotheses


def create_dynamic_plan(
    user_query: str,
    investigation_goal: str,
    relevant_context: Optional[Dict[str, Any]] = None,
    max_tool_calls: int = 8,
    max_iterations: int = 5,
    adversarial_config: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[SubTask], List[HypothesisRecord], List[str], List[str]]:
    """
    Constructs an investigation plan tailored to the specific query requirements.
    """
    target_query = investigation_goal or user_query
    entities = extract_entities_from_query(target_query)
    
    # Check context for entities if none found in raw query
    if not entities and relevant_context:
        ctx_companies = relevant_context.get("active_companies") or []
        for c in ctx_companies:
            if c.upper() not in entities:
                entities.append(c.upper())

    intent, strategy_desc = classify_query_intent(target_query, entities)
    subtasks: List[SubTask] = []
    
    if intent == "multi_comparison":
        # Parallel subtasks for each entity
        for ent in entities:
            subtasks.append(
                SubTask(
                    id=f"subtask-comp-{ent.lower()}",
                    title=f"Gather company profile and intelligence for {ent}",
                    tool_name="search_company_intelligence",
                    tool_input={"company_name": ent},
                    target_entity=ent,
                    priority=1,
                    status="pending",
                )
            )
            subtasks.append(
                SubTask(
                    id=f"subtask-news-{ent.lower()}",
                    title=f"Fetch latest news and market signals for {ent}",
                    tool_name="search_news",
                    tool_input={"query": ent},
                    target_entity=ent,
                    priority=2,
                    status="pending",
                )
            )
        
        # Web comparison research
        subtasks.append(
            SubTask(
                id="subtask-web-comparison",
                title=f"Investigate comparative analysis: {target_query}",
                tool_name="search_web",
                tool_input={"query": f"{target_query} comparison specs benchmark"},
                target_entity=", ".join(entities),
                priority=3,
                status="pending",
            )
        )
        
    elif intent == "single_company":
        ent = entities[0]
        subtasks.append(
            SubTask(
                id=f"subtask-comp-{ent.lower()}",
                title=f"Fetch verified profile and intelligence for {ent}",
                tool_name="search_company_intelligence",
                tool_input={"company_name": ent},
                target_entity=ent,
                priority=1,
                status="pending",
            )
        )
        subtasks.append(
            SubTask(
                id=f"subtask-news-{ent.lower()}",
                title=f"Query recent news articles for {ent}",
                tool_name="search_news",
                tool_input={"query": ent},
                target_entity=ent,
                priority=2,
                status="pending",
            )
        )
        subtasks.append(
            SubTask(
                id=f"subtask-web-{ent.lower()}",
                title=f"Search live web intelligence for {ent}",
                tool_name="search_web",
                tool_input={"query": f"{ent} overview strategic products"},
                target_entity=ent,
                priority=3,
                status="pending",
            )
        )
        
    elif intent == "scientific_research":
        subtasks.append(
            SubTask(
                id="subtask-papers",
                title=f"Search arXiv & OpenReview papers for '{target_query}'",
                tool_name="search_research_papers",
                tool_input={"query": target_query},
                priority=1,
                status="pending",
            )
        )
        subtasks.append(
            SubTask(
                id="subtask-web-research",
                title=f"Search technical web publications on '{target_query}'",
                tool_name="search_web",
                tool_input={"query": f"{target_query} research developments findings"},
                priority=2,
                status="pending",
            )
        )
        subtasks.append(
            SubTask(
                id="subtask-news-research",
                title=f"Search scientific news for '{target_query}'",
                tool_name="search_news",
                tool_input={"query": target_query},
                priority=3,
                status="pending",
            )
        )
        
    else:  # market_overview
        subtasks.append(
            SubTask(
                id="subtask-web-market",
                title=f"Search live web for '{target_query}'",
                tool_name="search_web",
                tool_input={"query": target_query},
                priority=1,
                status="pending",
            )
        )
        subtasks.append(
            SubTask(
                id="subtask-news-market",
                title=f"Query market news for '{target_query}'",
                tool_name="search_news",
                tool_input={"query": target_query},
                priority=2,
                status="pending",
            )
        )

    # Budget constraint
    subtasks = subtasks[:max_tool_calls]

    # Task plan summary
    task_plan = [
        {
            "phase": "Context & Plan",
            "description": f"Query classified as '{intent}'. Strategy: {strategy_desc}",
            "intent": intent,
        },
        {
            "phase": "Data Collection",
            "subtasks_count": len(subtasks),
            "tools": list({st.tool_name for st in subtasks}),
        },
        {
            "phase": "Evidence & Conflict Verification",
            "description": "Cross-check multi-source findings, resolve contradictions, score confidence.",
        },
        {
            "phase": "Strategic Intelligence Synthesis",
            "description": "Generate executive intelligence report via Intelligence Analyst Agent.",
        },
        {
            "phase": "Self-Evaluation",
            "description": "Evaluate completeness, entity coverage, confidence, and answer quality.",
        },
    ]

    hypotheses = generate_initial_hypotheses(target_query, entities, intent)
    remaining_tasks = [st.id for st in subtasks]
    detected_topics = [intent]

    return task_plan, subtasks, hypotheses, entities, remaining_tasks


def replan_on_failure(
    failed_tool: str,
    failed_subtask_id: str,
    error_msg: str,
    current_subtasks: List[Dict[str, Any]],
    unavailable_tools: List[str],
    remaining_task_ids: List[str],
    investigation_goal: str,
    detected_entities: List[str],
) -> Tuple[List[Dict[str, Any]], List[str], str]:
    """
    Autonomous replanning when a tool encounters an unrecoverable failure
    or when evidence is insufficient.
    """
    logger.info(f"Autonomous Replanning triggered after '{failed_tool}' failure: {error_msg}")
    
    updated_subtasks: List[Dict[str, Any]] = []
    for st in current_subtasks:
        st_obj = dict(st)
        if st_obj.get("id") == failed_subtask_id:
            st_obj["status"] = "failed"
            st_obj["error"] = error_msg
        updated_subtasks.append(st_obj)

    # Determine fallback strategy
    replanned_new_tasks: List[Dict[str, Any]] = []
    replan_summary = ""

    if failed_tool in ["search_web", "tavily"]:
        # Fallback to GNews and Company Intelligence
        replan_summary = "Primary web search unavailable. Routing to news aggregation and direct company profiles."
        for ent in detected_entities or [detect_company(investigation_goal) or "Tech Industry"]:
            new_id = f"fallback-news-{ent.lower()}-{uuid.uuid4().hex[:4]}"
            if new_id not in [s.get("id") for s in updated_subtasks]:
                replanned_new_tasks.append(
                    SubTask(
                        id=new_id,
                        title=f"[Fallback] Query latest news for {ent}",
                        tool_name="search_news",
                        tool_input={"query": ent},
                        target_entity=ent,
                        priority=1,
                        status="pending",
                    ).model_dump()
                )
    elif failed_tool in ["search_news", "gnews"]:
        # Fallback to Tavily web search
        replan_summary = "News tool unavailable. Routing to Tavily live web search for recent events."
        if "search_web" not in unavailable_tools:
            replanned_new_tasks.append(
                SubTask(
                    id=f"fallback-web-{uuid.uuid4().hex[:4]}",
                    title=f"[Fallback] Search web news for '{investigation_goal}'",
                    tool_name="search_web",
                    tool_input={"query": f"{investigation_goal} breaking news latest"},
                    priority=1,
                    status="pending",
                ).model_dump()
            )
    elif failed_tool in ["search_research_papers"]:
        # Fallback to general web with academic query
        replan_summary = "Research paper tool unavailable. Searching web archives for technical summaries."
        if "search_web" not in unavailable_tools:
            replanned_new_tasks.append(
                SubTask(
                    id=f"fallback-web-paper-{uuid.uuid4().hex[:4]}",
                    title=f"[Fallback] Web search for technical publications on '{investigation_goal}'",
                    tool_name="search_web",
                    tool_input={"query": f"{investigation_goal} arxiv paper summary"},
                    priority=1,
                    status="pending",
                ).model_dump()
            )
    else:
        replan_summary = f"Tool '{failed_tool}' failed. Continuing with existing multi-source intelligence."

    # Append new fallback subtasks
    updated_subtasks.extend(replanned_new_tasks)
    
    # Recompute remaining task IDs
    new_remaining = [
        s["id"] for s in updated_subtasks
        if s.get("status") in ["pending", "running"] and s["id"] != failed_subtask_id
    ]

    return updated_subtasks, new_remaining, replan_summary
