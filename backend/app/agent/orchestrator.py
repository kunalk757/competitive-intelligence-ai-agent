import uuid
import logging
from typing import Optional, List, Dict, Any
from app.agent.state import (
    AgentRunRequest,
    AgentRunResponse,
    StepActivity,
    CompanyCardData,
    NewsArticle,
    ResearchPaper,
    PatentItem,
    SourceItem,
)
from app.agent.research_agent import ResearchAgent, default_research_agent
from app.agent.intelligence_analyst import IntelligenceAnalystAgent, default_analyst_agent
from app.context.context_manager import ContextManager, default_context_manager
from app.agent.agent_graph.graph import investigation_graph
from app.agent.agent_graph.checkpoint import get_graph_config

logger = logging.getLogger("orchestrator")


class MultiAgentOrchestrator:
    """
    Multi-Agent Orchestrator powered by LangGraph.
    
    Coordinates the dynamic, stateful investigation lifecycle:
    1. Context & Memory Management (Follow-up disambiguation, session context)
    2. Dynamic Planner (Query intent classification, hypothesis formulation, subtask decomposition)
    3. Conditional Router & Parallel Research (Independent branches, concurrency)
    4. Evidence Evaluation & Conflict Resolution (Source weighting, contradiction handling)
    5. Intelligence Analyst Synthesis (Strategic intelligence report generation)
    6. Self-Evaluation Node (Pre-output completeness & confidence verification)
    7. Autonomous Replanning & Tool Fallback (Failure recovery, circuit breakers)
    8. Checkpointing & Session Memory (State persistence)
    """

    def __init__(
        self,
        research_agent: Optional[ResearchAgent] = None,
        analyst_agent: Optional[IntelligenceAnalystAgent] = None,
        context_manager: Optional[ContextManager] = None,
    ):
        self.research_agent = research_agent or default_research_agent
        self.analyst_agent = analyst_agent or default_analyst_agent
        self.context_manager = context_manager or default_context_manager

    async def run(self, request: AgentRunRequest) -> AgentRunResponse:
        """
        Execute the dynamic LangGraph multi-agent investigation workflow.
        """
        goal = request.goal.strip()
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        logger.info(f"LangGraph Orchestrator received request for session '{session_id}': '{goal}'")

        # Initial state channels for LangGraph
        initial_state = {
            "user_query": goal,
            "session_id": session_id,
            "conversation_id": session_id,
            "chat_history": request.chat_history,
            "investigation_goal": goal,
            "max_tool_calls": getattr(request, "max_tool_calls", 8) or 8,
            "max_iterations": request.max_iterations or 5,
            "adversarial_config": getattr(request, "adversarial_config", None),
            "tool_call_count": 0,
            "iteration_count": 0,
            "tools_used": [],
            "completed_tasks": [],
            "remaining_tasks": [],
            "collected_companies": [],
            "collected_news": [],
            "collected_research": [],
            "collected_patents": [],
            "collected_sources": [],
            "evidence": [],
            "conflicting_evidence": [],
            "hypotheses": [],
            "tool_errors": [],
            "unavailable_tools": [],
            "repeated_action_count": {},
            "action_history": [],
            "steps": [],
            "status": "initializing",
            "confidence": "high",
        }

        config = get_graph_config(session_id=session_id)

        try:
            # Execute compiled LangGraph StateGraph
            final_state = await investigation_graph.ainvoke(initial_state, config=config)

            # Convert step dictionaries back to StepActivity models
            raw_steps = final_state.get("steps", [])
            converted_steps: List[StepActivity] = []
            for s in raw_steps:
                converted_steps.append(
                    StepActivity(
                        step=s.get("step", 1),
                        action=s.get("action", "tool"),
                        tool=s.get("tool"),
                        summary=s.get("summary", ""),
                        status=s.get("status", "completed"),
                        timestamp=s.get("timestamp"),
                    )
                )

            # Deduplicate structured companies
            raw_companies = final_state.get("collected_companies", [])
            seen_comps = set()
            unique_companies: List[CompanyCardData] = []
            for c in raw_companies:
                norm_name = c.get("name", "").lower().strip()
                if norm_name and norm_name not in seen_comps:
                    seen_comps.add(norm_name)
                    unique_companies.append(CompanyCardData(**c))

            # Deduplicate structured news
            raw_news = final_state.get("collected_news", [])
            seen_news = set()
            unique_news: List[NewsArticle] = []
            for n in raw_news:
                key = n.get("url") or n.get("title")
                if key and key not in seen_news:
                    seen_news.add(key)
                    unique_news.append(NewsArticle(**n))

            # Deduplicate research papers
            raw_research = final_state.get("collected_research", [])
            seen_res = set()
            unique_research: List[ResearchPaper] = []
            for r in raw_research:
                key = r.get("url") or r.get("title")
                if key and key not in seen_res:
                    seen_res.add(key)
                    unique_research.append(ResearchPaper(**r))

            # Patents
            raw_patents = final_state.get("collected_patents", [])
            unique_patents = [PatentItem(**p) for p in raw_patents]

            # Sources
            raw_sources = final_state.get("collected_sources", [])
            seen_src = set()
            unique_sources: List[SourceItem] = []
            for s in raw_sources:
                u = s.get("url")
                if u and u not in seen_src:
                    seen_src.add(u)
                    unique_sources.append(SourceItem(**s))

            final_answer = final_state.get("final_answer") or "Investigation completed with synthesized intelligence."
            tools_used = final_state.get("tools_used", [])
            confidence = final_state.get("confidence", "high")
            hypotheses = final_state.get("hypotheses", [])
            conflicts = final_state.get("conflicting_evidence", [])

            return AgentRunResponse(
                success=True,
                answer=final_answer,
                steps=converted_steps,
                tools_used=tools_used,
                iterations=final_state.get("iteration_count", 1),
                session_id=session_id,
                companies=unique_companies,
                news=unique_news,
                news_results=unique_news,
                research=unique_research,
                patents=unique_patents,
                sources=unique_sources,
                confidence=confidence,
                hypotheses=hypotheses,
                conflicting_evidence=conflicts,
            )

        except Exception as e:
            logger.exception(f"LangGraph execution encountered an error: {e}")
            return AgentRunResponse(
                success=False,
                answer="Investigation failed during LangGraph execution.",
                steps=[
                    StepActivity(
                        step=1,
                        action="error",
                        summary=f"LangGraph execution halted: {str(e)}",
                        status="failed",
                    )
                ],
                tools_used=[],
                iterations=1,
                session_id=session_id,
                error=str(e),
            )


default_orchestrator = MultiAgentOrchestrator()

