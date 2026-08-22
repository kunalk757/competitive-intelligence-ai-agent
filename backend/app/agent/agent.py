import json
import logging
from typing import Optional
from app.agent.state import (
    AgentState,
    AgentRunRequest,
    AgentRunResponse,
    StepActivity,
    ToolExecutionRecord,
)
from app.agent.tool_registry import ToolRegistry, default_tool_registry
from app.agent.reasoning import ReasoningEngine, reasoning_engine

logger = logging.getLogger("agent")


class CompetitiveIntelligenceAgent:
    """Autonomous ReAct Agent for competitive research and analysis."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        reasoning: Optional[ReasoningEngine] = None,
    ):
        self.tool_registry = tool_registry or default_tool_registry
        self.reasoning = reasoning or reasoning_engine

    def _format_history_text(self, history: list[ToolExecutionRecord]) -> str:
        """Format prior tool execution records into clean context for Gemini."""
        if not history:
            return ""
        blocks = []
        for rec in history:
            blocks.append(
                f"--- Step {rec.step} ---\n"
                f"Action: Tool '{rec.tool_name}'\n"
                f"Input: {json.dumps(rec.tool_input)}\n"
                f"Observation:\n{rec.observation}\n"
            )
        return "\n".join(blocks)

    def _format_chat_context(self, chat_history: Optional[list]) -> Optional[str]:
        if not chat_history:
            return None
        lines = []
        for msg in chat_history[-6:]:  # Keep recent context
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    async def run(self, request: AgentRunRequest) -> AgentRunResponse:
        """
        Execute the autonomous ReAct reasoning loop.
        """
        state = AgentState(
            goal=request.goal.strip(),
            max_iterations=request.max_iterations or 5,
        )

        chat_context = self._format_chat_context(request.chat_history)

        state.steps.append(
            StepActivity(
                step=0,
                action="final",
                summary=f"Agent started investigation: '{state.goal}'",
                status="completed",
            )
        )

        try:
            tools_description = self.tool_registry.get_tools_description()

            for step_num in range(1, state.max_iterations + 1):
                state.current_iteration = step_num
                history_text = self._format_history_text(state.history)

                # 1. Ask Gemini to decide next step
                decision = await self.reasoning.decide_next_step(
                    goal=state.goal,
                    tools_description=tools_description,
                    history_text=history_text,
                    current_step=step_num,
                    max_steps=state.max_iterations,
                    chat_context=chat_context,
                )

                # 2. If decision is FINAL answer
                if decision.action == "final" and decision.answer:
                    state.final_answer = decision.answer
                    state.is_completed = True
                    state.steps.append(
                        StepActivity(
                            step=step_num,
                            action="final",
                            summary="Agent concluded investigation and synthesized final intelligence report.",
                            status="completed",
                        )
                    )
                    break

                # 3. If decision is TOOL call
                tool_name = decision.tool_name or "search_web"
                tool_input = decision.tool_input or {}
                tool = self.tool_registry.get_tool(tool_name)

                if not tool:
                    # Tool not found: log observation error and let agent adapt
                    err_msg = f"Error: Tool '{tool_name}' is not registered."
                    state.history.append(
                        ToolExecutionRecord(
                            step=step_num,
                            tool_name=tool_name,
                            tool_input=tool_input,
                            observation=err_msg,
                            success=False,
                            error=err_msg,
                        )
                    )
                    state.steps.append(
                        StepActivity(
                            step=step_num,
                            action="error",
                            tool=tool_name,
                            summary=f"Attempted tool '{tool_name}' but tool is unavailable.",
                            status="failed",
                        )
                    )
                    continue

                if tool_name not in state.tools_used:
                    state.tools_used.append(tool_name)

                # Clean summary for user activity log
                step_summary = decision.thought_summary or f"Executing '{tool_name}'"
                state.steps.append(
                    StepActivity(
                        step=step_num,
                        action="tool",
                        tool=tool_name,
                        summary=step_summary,
                        status="completed",
                    )
                )

                # Execute tool
                try:
                    observation = await tool.execute(**tool_input)
                    
                    # Extract structured multi-source entities
                    extracted_news = tool.extract_news(observation)
                    extracted_companies = tool.extract_companies(observation)
                    extracted_research = tool.extract_research(observation)
                    extracted_patents = tool.extract_patents(observation)
                    extracted_sources = tool.extract_sources(observation)

                    if extracted_news:
                        state.collected_news.extend(extracted_news)
                    if extracted_companies:
                        state.collected_companies.extend(extracted_companies)
                    if extracted_research:
                        state.collected_research.extend(extracted_research)
                    if extracted_patents:
                        state.collected_patents.extend(extracted_patents)
                    if extracted_sources:
                        state.collected_sources.extend(extracted_sources)

                    state.history.append(
                        ToolExecutionRecord(
                            step=step_num,
                            tool_name=tool_name,
                            tool_input=tool_input,
                            observation=observation,
                            success=True,
                            extracted_news=extracted_news,
                            extracted_companies=extracted_companies,
                            extracted_research=extracted_research,
                            extracted_patents=extracted_patents,
                            extracted_sources=extracted_sources,
                        )
                    )
                except Exception as tool_err:
                    err_obs = f"Error executing tool '{tool_name}': {str(tool_err)}"
                    state.history.append(
                        ToolExecutionRecord(
                            step=step_num,
                            tool_name=tool_name,
                            tool_input=tool_input,
                            observation=err_obs,
                            success=False,
                            error=str(tool_err),
                        )
                    )
                    state.steps.append(
                        StepActivity(
                            step=step_num,
                            action="error",
                            tool=tool_name,
                            summary=f"Error executing '{tool_name}'. Proceeding to next step.",
                            status="failed",
                        )
                    )

            # If loop finished without final answer (hit max iterations)
            if not state.final_answer:
                history_text = self._format_history_text(state.history)
                state.steps.append(
                    StepActivity(
                        step=state.max_iterations + 1,
                        action="final",
                        summary="Iteration limit reached. Synthesizing final intelligence report from collected observations.",
                        status="completed",
                    )
                )
                state.final_answer = await self.reasoning.synthesize_final_report(
                    goal=state.goal,
                    history_text=history_text,
                    chat_context=chat_context,
                )
                state.is_completed = True

            # Deduplicate items by URL or name
            unique_companies = []
            seen_comp_names = set()
            for c in state.collected_companies:
                norm_c = c.name.lower()
                if norm_c not in seen_comp_names:
                    seen_comp_names.add(norm_c)
                    unique_companies.append(c)

            unique_news = []
            seen_news_urls = set()
            for n in state.collected_news:
                key = n.url or n.title
                if key not in seen_news_urls:
                    seen_news_urls.add(key)
                    unique_news.append(n)

            unique_research = []
            seen_research_urls = set()
            for r in state.collected_research:
                key = r.url or r.title
                if key not in seen_research_urls:
                    seen_research_urls.add(key)
                    unique_research.append(r)

            unique_sources = []
            seen_sources = set()
            for s in state.collected_sources:
                if s.url and s.url not in seen_sources:
                    seen_sources.add(s.url)
                    unique_sources.append(s)

            return AgentRunResponse(
                success=True,
                answer=state.final_answer or "Investigation concluded with no report generated.",
                steps=state.steps,
                tools_used=state.tools_used,
                iterations=state.current_iteration,
                news_results=unique_news,
                companies=unique_companies,
                news=unique_news,
                research=unique_research,
                patents=state.collected_patents,
                sources=unique_sources,
            )

        except Exception as e:
            logger.exception("Agent execution failed")
            return AgentRunResponse(
                success=False,
                answer="Agent run encountered an unexpected failure.",
                steps=state.steps,
                tools_used=state.tools_used,
                iterations=state.current_iteration,
                news_results=state.collected_news,
                companies=state.collected_companies,
                news=state.collected_news,
                research=state.collected_research,
                patents=state.collected_patents,
                sources=state.collected_sources,
                error=str(e),
            )


# Default agent instance
default_agent = CompetitiveIntelligenceAgent()
