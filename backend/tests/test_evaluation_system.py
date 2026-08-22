"""
Unit and Integration Tests for Task 6 Evaluation Framework.

Tests:
1. Task completion scoring algorithm.
2. Groundedness and hallucination detection algorithms.
3. Recovery rate calculation for tool failure scenarios.
4. Multi-run consistency scoring algorithm.
5. Single-shot baseline execution and comparative differential.
6. Report generation and Markdown formatting.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.state import (
    AgentRunRequest,
    AgentRunResponse,
    CompanyCardData,
    NewsArticle,
    SourceItem,
    StepActivity,
)
from app.agent.agent_graph.state import EvidenceConflict
from app.evaluation.dataset import (
    EvaluationTestCase,
    EvaluationExpectedCriteria,
    get_evaluation_dataset,
)
from app.evaluation.metrics import (
    evaluate_task_completion,
    evaluate_groundedness_and_hallucination,
    evaluate_recovery_and_robustness,
    compute_consistency_score,
    evaluate_single_run,
    aggregate_evaluation_results,
)
from app.evaluation.baseline import SingleShotBaselineRunner
from app.evaluation.reporter import generate_markdown_report


def test_task_completion_evaluation():
    """Verify task completion scoring algorithm."""
    tc = EvaluationTestCase(
        id="TC-TEST-1",
        category="normal",
        name="Test Case 1",
        description="Verify completion",
        goal="What is NVIDIA's revenue and architecture?",
        expected=EvaluationExpectedCriteria(
            required_entities=["NVIDIA"],
            required_topics=["datacenter", "architecture"],
            min_evidence_count=2,
        ),
    )

    # Mock response fulfilling all criteria
    mock_resp = AgentRunResponse(
        success=True,
        answer="NVIDIA generates massive datacenter revenue with its latest Blackwell and Hopper GPU architecture.",
        companies=[CompanyCardData(name="NVIDIA", description="AI semiconductor leader.")],
        news=[NewsArticle(title="NVIDIA announces record revenue.", url="https://example.com/1", source="Reuters")],
        sources=[SourceItem(title="GPU Architecture", url="https://example.com/2", snippet="Datacenter compute.")],
        tools_used=["search_company", "search_news"],
        iterations=2,
        steps=[StepActivity(step=1, action="final", summary="Done", status="completed")],
        confidence="high",
    )

    score, reasons = evaluate_task_completion(tc, mock_resp)
    assert score >= 0.85, f"Expected high completion score, got {score}. Reasons: {reasons}"
    assert len(reasons) == 0, f"Expected 0 failure reasons, got {reasons}"


def test_groundedness_and_hallucination_evaluation():
    """Verify groundedness scoring and hallucination detection."""
    tc = EvaluationTestCase(
        id="TC-TEST-2",
        category="normal",
        name="Groundedness Test",
        description="Verify grounding",
        goal="Compare GPUs",
        expected=EvaluationExpectedCriteria(),
    )

    # Response well grounded in company/news snippets
    mock_resp = AgentRunResponse(
        success=True,
        answer=(
            "NVIDIA Corporation designs advanced graphics processing units for artificial intelligence.\n\n"
            "The Blackwell B200 platform delivers high throughput for deep learning workloads.\n\n"
            "Available sources conflict on exact yields, with preliminary estimates varying."
        ),
        companies=[CompanyCardData(name="NVIDIA Corporation", description="Advanced graphics processing units for artificial intelligence deep learning.")],
        news=[NewsArticle(title="Blackwell B200 platform delivers high throughput", url="https://example.com", source="TechCrunch")],
        tools_used=["search_company", "search_news"],
        iterations=2,
        steps=[],
    )

    groundedness, hallucination_rate, unsupported = evaluate_groundedness_and_hallucination(mock_resp, tc)
    assert groundedness >= 0.70, f"Expected groundedness >= 0.70, got {groundedness}"
    assert hallucination_rate <= 0.30, f"Expected hallucination rate <= 0.30, got {hallucination_rate}"


def test_recovery_evaluation():
    """Verify failure recovery evaluator."""
    tc = EvaluationTestCase(
        id="TC-TEST-3",
        category="tool_failure",
        name="Recovery Test",
        description="Verify recovery",
        goal="Compare chips",
        expected=EvaluationExpectedCriteria(expect_recovery=True),
    )

    # Successful recovery response
    recovered_resp = AgentRunResponse(
        success=True,
        answer="Investigation completed via fallback news and company profile sources.",
        steps=[
            StepActivity(step=1, action="error", summary="⚠ Tool failed: Tavily search outage", status="failed"),
            StepActivity(step=2, action="tool", summary="↻ Replanning: routing to GNews", status="completed"),
            StepActivity(step=3, action="tool", summary="✓ Fallback selected: GNews", status="completed"),
        ],
        tools_used=["search_news"],
        iterations=2,
    )

    rec_success, reasons = evaluate_recovery_and_robustness(tc, recovered_resp)
    assert rec_success is True, f"Expected recovery success, got {rec_success}"


def test_consistency_scoring():
    """Verify consistency computation across repeated runs."""
    run1 = AgentRunResponse(
        success=True,
        answer="Report 1 for NVIDIA and AMD.",
        companies=[CompanyCardData(name="NVIDIA"), CompanyCardData(name="AMD")],
        confidence="high",
        tools_used=["search_company"],
        iterations=2,
        steps=[],
    )
    run2 = AgentRunResponse(
        success=True,
        answer="Report 2 comparing NVIDIA vs AMD.",
        companies=[CompanyCardData(name="NVIDIA"), CompanyCardData(name="AMD")],
        confidence="high",
        tools_used=["search_company"],
        iterations=2,
        steps=[],
    )
    run3 = AgentRunResponse(
        success=True,
        answer="Report 3 on NVIDIA and AMD AI accelerators.",
        companies=[CompanyCardData(name="NVIDIA"), CompanyCardData(name="AMD")],
        confidence="high",
        tools_used=["search_company"],
        iterations=2,
        steps=[],
    )

    consistency = compute_consistency_score([run1, run2, run3])
    assert consistency >= 0.90, f"Expected high consistency >= 0.90, got {consistency}"


@pytest.mark.asyncio
async def test_baseline_runner_execution():
    """Verify single-shot baseline runner executes cleanly and handles errors."""
    baseline = SingleShotBaselineRunner()

    # Normal execution
    req_normal = AgentRunRequest(goal="What is Intel?")
    res_normal = await baseline.run(req_normal)
    assert res_normal.iterations == 1
    assert len(res_normal.answer) > 20

    # Failure execution (simulated Tavily outage)
    req_fail = AgentRunRequest(goal="What is Intel?", adversarial_config={"force_tavily_fail": True})
    res_fail = await baseline.run(req_fail)
    assert res_fail.success is False
    assert "failed" in res_fail.answer.lower()


def test_markdown_report_formatting():
    """Verify Markdown report generation."""
    eval_data = {
        "timestamp": "2026-08-23T01:00:00Z",
        "agent_summary": {
            "total_test_cases": 8,
            "passed_test_cases": 8,
            "pass_rate": 1.0,
            "average_task_completion": 0.95,
            "average_groundedness": 0.92,
            "average_hallucination_rate": 0.08,
            "recovery_rate": 1.0,
            "consistency_score": 0.96,
            "average_latency_seconds": 2.45,
            "average_tool_calls": 3.8,
            "average_iterations": 2.1,
            "category_breakdown": {
                "normal": {"total": 2, "passed": 2, "pass_rate": 1.0, "average_completion": 0.95, "average_groundedness": 0.92, "average_latency_seconds": 1.8},
            },
        },
        "baseline_summary": {
            "total_test_cases": 8,
            "passed_test_cases": 5,
            "pass_rate": 0.625,
            "average_task_completion": 0.55,
            "average_groundedness": 0.60,
            "average_hallucination_rate": 0.40,
            "average_latency_seconds": 1.10,
            "average_tool_calls": 1.0,
            "average_iterations": 1.0,
        },
        "detailed_scenario_results": [
            {
                "test_id": "TC-01",
                "test_name": "Single Company",
                "category": "normal",
                "passed": True,
                "task_completion_score": 0.95,
                "groundedness_score": 0.92,
                "confidence": "high",
                "latency_seconds": 1.8,
                "tool_calls_count": 3,
            }
        ],
    }

    md = generate_markdown_report(eval_data)
    assert "# Competitive Intelligence AI Agent — Task 6 Evaluation Report" in md
    assert "Pass Rate" in md
    assert "Groundedness" in md
    assert "Tool Failure Recovery Rate" in md
    assert "Human Evaluation Rubric" in md
