"""
Persistent Storage and Retrieval for Investigation Traces (Task 7).
Saves structured traces to data/traces/ and allows query by session_id or trace_id.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from app.observability.schema import InvestigationTrace

logger = logging.getLogger("trace_storage")


class TraceStorage:
    """
    Manages local and persistent storage of investigation traces.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = storage_dir
        else:
            self.storage_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "data", "traces"
            )
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.storage_dir):
            try:
                os.makedirs(self.storage_dir, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create trace directory: {e}")

    def save_trace(self, trace: InvestigationTrace) -> str:
        """Save an InvestigationTrace document to disk as JSON."""
        self._ensure_dir()
        file_path = os.path.join(self.storage_dir, f"{trace.trace_id}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(trace.model_dump(), f, indent=2, ensure_ascii=False)
            return file_path
        except Exception as e:
            logger.error(f"Failed to save trace '{trace.trace_id}': {e}")
            return ""

    def get_trace(self, trace_id: str) -> Optional[InvestigationTrace]:
        """Retrieve a specific trace by trace_id."""
        clean_id = trace_id.replace(".json", "")
        file_path = os.path.join(self.storage_dir, f"{clean_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return InvestigationTrace(**data)
            except Exception as e:
                logger.error(f"Error reading trace '{trace_id}': {e}")
        return None

    def list_traces(self, limit: int = 50, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List summary info for recently stored traces."""
        self._ensure_dir()
        summaries: List[Dict[str, Any]] = []

        if not os.path.exists(self.storage_dir):
            return []

        files = sorted(
            [f for f in os.listdir(self.storage_dir) if f.endswith(".json")],
            key=lambda f: os.path.getmtime(os.path.join(self.storage_dir, f)),
            reverse=True,
        )

        for filename in files[:limit]:
            file_path = os.path.join(self.storage_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if session_id and data.get("session_id") != session_id:
                        continue
                    summaries.append({
                        "trace_id": data.get("trace_id"),
                        "agent_run_id": data.get("agent_run_id"),
                        "session_id": data.get("session_id"),
                        "user_goal": data.get("user_goal", "")[:80],
                        "status": data.get("status"),
                        "total_latency_ms": data.get("total_latency_ms", 0.0),
                        "start_time": data.get("start_time"),
                        "end_time": data.get("end_time"),
                        "tool_calls": len([s for s in data.get("spans", []) if s.get("span_type") == "tool_execution"]),
                        "diagnoses_count": len(data.get("root_cause_diagnoses", [])),
                        "confidence": data.get("confidence", "high"),
                    })
            except Exception as e:
                logger.warning(f"Error reading trace summary from '{filename}': {e}")

        return summaries


# Global default trace storage singleton
default_trace_storage = TraceStorage()
