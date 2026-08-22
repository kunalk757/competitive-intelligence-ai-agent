import uuid
import logging
from typing import Optional, List
from app.agent.state import (
    AgentRunRequest,
    AgentRunResponse,
    StepActivity,
    ResearchResults,
    AnalystReport,
)
from app.agent.research_agent import ResearchAgent, default_research_agent
from app.agent.intelligence_analyst import IntelligenceAnalystAgent, default_analyst_agent
from app.context.context_manager import ContextManager, default_context_manager

logger = logging.getLogger("orchestrator")


class MultiAgentOrchestrator:
    """
    Multi-Agent Orchestrator for Competitive Intelligence with Context & Memory Management.
    
    Coordinates the collaborative pipeline:
    1. Context Manager (Disambiguates follow-ups, retrieves session memory, resolves pronouns)
    2. Research Agent (Live factual data collection from Tavily, GNews, Company APIs)
    3. Intelligence Analyst Agent (Strategic synthesis, competitive analysis, recommendations)
    4. Session Memory Update (Persists extracted entities, topics, and key findings)
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
        Execute the stateful multi-agent orchestration pipeline.
        
        Flow:
        User Query -> Understand Query -> Retrieve Relevant Context -> Plan Investigation ->
        Orchestrator -> Research Agent -> Research Results -> Intelligence Analyst -> Final Report -> Update Session Context
        """
        goal = request.goal.strip()
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        logger.info(f"Orchestrator received request for session '{session_id}': '{goal}'")

        all_steps: List[StepActivity] = []
        step_index = 1

        # 1. Understand Query & Retrieve Relevant Context from Session Memory
        investigation_goal = goal
        context_summary = "Initializing fresh multi-agent investigation."
        try:
            relevant_context = await self.context_manager.get_relevant_context(
                session_id=session_id,
                current_query=goal,
                chat_history=request.chat_history,
            )
            investigation_goal = relevant_context.contextual_query or goal

            if relevant_context.has_context:
                context_parts = []
                if relevant_context.active_companies:
                    context_parts.append(f"Entities: {', '.join(relevant_context.active_companies)}")
                if relevant_context.active_topics:
                    context_parts.append(f"Topic: {', '.join(relevant_context.active_topics)}")
                if relevant_context.context_notes:
                    context_parts.append(f"Notes: {'; '.join(relevant_context.context_notes)}")
                
                context_summary = f"Retrieved relevant session context ({' | '.join(context_parts)}). Contextual target: '{investigation_goal}'"
            else:
                context_summary = f"Planning multi-agent investigation for: '{investigation_goal}'"

        except Exception as e:
            logger.warning(f"Context retrieval non-fatal warning: {e}. Proceeding with raw query.")
            context_summary = f"Planning multi-agent investigation: '{goal}'"

        all_steps.append(
            StepActivity(
                step=step_index,
                action="tool",
                summary=context_summary,
                status="completed",
            )
        )
        step_index += 1

        # 2. Execute Research Agent with Contextualized Objective
        research_results: Optional[ResearchResults] = None
        try:
            research_results = await self.research_agent.execute_research(
                objective=investigation_goal,
                max_iterations=request.max_iterations or 5,
                chat_history=request.chat_history,
            )

            # Append research agent steps
            for s in research_results.steps:
                all_steps.append(
                    StepActivity(
                        step=step_index,
                        action=s.action,
                        tool=s.tool,
                        summary=s.summary,
                        status=s.status,
                    )
                )
                step_index += 1

        except Exception as e:
            logger.exception(f"Research Agent failed: {e}")
            all_steps.append(
                StepActivity(
                    step=step_index,
                    action="error",
                    summary=f"Research Agent encountered critical error: {str(e)}",
                    status="failed",
                )
            )
            return AgentRunResponse(
                success=False,
                answer="Investigation failed during the data collection phase.",
                steps=all_steps,
                tools_used=[],
                iterations=1,
                session_id=session_id,
                error=str(e),
            )

        # 3. Handover: Pass research results to Intelligence Analyst
        handover_summary = (
            f"Research results passed to Intelligence Analyst "
            f"({len(research_results.company_data)} company profiles, {len(research_results.news)} news articles, "
            f"{len(research_results.research)} research papers, {len(research_results.sources)} external citations)"
        )
        all_steps.append(
            StepActivity(
                step=step_index,
                action="tool",
                summary=handover_summary,
                status="completed",
            )
        )
        step_index += 1

        # 4. Execute Intelligence Analyst Agent
        analyst_report: Optional[AnalystReport] = None
        try:
            analyst_report = await self.analyst_agent.analyze(
                research_results=research_results,
                chat_history=request.chat_history,
            )

            # Append analyst agent steps
            for s in analyst_report.steps:
                all_steps.append(
                    StepActivity(
                        step=step_index,
                        action=s.action,
                        tool=s.tool,
                        summary=s.summary,
                        status=s.status,
                    )
                )
                step_index += 1

        except Exception as e:
            logger.exception(f"Intelligence Analyst failed: {e}")
            all_steps.append(
                StepActivity(
                    step=step_index,
                    action="error",
                    summary=f"Intelligence Analyst encountered an issue during synthesis: {str(e)}",
                    status="failed",
                )
            )
            fallback_answer = (
                f"### Research Collection Completed\n\n"
                f"The Research Agent successfully gathered intelligence for **{investigation_goal}**, but the analysis synthesis encountered an issue.\n\n"
                f"Please review the collected company profiles, news items, and research citations attached above."
            )
            return AgentRunResponse(
                success=True,
                answer=fallback_answer,
                steps=all_steps,
                tools_used=research_results.tools_used,
                iterations=len(research_results.tools_used) + 1,
                session_id=session_id,
                companies=research_results.company_data,
                news=research_results.news,
                news_results=research_results.news,
                research=research_results.research,
                patents=research_results.patents,
                sources=research_results.sources,
                error=f"Analyst notice: {str(e)}",
            )

        # 5. Update Session Context in Memory Service
        final_answer = analyst_report.full_markdown_report or "Investigation concluded with no report generated."
        try:
            company_names = [c.name for c in research_results.company_data]
            await self.context_manager.update_session(
                session_id=session_id,
                user_query=goal,
                assistant_response=final_answer,
                tools_used=research_results.tools_used,
                key_findings=analyst_report.key_findings,
                company_names=company_names,
            )
            all_steps.append(
                StepActivity(
                    step=step_index,
                    action="tool",
                    summary=f"Updated session memory ({session_id}) with current entities and strategic findings.",
                    status="completed",
                )
            )
            step_index += 1
        except Exception as e:
            logger.warning(f"Failed to update session memory: {e}")

        # 6. Finalize Orchestration
        all_steps.append(
            StepActivity(
                step=step_index,
                action="final",
                summary="Orchestrator consolidated multi-agent findings into final intelligence report.",
                status="completed",
            )
        )

        return AgentRunResponse(
            success=True,
            answer=final_answer,
            steps=all_steps,
            tools_used=research_results.tools_used,
            iterations=len(research_results.tools_used) + 1,
            session_id=session_id,
            companies=research_results.company_data,
            news=research_results.news,
            news_results=research_results.news,
            research=research_results.research,
            patents=research_results.patents,
            sources=research_results.sources,
        )


default_orchestrator = MultiAgentOrchestrator()

