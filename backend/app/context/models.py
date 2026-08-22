"""
Pydantic data models for session memory, conversation turns, and relevant context.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EntityState(BaseModel):
    """Tracks active entities and focal topics identified within a conversation."""
    companies: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    comparison_targets: List[str] = Field(default_factory=list)
    active_objective: Optional[str] = None


class ConversationTurn(BaseModel):
    """Record of a single conversational turn (user query and AI response)."""
    turn_id: str
    user_query: str
    assistant_response: str
    entities: EntityState = Field(default_factory=EntityState)
    key_findings: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SessionContext(BaseModel):
    """Complete context of an ongoing research session."""
    session_id: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    turns: List[ConversationTurn] = Field(default_factory=list)
    current_entities: EntityState = Field(default_factory=EntityState)
    summary: Optional[str] = None


class RelevantContext(BaseModel):
    """Filtered, query-specific context extracted from session memory."""
    session_id: str
    original_query: str
    contextual_query: str
    active_companies: List[str] = Field(default_factory=list)
    active_topics: List[str] = Field(default_factory=list)
    active_objective: Optional[str] = None
    comparison_targets: List[str] = Field(default_factory=list)
    relevant_prior_findings: List[str] = Field(default_factory=list)
    recent_dialogue_summary: Optional[str] = None
    has_context: bool = False
    context_notes: List[str] = Field(default_factory=list)
