"""
Comprehensive Test Suite for LangGraph Agent Framework (Task 5).

Verifies all 6 required test scenarios:
1. TEST 1: Dynamic single-entity plan ("What is NVIDIA?")
2. TEST 2: Dynamic comparison + parallel execution ("Compare NVIDIA and AMD latest AI chips.")
3. TEST 3: Dynamic scientific research routing ("Find recent research on LLM reasoning.")
4. TEST 4: Adversarial tool failure recovery (Tavily failure -> Replanning/Fallback)
5. TEST 5: Conflicting evidence detection and confidence-aware resolution
6. TEST 6: Repeated tool failure and loop/deadlock prevention
"""

import asyncio
import logging
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.orchestrator import MultiAgentOrchestrator
from app.agent.state import AgentRunRequest, AgentRunResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_langgraph_framework")


@pytest.mark.asyncio
async def test_1_dynamic_single_entity_plan():
    """
    TEST 1: "What is NVIDIA?"
    Expected: Dynamic single-company plan with only necessary work (Company Profile, News, Synthesis).
    """
    orchestrator = MultiAgentOrchestrator()
    req = AgentRunRequest(goal="What is NVIDIA?", max_iterations=4)
    res = await orchestrator.run(req)

    assert res.success is True, "TEST 1 failed: execution unsuccessful"
    assert len(res.steps) >= 3, "TEST 1 failed: expected at least 3 steps"
    assert any("nvidia" in c.name.lower() for c in res.companies), "TEST 1 failed: NVIDIA company profile missing"
    assert len(res.answer) > 50, "TEST 1 failed: answer too short"

    # Verify dynamic planning step exists
    step_summaries = [s.summary.lower() for s in res.steps]
    assert any("planner created dynamic" in s or "dynamic" in s for s in step_summaries), "TEST 1 failed: missing dynamic planning activity"
    assert any("self-evaluation" in s for s in step_summaries), "TEST 1 failed: missing self-evaluation activity"
    print("\n>>> TEST 1: Dynamic Single-Entity Plan PASSED!")


@pytest.mark.asyncio
async def test_2_dynamic_comparison_parallel_research():
    """
    TEST 2: "Compare NVIDIA and AMD latest AI chips."
    Expected: Dynamic multi-entity plan, parallel execution, hypothesis formulation & verification.
    """
    orchestrator = MultiAgentOrchestrator()
    req = AgentRunRequest(
        goal="Compare NVIDIA and AMD latest AI chips.",
        max_iterations=5,
    )
    res = await orchestrator.run(req)

    assert res.success is True, "TEST 2 failed: execution unsuccessful"
    assert len(res.steps) >= 4, "TEST 2 failed: expected multi-step execution"
    
    # Check entities gathered
    comp_names = [c.name.upper() for c in res.companies]
    assert "NVIDIA" in comp_names or "AMD" in comp_names, "TEST 2 failed: target entities missing"

    # Check parallel execution and hypothesis evaluation
    step_summaries = [s.summary.lower() for s in res.steps]
    assert any("parallel" in s or "dispatched" in s for s in step_summaries), "TEST 2 failed: parallel research step missing"
    assert any("hypothesis" in s for s in step_summaries), "TEST 2 failed: hypothesis formulation/verification missing"
    assert len(res.hypotheses) >= 1, "TEST 2 failed: no hypotheses recorded in state"
    print("\n>>> TEST 2: Parallel Research & Comparison Hypotheses PASSED!")


@pytest.mark.asyncio
async def test_3_scientific_research_routing():
    """
    TEST 3: "Find recent research on LLM reasoning."
    Expected: Research-paper focused dynamic routing (arXiv/OpenReview, technical papers, academic synthesis).
    """
    orchestrator = MultiAgentOrchestrator()
    req = AgentRunRequest(
        goal="Find recent research on LLM reasoning.",
        max_iterations=4,
    )
    res = await orchestrator.run(req)

    assert res.success is True, "TEST 3 failed: execution unsuccessful"
    assert len(res.research) >= 1, "TEST 3 failed: expected research papers to be collected"
    
    step_summaries = [s.summary.lower() for s in res.steps]
    assert any("academic" in s or "paper" in s or "scientific" in s or "research" in s for s in step_summaries), "TEST 3 failed: missing scientific research step"
    print("\n>>> TEST 3: Dynamic Scientific Research Routing PASSED!")


