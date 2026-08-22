from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class NewsArticle(BaseModel):
    """Structured model for news results retrieved by intelligence tools."""
    id: Optional[str] = None
    title: str
    source: str
    published_at: Optional[str] = None
    time: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = "News"
    company_tag: Optional[str] = None


class StepActivity(BaseModel):
    """Safe high-level summary of an action taken in an agent step."""
    step: int
    action: Literal["tool", "final", "error"]
    tool: Optional[str] = None
    summary: str
    status: Literal["running", "completed", "failed"] = "completed"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ToolExecutionRecord(BaseModel):
    """Record of a tool call and its observation."""
    step: int
    tool_name: str
    tool_input: Dict[str, Any]
    observation: str
    success: bool = True
    error: Optional[str] = None
    extracted_news: List[NewsArticle] = Field(default_factory=list)


class AgentDecision(BaseModel):
    """Structured decision returned by Gemini in the ReAct loop."""
    action: Literal["tool", "final"]
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    answer: Optional[str] = None
    thought_summary: Optional[str] = None  # High-level rationale (safe for activity logs)


class AgentState(BaseModel):
    """Tracks state throughout the ReAct agent execution lifecycle."""
    goal: str
    max_iterations: int = 5
    current_iteration: int = 0
    is_completed: bool = False
    tools_used: List[str] = Field(default_factory=list)
    history: List[ToolExecutionRecord] = Field(default_factory=list)
    steps: List[StepActivity] = Field(default_factory=list)
    collected_news: List[NewsArticle] = Field(default_factory=list)
    final_answer: Optional[str] = None
    error: Optional[str] = None


class AgentRunRequest(BaseModel):
    """Request model for invoking the agent."""
    goal: str = Field(
        ...,
        description="The investigation objective or competitor analysis goal.",
        examples=["Analyze the competitive landscape for AI chips."],
    )
    max_iterations: Optional[int] = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum reasoning iterations allowed before forcing synthesis.",
    )


class AgentRunResponse(BaseModel):
    """Response model returning the agent's completed execution and findings."""
    success: bool
    answer: str
    steps: List[StepActivity]
    tools_used: List[str]
    iterations: int
    news_results: List[NewsArticle] = Field(default_factory=list)
    error: Optional[str] = None
