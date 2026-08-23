"""
Investigation Tracer Singleton and Context Manager (Task 7).
Captures end-to-end multi-agent execution spans, handles timing,
attaches diagnostic events, and persists traces safely.
"""

import time
import uuid
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from contextlib import contextmanager

from app.observability.schema import (
    InvestigationTrace,
    TraceSpan,
    RootCauseDiagnosis,
    ResourceMetrics,
)
from app.observability.diagnostics import RootCauseDiagnosticEngine
from app.observability.storage import default_trace_storage, TraceStorage

logger = logging.getLogger("tracer")


class InvestigationTracer:
    """
    Active tracer for managing the lifecycle of an investigation trace.
    """

    def __init__(self, storage: Optional[TraceStorage] = None):
        self.storage = storage or default_trace_storage
        self._active_traces: Dict[str, InvestigationTrace] = {}
        self._perf_starts: Dict[str, float] = {}

    def start_trace(
        self,
        session_id: str,
        user_goal: str,
        agent_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InvestigationTrace:
        """Initialize and register a new trace for an agent run."""
        trace = InvestigationTrace(
            trace_id=f"tr-{uuid.uuid4().hex[:12]}",
            agent_run_id=agent_run_id or f"run-{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            user_goal=user_goal,
            start_time=datetime.now(timezone.utc).isoformat(),
            status="running",
            tags=tags or ["competitive-intelligence", "langgraph"],
            metadata=metadata or {},
        )
        self._active_traces[trace.trace_id] = trace
        self._perf_starts[trace.trace_id] = time.perf_counter()
        return trace

    def get_trace(self, trace_id: str) -> Optional[InvestigationTrace]:
        """Get an in-memory active trace or retrieve from storage."""
        if trace_id in self._active_traces:
            return self._active_traces[trace_id]
        return self.storage.get_trace(trace_id)

    def record_node_span(
        self,
        trace_id: str,
        node_name: str,
        duration_ms: float,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[TraceSpan]:
        """Record the execution span of a LangGraph workflow node."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            return None

        span = TraceSpan(
            span_type="node_execution",
            name=f"node:{node_name}",
            node_name=node_name,
            duration_ms=round(duration_ms, 2),
            status="success" if status == "success" else "failed",
            metadata=metadata or {},
            end_time=datetime.now(timezone.utc).isoformat(),
        )
        trace.spans.append(span)
        return span

    def record_tool_span(
        self,
        trace_id: str,
        tool_name: str,
        duration_ms: float,
        success: bool,
        attempt: int = 1,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        fallback_used: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[TraceSpan]:
        """Record the execution span of an external research tool."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            return None

        span = TraceSpan(
            span_type="tool_execution",
            name=f"tool:{tool_name}",
            tool_name=tool_name,
            duration_ms=round(duration_ms, 2),
            status="success" if success else ("recovered" if fallback_used else "failed"),
            attempt=attempt,
            error_type=error_type,
            error_message=error_message,
            fallback_used=fallback_used,
            metadata=metadata or {},
            end_time=datetime.now(timezone.utc).isoformat(),
        )
        trace.spans.append(span)

        # Update trace resource metrics
        trace.resource_metrics.total_tool_calls += 1
        if success:
            trace.resource_metrics.successful_tool_calls += 1
        else:
            trace.resource_metrics.failed_tool_calls += 1
            if fallback_used:
                trace.resource_metrics.recovered_tool_calls += 1

        return span

    def record_diagnostic_event(
        self,
        trace_id: str,
        tool_name: str,
        error_message: str,
        attempt: int = 1,
        consecutive_failures: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[RootCauseDiagnosis]:
        """Diagnose a failure mode, attach root-cause event and span to the trace."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            return None

        diagnosis = RootCauseDiagnosticEngine.diagnose_failure(
            tool_name=tool_name,
            error_message=error_message,
            attempt=attempt,
            consecutive_failures=consecutive_failures,
            details=details,
        )

        trace.root_cause_diagnoses.append(diagnosis)

        # Also log a diagnostic span
        diag_span = TraceSpan(
            span_type="diagnostic_event",
            name=f"diagnostic:{diagnosis.diagnosis}",
            node_name="replan_node",
            tool_name=tool_name,
            duration_ms=1.0,
            status="completed",
            error_type=diagnosis.error_category,
            error_message=error_message[:150] if error_message else None,
            fallback_used=True,
            metadata=diagnosis.model_dump(),
            end_time=datetime.now(timezone.utc).isoformat(),
        )
        trace.spans.append(diag_span)

        return diagnosis

    def finalize_trace(
        self,
        trace_id: str,
        status: str = "completed",
        confidence: str = "high",
        iterations: int = 1,
        tokens: Optional[Dict[str, int]] = None,
    ) -> Optional[InvestigationTrace]:
        """Finalize, compute total latency, save to disk, and return."""
        trace = self._active_traces.pop(trace_id, None)
        if not trace:
            return self.storage.get_trace(trace_id)

        perf_start = self._perf_starts.pop(trace_id, None)
        if perf_start:
            total_duration_ms = (time.perf_counter() - perf_start) * 1000.0
            trace.total_latency_ms = round(total_duration_ms, 2)

        trace.end_time = datetime.now(timezone.utc).isoformat()
        trace.status = status
        trace.confidence = confidence
        trace.iterations = iterations
        trace.resource_metrics.iterations = iterations

        if tokens:
            trace.resource_metrics.input_tokens = tokens.get("input_tokens")
            trace.resource_metrics.output_tokens = tokens.get("output_tokens")
            trace.resource_metrics.total_tokens = tokens.get("total_tokens")

        # Save trace to persistent storage
        self.storage.save_trace(trace)
        return trace


# Global singleton tracer
default_tracer = InvestigationTracer()
