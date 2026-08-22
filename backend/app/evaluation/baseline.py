"""
Fixed Single-Shot Baseline Implementation for Empirical Comparison (Task 6).

Represents a traditional non-agentic linear research pipeline:
1. Performs a single direct keyword search without dynamic planning or entity decomposition.
2. Directly prompts the LLM without parallel branching, failure recovery, or conflict detection.
3. If an API error occurs, fails immediately without autonomous replanning.

Used to benchmark the measurable advantages of the LangGraph Dynamic Agent Framework.
"""

import time
import logging
from typing import Any, Dict, List, Optional

from app.agent.state import (
    AgentRunRequest,
    AgentRunResponse,
    StepActivity,
    CompanyCardData,
    NewsArticle,
    SourceItem,
)
from app.agent.tool_registry import default_tool_registry
from app.ai.gemini_service import gemini_service

logger = logging.getLogger("evaluation_baseline")


class SingleShotBaselineRunner:
    """Fixed-sequence non-agentic baseline."""

    async def run(self, request: AgentRunRequest) -> AgentRunResponse:
        """Executes a rigid, single-step research pipeline."""
        start_time = time.perf_counter()
        goal = request.goal
        adv_config = request.adversarial_config or {}

        steps: List[StepActivity] = []
        step_num = 1

        steps.append(
            StepActivity(
                step=step_num,
                action="tool",
                summary=f"Baseline: Starting single-shot execution for '{goal}'",
                status="completed",
            )
        )
        step_num += 1

        # 1. Single direct web search call
        search_tool = default_tool_registry.get_tool("search_web")
        search_results_raw = ""
        sources: List[SourceItem] = []
        news: List[NewsArticle] = []
        companies: List[CompanyCardData] = []

        # Check for simulated failure
        if adv_config.get("force_tavily_fail") or adv_config.get("force_repeated_tool_fail") == "search_web":
            steps.append(
                StepActivity(
                    step=step_num,
                    action="error",
                    tool="search_web",
                    summary="Baseline: Primary search failed with 503 error. No replanning mechanism.",
                    status="failed",
                )
            )
            # Baseline crashes / fails on tool error
            return AgentRunResponse(
                success=False,
                answer="Error: Baseline search pipeline failed. No fallback mechanism available.",
                steps=steps,
                tools_used=["search_web"],
                iterations=1,
                session_id=request.session_id or "baseline-session",
                error="Search service unavailable",
                confidence="low",
            )

        try:
            if search_tool:
                obs = await search_tool.execute(query=goal)
                search_results_raw = str(obs)
                sources = search_tool.extract_sources(obs)
                news = search_tool.extract_news(obs)
                steps.append(
                    StepActivity(
                        step=step_num,
                        action="tool",
                        tool="search_web",
                        summary=f"Baseline: Retrieved {len(sources)} search sources",
                        status="completed",
                    )
                )
                step_num += 1
        except Exception as e:
            logger.warning(f"Baseline search error: {e}")
            steps.append(
                StepActivity(
                    step=step_num,
                    action="error",
                    summary=f"Baseline: Search failed ({e})",
                    status="failed",
                )
            )
            return AgentRunResponse(
                success=False,
                answer=f"Baseline execution failed: {e}",
                steps=steps,
                tools_used=["search_web"],
                iterations=1,
                session_id=request.session_id or "baseline-session",
                error=str(e),
                confidence="low",
            )

        # 2. Direct LLM Prompting without multi-agent analysis or conflict verification
        prompt = (
            f"You are a basic intelligence summary assistant. Summarize the following information for the objective:\n\n"
            f"Objective: {goal}\n\n"
            f"Search Evidence:\n{search_results_raw[:2500]}\n\n"
            f"Write a standard brief summary."
        )

        try:
            if gemini_service.is_configured():
                report_text = await gemini_service.generate_text(prompt=prompt)
            else:
                report_text = f"Baseline summary: Retrieved factual data regarding {goal} across {len(sources)} sources."
            steps.append(
                StepActivity(
                    step=step_num,
                    action="final",
                    summary="Baseline: Generated single-shot summary",
                    status="completed",
                )
            )
        except Exception as e:
            report_text = f"Baseline summary for {goal} based on retrieved evidence ({e})."

        return AgentRunResponse(
            success=True,
            answer=report_text,
            steps=steps,
            tools_used=["search_web"],
            iterations=1,
            session_id=request.session_id or "baseline-session",
            sources=sources,
            news=news,
            companies=companies,
            confidence="medium",
        )