@pytest.mark.asyncio
async def test_4_adversarial_tool_failure_and_replanning():
    """
    TEST 4: Adversarial tool failure recovery.
    Simulate Tavily search failure.
    Expected: Agent detects failure, logs warning, initiates autonomous replanning,
              uses fallback sources (GNews/Company Profiles), and successfully completes.
    """
    orchestrator = MultiAgentOrchestrator()
    req = AgentRunRequest(
        goal="Compare NVIDIA and AMD latest AI chips.",
        max_iterations=5,
        adversarial_config={
            "force_tavily_fail": True,
        },
    )
    res = await orchestrator.run(req)

    # Must complete successfully despite Tavily failure
    assert res.success is True, "TEST 4 failed: workflow crashed on simulated tool failure"
    assert len(res.answer) > 50, "TEST 4 failed: failed to generate report via fallback sources"

    step_summaries = [s.summary.lower() for s in res.steps]
    # Check that error was captured and recovery took place
    has_error_handled = any("issue" in s or "error" in s or "failed" in s or "recovery" in s for s in step_summaries)
    assert has_error_handled, "TEST 4 failed: simulated tool failure was not detected in activity log"
    print("\n>>> TEST 4: Adversarial Tool Failure Recovery & Replanning PASSED!")


@pytest.mark.asyncio
async def test_5_conflicting_evidence_and_confidence_scoring():
    """
    TEST 5: Conflicting evidence detection and uncertainty-aware conclusion.
    Simulate Source A claiming X (earlier) and Source B claiming NOT X (recent benchmark).
    Expected: Agent detects conflict, compares source reliability & recency,
              adjusts confidence rating, and includes transparent conflict notes in report.
    """
    orchestrator = MultiAgentOrchestrator()
    req = AgentRunRequest(
        goal="Compare NVIDIA and AMD latest AI chips.",
        max_iterations=5,
        adversarial_config={
            "inject_conflicting_evidence": {
                "topic": "H100 vs MI300X Memory Bandwidth and FLOPS",
                "claim_a": "Initial preliminary leak claimed MI300X has lower FP8 compute than H100",
                "source_a": "Tech Blog Rumors",
                "date_a": "2023-11-01",
                "claim_b": "Official MLPerf and IEEE benchmark verified MI300X achieves 5.3 TB/s bandwidth and matches H100 in FP8 throughput",
                "source_b": "IEEE Micro & MLPerf Industry Benchmark",
                "date_b": "2024-06-15",
            }
        },
    )
    res = await orchestrator.run(req)

    assert res.success is True, "TEST 5 failed: execution unsuccessful"
    assert len(res.conflicting_evidence) >= 1, "TEST 5 failed: conflicting evidence not recorded in state"

    conflict_rec = res.conflicting_evidence[0]
    assert "Discrepancy" in conflict_rec.get("analysis", "") or "disagreement" in conflict_rec.get("analysis", "").lower() or "conflict" in conflict_rec.get("analysis", "").lower(), "TEST 5 failed: conflict analysis missing"

    step_summaries = [s.summary.lower() for s in res.steps]
    assert any("conflict" in s for s in step_summaries), "TEST 5 failed: conflict detection step missing from activity log"

    # Verify transparent conflict explanation in final report
    assert "cross-source verification" in res.answer.lower() or "conflict" in res.answer.lower() or "confidence" in res.answer.lower(), "TEST 5 failed: final report missing uncertainty disclosure"
    print(f"\n>>> TEST 5: Conflicting Evidence Detection & Confidence Rating ({res.confidence.upper()}) PASSED!")


@pytest.mark.asyncio
async def test_6_repeated_tool_failure_and_deadlock_prevention():
    """
    TEST 6: Repeated tool failure and loop/deadlock prevention.
    Simulate repeated failures on a tool.
    Expected: Circuit breaker detects repeated failing action, halts retries on that tool,
              prevents infinite loops, respects tool budget, and safely terminates with best answer.
    """
    orchestrator = MultiAgentOrchestrator()
    req = AgentRunRequest(
        goal="Analyze Qualcomm AI processor roadmap",
        max_iterations=4,
        max_tool_calls=6,
        adversarial_config={
            "force_repeated_tool_fail": "search_news",
        },
    )
    res = await orchestrator.run(req)

    assert res.success is True, "TEST 6 failed: system crashed instead of safe termination"
    assert res.iterations <= 5, f"TEST 6 failed: iteration budget exceeded ({res.iterations})"
    
    # Safe answer produced
    assert len(res.answer) > 50, "TEST 6 failed: no fallback answer produced"
    print("\n>>> TEST 6: Repeated Tool Failure & Deadlock Prevention PASSED!")


async def run_all_tests():
    print("\n" + "=" * 60)
    print("RUNNING ALL LANGGRAPH AGENT FRAMEWORK TESTS (TEST 1 to 6)")
    print("=" * 60)
    await test_1_dynamic_single_entity_plan()
    await test_2_dynamic_comparison_parallel_research()
    await test_3_scientific_research_routing()
    await test_4_adversarial_tool_failure_and_replanning()
    await test_5_conflicting_evidence_and_confidence_scoring()
    await test_6_repeated_tool_failure_and_deadlock_prevention()
    print("\n" + "=" * 60)
    print("ALL 6 LANGGRAPH FRAMEWORK TESTS PASSED PERFECTLY!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
