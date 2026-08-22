import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.state import AgentRunRequest, AgentDecision
from app.agent.agent import CompetitiveIntelligenceAgent
from app.agent.tool_registry import ToolRegistry, SearchDemoTool
from app.agent.reasoning import ReasoningEngine


async def test_react_loop_orchestration():
    print("\n--- Test 1: Full ReAct Loop (Tool -> Observation -> Final) ---")
    
    # Custom registry with search_demo
    registry = ToolRegistry()
    
    # Mock reasoning engine to simulate Gemini ReAct decisions
    mock_reasoning = AsyncMock(spec=ReasoningEngine)
    
    # Step 1: LLM decides to call search_demo tool
    # Step 2: LLM observes tool output and returns final answer
    mock_reasoning.decide_next_step.side_effect = [
        AgentDecision(
            action="tool",
            tool_name="search_demo",
            tool_input={"query": "AI chip competitive landscape"},
            thought_summary="Need to gather market intelligence on AI chips.",
        ),
        AgentDecision(
            action="final",
            answer="### Executive Summary\nThe AI chip landscape is dominated by custom silicon and accelerator architectures.\n\n### Key Findings\n- Major investments in high-bandwidth memory.\n- Rapid adoption of tensor cores.",
            thought_summary="Sufficient data gathered to compile final report.",
        ),
    ]

    agent = CompetitiveIntelligenceAgent(tool_registry=registry, reasoning=mock_reasoning)
    
    req = AgentRunRequest(goal="Analyze the competitive landscape for AI chips.", max_iterations=5)
    res = await agent.run(req)

    print(f"Success: {res.success}")
    print(f"Iterations: {res.iterations}")
    print(f"Tools Used: {res.tools_used}")
    print(f"Steps recorded: {len(res.steps)}")
    for s in res.steps:
        print(f"  Step {s.step} [{s.action}]: {s.summary}")
    print(f"Final Answer preview:\n{res.answer[:150]}...")

    assert res.success is True
    assert "search_demo" in res.tools_used
    assert res.iterations == 2
    assert "Executive Summary" in res.answer
    print(">>> Test 1 Passed!\n")


async def test_max_iteration_limit():
    print("--- Test 2: Max Iteration Limit Synthesis ---")
    registry = ToolRegistry()
    mock_reasoning = AsyncMock(spec=ReasoningEngine)
    
    # Simulate LLM continuing to request tools beyond limit
    mock_reasoning.decide_next_step.return_value = AgentDecision(
        action="tool",
        tool_name="search_demo",
        tool_input={"query": "AI chip power efficiency"},
        thought_summary="Need more power benchmarks.",
    )
    mock_reasoning.synthesize_final_report.return_value = "### Final Synthesized Report (Forced after max iterations)"

    agent = CompetitiveIntelligenceAgent(tool_registry=registry, reasoning=mock_reasoning)
    req = AgentRunRequest(goal="Deep dive on AI chip efficiency", max_iterations=3)
    res = await agent.run(req)

    print(f"Success: {res.success}")
    print(f"Iterations: {res.iterations}")
    print(f"Steps count: {len(res.steps)}")
    print(f"Final answer: {res.answer}")

    assert res.success is True
    assert res.iterations == 3
    assert "Final Synthesized Report" in res.answer
    print(">>> Test 2 Passed!\n")


async def test_tool_failure_graceful_recovery():
    print("--- Test 3: Unregistered Tool Recovery ---")
    registry = ToolRegistry()
    mock_reasoning = AsyncMock(spec=ReasoningEngine)
    
    mock_reasoning.decide_next_step.side_effect = [
        AgentDecision(
            action="tool",
            tool_name="non_existent_tool",
            tool_input={"query": "test"},
            thought_summary="Try invalid tool.",
        ),
        AgentDecision(
            action="final",
            answer="Recovered and concluded gracefully.",
            thought_summary="Conclude despite missing tool.",
        ),
    ]

    agent = CompetitiveIntelligenceAgent(tool_registry=registry, reasoning=mock_reasoning)
    req = AgentRunRequest(goal="Test resilience", max_iterations=4)
    res = await agent.run(req)

    print(f"Success: {res.success}")
    print(f"Final Answer: {res.answer}")
    assert res.success is True
    assert any(s.action == "error" for s in res.steps)
    print(">>> Test 3 Passed!\n")


if __name__ == "__main__":
    asyncio.run(test_react_loop_orchestration())
    asyncio.run(test_max_iteration_limit())
    asyncio.run(test_tool_failure_graceful_recovery())
