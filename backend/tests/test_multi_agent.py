import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.orchestrator import MultiAgentOrchestrator
from app.agent.research_agent import ResearchAgent
from app.agent.intelligence_analyst import IntelligenceAnalystAgent
from app.agent.state import AgentRunRequest
from app.agent.tool_registry import ToolRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_multi_agent")


async def run_multi_agent_tests():
    registry = ToolRegistry()
    research_agent = ResearchAgent(tool_registry=registry)
    analyst_agent = IntelligenceAnalystAgent()
    orchestrator = MultiAgentOrchestrator(
        research_agent=research_agent, analyst_agent=analyst_agent
    )

    test_queries = [
        "NVIDIA latest AI developments",
        "Compare NVIDIA and AMD in AI chips",
        "Latest developments in generative AI",
    ]

    print("\n=======================================================")
    print("STARTING MULTI-AGENT ARCHITECTURE VERIFICATION SUITE")
    print("=======================================================")

    for idx, query in enumerate(test_queries, 1):
        print(f"\n-------------------------------------------------------")
        print(f"TEST {idx}: '{query}'")
        print(f"-------------------------------------------------------")

        req = AgentRunRequest(goal=query, max_iterations=4)
        response = await orchestrator.run(req)

        print(f"Success: {response.success}")
        print(f"Total Collaborative Steps: {len(response.steps)}")
        print(f"Tools Used by Research Agent: {response.tools_used}")
        print(f"Extracted Companies: {[c.name for c in response.companies]}")
        print(f"Extracted News: {len(response.news)}")
        print(f"Extracted Research Papers: {len(response.research)}")
        print(f"Extracted External Sources: {len(response.sources)}")
        print("\n--- ACTIVITY LOG SUMMARY ---")
        for s in response.steps:
            icon = "[OK]" if s.status == "completed" else ("[FAIL]" if s.status == "failed" else "[INFO]")
            print(f"  {icon} [Step {s.step}] {s.summary}")

        print("\n--- ANALYST REPORT PREVIEW ---")
        print(response.answer[:350] + ("..." if len(response.answer) > 350 else ""))

        # Assertions
        assert response.success is True, f"Test {idx} failed: response.success is False"
        assert len(response.steps) >= 4, f"Test {idx} failed: too few steps ({len(response.steps)})"
        assert len(response.answer) > 50, f"Test {idx} failed: answer too short"

        # Verify collaboration markers in steps
        step_summaries = [s.summary.lower() for s in response.steps]
        has_orchestrator = any("orchestrator" in s for s in step_summaries)
        has_research = any("research agent" in s for s in step_summaries)
        has_analyst = any("intelligence analyst" in s or "analyst" in s for s in step_summaries)
        has_handover = any("passed to intelligence analyst" in s or "handover" in s or "analyst" in s for s in step_summaries)

        assert has_orchestrator, f"Test {idx} failed: missing Orchestrator log"
        assert has_research, f"Test {idx} failed: missing Research Agent log"
        assert has_analyst, f"Test {idx} failed: missing Intelligence Analyst log"
        assert has_handover, f"Test {idx} failed: missing handover step between agents"

        print(f"\n>>> TEST {idx} PASSED!")

    print("\n=======================================================")
    print("ALL 3 MULTI-AGENT ARCHITECTURE TESTS PASSED SUCCESSFULLY!")
    print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(run_multi_agent_tests())
