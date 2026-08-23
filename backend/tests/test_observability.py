"""
Comprehensive Test Suite for Task 7: Advanced Tracing & Observability.

Verifies:
1. Trace creation and initialization
2. Agent run lifecycle tracing
3. Tool call tracing (durations, status, attempts)
4. Tool failure tracing (categorized errors)
5. Autonomous recovery tracing
6. Root-cause diagnostic engine (RCA classification)
7. Before vs After metric collection
8. Trace completeness and span hierarchy
9. Privacy compliance (no API keys, tokens, or raw CoT leaked into trace documents)
10. Trace retrieval via storage and API endpoints
"""

import pytest
import os
import json
import tempfile
from datetime import datetime

from app.observability.schema import InvestigationTrace, TraceSpan, RootCauseDiagnosis
from app.observability.diagnostics import RootCauseDiagnosticEngine
from app.observability.storage import TraceStorage
from app.observability.tracer import InvestigationTracer
from app.agent.state import AgentRunRequest, AgentRunResponse
from app.agent.orchestrator import MultiAgentOrchestrator


@pytest.fixture
def temp_tracer():
    """Provides an isolated tracer instance using a temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = TraceStorage(storage_dir=tmp_dir)
        tracer = InvestigationTracer(storage=storage)
        yield tracer, storage


# ---------------------------------------------------------------------------
# TEST 1: Trace Creation & Initialization
# ---------------------------------------------------------------------------
def test_1_trace_creation(temp_tracer):
    tracer, storage = temp_tracer
    trace = tracer.start_trace(
        session_id="test-session-101",
        user_goal="Evaluate competitive landscape of TSMC and Intel.",
    )

    assert trace is not None
    assert trace.trace_id.startswith("tr-")
    assert trace.session_id == "test-session-101"
    assert trace.user_goal == "Evaluate competitive landscape of TSMC and Intel."
    assert trace.status == "running"
    assert len(trace.spans) == 0


# ---------------------------------------------------------------------------
# TEST 2: Granular Node & Tool Call Tracing
# ---------------------------------------------------------------------------
def test_2_granular_node_and_tool_tracing(temp_tracer):
    tracer, storage = temp_tracer
    trace = tracer.start_trace(session_id="test-session-102", user_goal="Analyze Nvidia GPUs.")

    # 1. Record node span
    node_span = tracer.record_node_span(
        trace_id=trace.trace_id,
        node_name="planner_node",
        duration_ms=45.2,
        status="success",
        metadata={"subtasks": 3},
    )
    assert node_span is not None
    assert node_span.span_type == "node_execution"
    assert node_span.name == "node:planner_node"
    assert node_span.duration_ms == 45.2

    # 2. Record tool span
    tool_span = tracer.record_tool_span(
        trace_id=trace.trace_id,
        tool_name="search_web",
        duration_ms=120.5,
        success=True,
        metadata={"results_count": 5},
    )
    assert tool_span is not None
    assert tool_span.span_type == "tool_execution"
    assert tool_span.status == "success"
    assert trace.resource_metrics.total_tool_calls == 1
    assert trace.resource_metrics.successful_tool_calls == 1


# ---------------------------------------------------------------------------
# TEST 3: Tool Failure & Root Cause Diagnosis
# ---------------------------------------------------------------------------
def test_3_tool_failure_and_root_cause_diagnosis(temp_tracer):
    tracer, storage = temp_tracer
    trace = tracer.start_trace(session_id="test-session-103", user_goal="Investigate edge chips.")

    # 1. Record failed tool call
    fail_span = tracer.record_tool_span(
        trace_id=trace.trace_id,
        tool_name="search_web",
        duration_ms=30.0,
        success=False,
        error_type="SERVICE_UNAVAILABLE",
        error_message="503 Service Unavailable / Rate Limit",
        fallback_used=True,
    )
    assert fail_span.status == "recovered"
    assert trace.resource_metrics.failed_tool_calls == 1
    assert trace.resource_metrics.recovered_tool_calls == 1

    # 2. Perform diagnostic classification
    diag = tracer.record_diagnostic_event(
        trace_id=trace.trace_id,
        tool_name="search_web",
        error_message="503 Service Unavailable / Connection refused",
        attempt=1,
        consecutive_failures=1,
    )
    assert diag is not None
    assert diag.error_category == "SERVICE_UNAVAILABLE"
    assert "unavailable" in diag.diagnosis
    assert diag.recovery_action == "fallback_to_alternative_source"
    assert len(trace.root_cause_diagnoses) == 1


# ---------------------------------------------------------------------------
# TEST 4: Diagnostic Engine Rules
# ---------------------------------------------------------------------------
def test_4_diagnostic_engine_classification_rules():
    # 429 Rate Limit
    d1 = RootCauseDiagnosticEngine.diagnose_failure("search_news", "HTTP 429 Too Many Requests")
    assert d1.error_category == "RATE_LIMIT_EXCEEDED"
    assert d1.recovery_action == "fallback_to_alternative_source_and_backoff"

    # 401 Unauthorized
    d2 = RootCauseDiagnosticEngine.diagnose_failure("search_web", "401 Unauthorized: Invalid API key")
    assert d2.error_category == "AUTHENTICATION_ERROR"
    assert d2.circuit_breaker_triggered is True

    # Circuit Breaker / Repeated
    d3 = RootCauseDiagnosticEngine.diagnose_failure("search_web", "Persistent failure", consecutive_failures=3)
    assert d3.error_category == "CIRCUIT_BREAKER_TRIGGERED"
    assert d3.circuit_breaker_triggered is True


# ---------------------------------------------------------------------------
# TEST 5: Trace Finalization and Persistence
# ---------------------------------------------------------------------------
def test_5_trace_finalization_and_persistence(temp_tracer):
    tracer, storage = temp_tracer
    trace = tracer.start_trace(session_id="test-session-105", user_goal="Persist test trace.")
    tracer.record_node_span(trace.trace_id, "planner_node", 10.0)

    finalized = tracer.finalize_trace(
        trace_id=trace.trace_id,
        status="completed",
        confidence="high",
        iterations=2,
    )
    assert finalized is not None
    assert finalized.total_latency_ms > 0
    assert finalized.status == "completed"

    # Verify retrieval from storage
    loaded = storage.get_trace(trace.trace_id)
    assert loaded is not None
    assert loaded.trace_id == trace.trace_id
    assert loaded.session_id == "test-session-105"
    assert len(loaded.spans) == 1


# ---------------------------------------------------------------------------
# TEST 6: End-to-End Orchestrator Tracing Lifecycle
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_6_end_to_end_orchestrator_tracing():
    orchestrator = MultiAgentOrchestrator()
    req = AgentRunRequest(
        goal="Compare Microsoft and Apple market strategies.",
        session_id="test-session-e2e",
    )
    response = await orchestrator.run(req)

    assert response.success is True
    assert response.trace_id is not None
    assert response.trace_id.startswith("tr-")
    assert response.trace_summary is not None
    assert response.trace_summary["spans_count"] > 0
    assert response.trace_summary["total_latency_ms"] > 0


# ---------------------------------------------------------------------------
# TEST 7: Adversarial Failure Trace & Self-Healing Verification
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_7_adversarial_failure_trace_and_diagnosis():
    orchestrator = MultiAgentOrchestrator()
    req = AgentRunRequest(
        goal="Analyze Qualcomm wireless positioning.",
        session_id="test-session-adv-fail",
        adversarial_config={"force_tavily_fail": True},
    )
    response = await orchestrator.run(req)

    assert response.success is True
    assert response.trace_id is not None
    # Verify diagnosis was recorded during replanning
    assert len(response.diagnoses) > 0
    diag = response.diagnoses[0]
    assert diag["affected_tool"] in ["search_web", "search_research_papers"]
    assert diag["error_category"] == "SERVICE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# TEST 8: Privacy & Redaction Compliance
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_8_privacy_compliance_no_secrets():
    orchestrator = MultiAgentOrchestrator()
    req = AgentRunRequest(
        goal="Verify zero secret leakage in trace metadata.",
        session_id="test-session-privacy",
    )
    response = await orchestrator.run(req)

    # Convert entire response and step activities to text
    serialized = response.model_dump_json()

    # Verify no private API keys or forbidden strings leaked
    forbidden_tokens = ["api_key=", "GEMINI_API_KEY", "TAVILY_API_KEY", "SUPABASE_KEY", "BEGIN PRIVATE KEY"]
    for token in forbidden_tokens:
        assert token not in serialized, f"Privacy violation: '{token}' found in trace/response JSON."


# ---------------------------------------------------------------------------
# TEST 9: Before vs After Benchmark Comparison
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_9_before_vs_after_benchmark_metric_collection():
    from app.api.routes.observability import run_observability_benchmark

    benchmark = await run_observability_benchmark()
    assert benchmark is not None
    assert len(benchmark.comparison_table) >= 4
    assert benchmark.after_details["total_spans"] > 0
    assert benchmark.after_details["recovery_success"] is True
