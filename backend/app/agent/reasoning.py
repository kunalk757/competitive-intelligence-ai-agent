import json
import re
from typing import Optional
from app.ai.gemini_service import gemini_service
from app.agent.prompts import (
    REACT_SYSTEM_PROMPT,
    build_react_step_prompt,
    build_forced_synthesis_prompt,
)
from app.agent.state import AgentDecision


class ReasoningEngine:
    """Invokes the LLM to make structured ReAct decisions."""

    @staticmethod
    def _clean_json_text(raw_text: str) -> str:
        """Strip markdown code blocks or wrapping whitespace."""
        text = raw_text.strip()
        # Remove ```json ... ``` or ``` ... ``` wrappers
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text

    async def decide_next_step(
        self,
        goal: str,
        tools_description: str,
        history_text: str,
        current_step: int,
        max_steps: int,
    ) -> AgentDecision:
        """
        Calls Gemini to determine whether to execute a tool or conclude with a final answer.
        """
        step_prompt = build_react_step_prompt(
            goal=goal,
            available_tools_description=tools_description,
            history_text=history_text,
            current_step=current_step,
            max_steps=max_steps,
        )

        full_prompt = f"{REACT_SYSTEM_PROMPT}\n\n{step_prompt}"

        raw_response = await gemini_service.generate_text(prompt=full_prompt)
        cleaned_json = self._clean_json_text(raw_response)

        try:
            parsed = json.loads(cleaned_json)
            # Normalize action
            action = parsed.get("action", "").lower()
            if action not in ["tool", "final"]:
                # If ambiguous, check if answer or tool_name is present
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
            # Fallback if raw text wasn't pure JSON: treat as final answer or retry
            if "{" not in raw_response:
                return AgentDecision(
                    action="final",
                    answer=raw_response,
                    thought_summary="Generated response directly from analysis",
                )
            raise RuntimeError(
                f"Failed to parse agent decision from model output: {str(e)}. Raw output: {raw_response[:200]}"
            )

    async def synthesize_final_report(
        self,
        goal: str,
        history_text: str,
    ) -> str:
        """Forced synthesis when max iterations are exhausted."""
        prompt = build_forced_synthesis_prompt(goal=goal, history_text=history_text)
        return await gemini_service.generate_text(prompt=prompt)


reasoning_engine = ReasoningEngine()
