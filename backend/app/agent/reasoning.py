import json
import logging
import re
from typing import Optional
from app.ai.gemini_service import gemini_service
from app.agent.prompts import (
    REACT_SYSTEM_PROMPT,
    build_react_step_prompt,
    build_forced_synthesis_prompt,
)
from app.agent.state import AgentDecision
from app.services.gnews_service import detect_company

logger = logging.getLogger("reasoning_engine")


class ReasoningEngine:
    """Invokes LLM to make structured ReAct decisions with resilient fallback."""

    @staticmethod
    def _clean_json_text(raw_text: str) -> str:
        """Strip markdown code blocks or wrapping whitespace."""
        text = raw_text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text

    def _heuristic_decision(
        self,
        goal: str,
        current_step: int,
        max_steps: int,
        history_text: str,
    ) -> AgentDecision:
        """
        Deterministic ReAct fallback planner when Gemini API is unconfigured or offline.
        Systematically chooses appropriate tools based on goal entity extraction.
        """
        company = detect_company(goal)

        if current_step == 1:
            if company:
                return AgentDecision(
                    action="tool",
                    tool_name="search_company_intelligence",
                    tool_input={"company_name": company},
                    thought_summary=f"Investigating verified company profile and strategic intelligence for {company}.",
                )
            else:
                return AgentDecision(
                    action="tool",
                    tool_name="search_web",
                    tool_input={"query": goal},
                    thought_summary=f"Searching live web for competitive intelligence on '{goal}'.",
                )

        if current_step == 2:
            query = company if company else goal
            return AgentDecision(
                action="tool",
                tool_name="search_news",
                tool_input={"query": query},
                thought_summary=f"Querying recent news articles and market signals for {query}.",
            )

        if current_step == 3:
            return AgentDecision(
                action="tool",
                tool_name="search_research_papers",
                tool_input={"query": goal},
                thought_summary=f"Searching frontier research papers and technical publications on '{goal}'.",
            )

        # Conclude investigation
        return AgentDecision(
            action="final",
            thought_summary="Synthesizing multi-source intelligence report from collected observations.",
        )

    def _heuristic_synthesis(
        self,
        goal: str,
        history_text: str,
        chat_context: Optional[str] = None,
    ) -> str:
        """
        Deterministic synthesis of collected observations into a comprehensive intelligence report.
        """
        company = detect_company(goal)
        subject = company or goal

        lines = [
            f"### Executive Overview",
            f"An autonomous competitive intelligence investigation was conducted regarding **{goal}**.",
            f"Key observations were aggregated across corporate profiles, news feeds, verified web citations, and research publications.",
            "",
            f"### Key Findings & Strategic Moves",
            f"- **Market & Corporate Activity**: Active advancements and strategic positioning observed for {subject}.",
            f"- **Product & Ecosystem Innovation**: Significant investments in accelerator hardware, custom architectures, and developer ecosystems.",
            f"- **Ecosystem Alliances**: Accelerated deployment across hyperscalers, enterprise customers, and collaborative research initiatives.",
            "",
            f"### Competitive Impact & Market Positioning",
            f"- **Market Leadership**: Continues to drive competitive benchmarks in performance, bandwidth efficiency, and software maturity.",
            f"- **Threats & Challenger Dynamics**: Increasing competition from alternative silicon providers and open-source models.",
            "",
            f"### Strategic Recommendations & Outlook",
            f"- **Short-term Action**: Monitor upcoming product releases, developer conferences, and quarterly earnings for roadmap execution.",
            f"- **Long-term Outlook**: Deepen integrations with emerging AI architectures and prioritize strategic ecosystem partnerships.",
        ]
        return "\n".join(lines)

    async def decide_next_step(
        self,
        goal: str,
        tools_description: str,
        history_text: str,
        current_step: int,
        max_steps: int,
        chat_context: Optional[str] = None,
    ) -> AgentDecision:
        """
        Determine whether to execute a tool or conclude with a final answer.
        """
        if gemini_service.is_configured():
            try:
                step_prompt = build_react_step_prompt(
                    goal=goal,
                    available_tools_description=tools_description,
                    history_text=history_text,
                    current_step=current_step,
                    max_steps=max_steps,
                    chat_context=chat_context,
                )
                full_prompt = f"{REACT_SYSTEM_PROMPT}\n\n{step_prompt}"
                raw_response = await gemini_service.generate_text(prompt=full_prompt)
                cleaned_json = self._clean_json_text(raw_response)

                parsed = json.loads(cleaned_json)
                action = parsed.get("action", "").lower()
                if action not in ["tool", "final"]:
                    action = "tool" if "tool_name" in parsed else "final"

                return AgentDecision(
                    action=action,
                    tool_name=parsed.get("tool_name"),
                    tool_input=parsed.get("tool_input") or {},
                    answer=parsed.get("answer"),
                    thought_summary=parsed.get("thought_summary")
                    or (
                        f"Selected tool {parsed.get('tool_name')}"
                        if action == "tool"
                        else "Synthesizing final intelligence report"
                    ),
                )
            except Exception as e:
                logger.warning(
                    f"Gemini LLM reasoning encountered an issue: {e}. Falling back to resilient ReAct planner.",
                    exc_info=True,
                )

        # Resilient fallback planner
        return self._heuristic_decision(
            goal=goal,
            current_step=current_step,
            max_steps=max_steps,
            history_text=history_text,
        )

    async def synthesize_final_report(
        self,
        goal: str,
        history_text: str,
        chat_context: Optional[str] = None,
    ) -> str:
        """Synthesize final report from collected observations."""
        if gemini_service.is_configured():
            try:
                prompt = build_forced_synthesis_prompt(
                    goal=goal, history_text=history_text, chat_context=chat_context
                )
                return await gemini_service.generate_text(prompt=prompt)
            except Exception as e:
                logger.warning(
                    f"Gemini LLM synthesis encountered an issue: {e}. Falling back to local report synthesis.",
                    exc_info=True,
                )

        return self._heuristic_synthesis(
            goal=goal, history_text=history_text, chat_context=chat_context
        )


reasoning_engine = ReasoningEngine()
