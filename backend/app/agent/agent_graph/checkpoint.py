"""
LangGraph Checkpointing Configuration.

Maintains state persistence across graph execution stages.
Uses an in-memory MemorySaver checkpointer that can be seamlessly
swapped for persistent storage (e.g. Supabase, Postgres) in the future.
"""

from typing import Any, Dict
from langgraph.checkpoint.memory import MemorySaver

# Singleton MemorySaver instance for the application lifecycle
_global_checkpointer = MemorySaver()


def get_checkpointer() -> MemorySaver:
    """Returns the configured LangGraph checkpointer instance."""
    return _global_checkpointer


def get_graph_config(session_id: str, thread_id: str = "main") -> Dict[str, Any]:
    """Generates the runtime configuration dictionary required by LangGraph."""
    return {
        "configurable": {
            "thread_id": f"{session_id}:{thread_id}",
            "checkpoint_ns": "competitive_intelligence",
        }
    }
