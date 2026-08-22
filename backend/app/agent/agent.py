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

    async def run(self, request: AgentRunRequest) -> AgentRunResponse:
        """
        Execute the autonomous ReAct reasoning loop.
        """
        state = AgentState(
            goal=request.goal.strip(),
            max_iterations=request.max_iterations or 5,
        )

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
                tool_name = decision.tool_name or "search_demo"
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

                # Safe activity log: tool selected
                state.steps.append(
                    StepActivity(
                        step=step_num,
                        action="tool",
                        tool=tool_name,
                        summary=f"Selected tool '{tool_name}' with parameters: {json.dumps(tool_input)}",
                        status="completed",
                    )
                )

                # Execute tool
                try:
                    observation = await tool.execute(**tool_input)
                    extracted_news = tool.extract_news(observation)
                    if extracted_news:
                        state.collected_news.extend(extracted_news)

                    state.history.append(
                        ToolExecutionRecord(
                            step=step_num,
                            tool_name=tool_name,
                            tool_input=tool_input,
                            observation=observation,
                            success=True,
                            extracted_news=extracted_news,
                        )
                    )
                    state.steps.append(
                        StepActivity(
                            step=step_num,
                            action="tool",
                            tool=tool_name,
                            summary=f"Tool '{tool_name}' executed. Observation received.",
                            status="completed",
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
                            summary=f"Error executing tool '{tool_name}'. Proceeding to next step.",
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
                )
                state.is_completed = True

            return AgentRunResponse(
                success=True,
                answer=state.final_answer or "Investigation concluded with no report generated.",
                steps=state.steps,
                tools_used=state.tools_used,
                iterations=state.current_iteration,
                news_results=state.collected_news,
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
                error=str(e),
            )


# Default agent instance
default_agent = CompetitiveIntelligenceAgent()
