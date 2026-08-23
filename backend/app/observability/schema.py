"""
Data models and schemas for Task 7 Advanced Tracing & Observability.
Conforms to OpenTelemetry / LangSmith event conventions while strictly redacting
private Chain-of-Thought, sensitive prompt texts, and API secrets.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class TraceSpan(BaseModel):
    """
    Individual granular execution span representing a node execution,
    tool call, evidence evaluation, or diagnostic event.
    """
    span_id: str = Field(default_factory=lambda: f"span-{uuid.uuid4().hex[:8]}")
    parent_span_id: Optional[str] = None
    span_type: Literal[
        "agent_run",
        "node_execution",
        "tool_execution",
        "diagnostic_event",
        "evaluation_event",
        "replanning_event",
    ]
    name: str
    node_name: Optional[str] = None
    tool_name: Optional[str] = None
    start_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    status: Literal["running", "success", "completed", "failed", "recovered"] = "running"
    attempt: int = 1
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    fallback_used: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RootCauseDiagnosis(BaseModel):
    """
    Structured failure diagnosis generated when errors or circuit breakers occur.
    """
    diagnosis: str
    affected_tool: str
    error_category: str
    recovery_action: str
    circuit_breaker_triggered: bool = False
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    details: Dict[str, Any] = Field(default_factory=dict)


class ResourceMetrics(BaseModel):
    """
    Execution and resource metrics for the investigation.
    """
    total_tool_calls: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    recovered_tool_calls: int = 0
    iterations: int = 1
    model_name: str = "gemini-2.0-flash / langgraph-orchestrator"
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class InvestigationTrace(BaseModel):
    """
    End-to-end trace representation for a complete agent investigation.
    """
    trace_id: str = Field(default_factory=lambda: f"tr-{uuid.uuid4().hex[:12]}")
    agent_run_id: str = Field(default_factory=lambda: f"run-{uuid.uuid4().hex[:8]}")
    session_id: str
    user_goal: str
    start_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    end_time: Optional[str] = None
    total_latency_ms: float = 0.0
    status: Literal["running", "completed", "failed", "recovered"] = "running"
    iterations: int = 1
    confidence: str = "high"
    spans: List[TraceSpan] = Field(default_factory=list)
    root_cause_diagnoses: List[RootCauseDiagnosis] = Field(default_factory=list)
    resource_metrics: ResourceMetrics = Field(default_factory=ResourceMetrics)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
