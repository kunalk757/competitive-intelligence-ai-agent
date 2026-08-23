"""
Automated Root-Cause Diagnostic Engine for Task 7.
Classifies failure modes, determines error severity, triggers circuit breakers,
and prescribes deterministic recovery actions.
"""

from typing import Any, Dict, Optional
import re
from app.observability.schema import RootCauseDiagnosis


class RootCauseDiagnosticEngine:
    """
    Deterministic rule-based diagnostic engine for identifying root causes
    of tool, node, or network failures in multi-agent workflows.
    """

    @staticmethod
    def diagnose_failure(
        tool_name: str,
        error_message: str,
        attempt: int = 1,
        consecutive_failures: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ) -> RootCauseDiagnosis:
        """
        Analyze the failure signature and generate a structured diagnosis.
        """
        err_lower = (error_message or "").lower()
        details_dict = details or {}

        # 1. Service Unavailable / Server Outage (HTTP 503 / 502 / 504 / Connection refused)
        if "503" in err_lower or "service unavailable" in err_lower or "connection refused" in err_lower or "502" in err_lower or "timeout" in err_lower:
            error_category = "SERVICE_UNAVAILABLE"
            diagnosis = f"primary_{tool_name}_unavailable"
            recovery_action = "fallback_to_alternative_source"
            circuit_breaker = consecutive_failures >= 2

        # 2. Rate Limiting (HTTP 429)
        elif "429" in err_lower or "rate limit" in err_lower or "too many requests" in err_lower or "quota" in err_lower:
            error_category = "RATE_LIMIT_EXCEEDED"
            diagnosis = f"primary_{tool_name}_rate_limited"
            recovery_action = "fallback_to_alternative_source_and_backoff"
            circuit_breaker = consecutive_failures >= 2

        # 3. Authentication / Authorization (HTTP 401 / 403)
        elif "401" in err_lower or "403" in err_lower or "unauthorized" in err_lower or "api key" in err_lower or "forbidden" in err_lower:
            error_category = "AUTHENTICATION_ERROR"
            diagnosis = f"{tool_name}_credentials_invalid_or_forbidden"
            recovery_action = "fallback_to_local_cache_or_mock"
            circuit_breaker = True

        # 4. Resource Not Found (HTTP 404)
        elif "404" in err_lower or "not found" in err_lower:
            error_category = "RESOURCE_NOT_FOUND"
            diagnosis = f"{tool_name}_endpoint_or_entity_not_found"
            recovery_action = "broaden_search_query_or_skip"
            circuit_breaker = False

        # 5. Circuit Breaker / Repeated Failures
        elif "circuit breaker" in err_lower or consecutive_failures >= 3:
            error_category = "CIRCUIT_BREAKER_TRIGGERED"
            diagnosis = f"repeated_failure_circuit_breaker_for_{tool_name}"
            recovery_action = "mark_tool_permanently_unavailable_and_replan"
            circuit_breaker = True

        # 6. Unregistered Tool
        elif "not registered" in err_lower:
            error_category = "UNREGISTERED_TOOL"
            diagnosis = f"tool_{tool_name}_unregistered"
            recovery_action = "route_to_registered_tools"
            circuit_breaker = True

        # 7. Generic Network / Runtime Error
        else:
            error_category = "RUNTIME_EXCEPTION"
            diagnosis = f"{tool_name}_runtime_failure"
            recovery_action = "replan_subtasks_with_alternative_tool"
            circuit_breaker = consecutive_failures >= 3

        return RootCauseDiagnosis(
            diagnosis=diagnosis,
            affected_tool=tool_name,
            error_category=error_category,
            recovery_action=recovery_action,
            circuit_breaker_triggered=circuit_breaker,
            details={
                "attempt": attempt,
                "consecutive_failures": consecutive_failures,
                "raw_error_summary": error_message[:200] if error_message else "Unknown",
                **details_dict,
            },
        )
