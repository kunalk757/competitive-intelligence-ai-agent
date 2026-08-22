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


class CompanyCardData(BaseModel):
    """Structured model for company profiles retrieved during research."""
    id: Optional[str] = None
    name: str
    ticker: Optional[str] = None
    industry: Optional[str] = None
    overview: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    sources: List[Dict[str, str]] = Field(default_factory=list)


class ResearchPaper(BaseModel):
    """Structured model for academic and frontier research papers."""
    title: str
    authors: Optional[str] = None
    published_date: Optional[str] = None
    source: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None


class PatentItem(BaseModel):
    """Structured model for patent documents (when available)."""
    patent_number: str
    title: str
    assignee: Optional[str] = None
    filing_date: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None


class SourceItem(BaseModel):
    """Structured model for verified external citation sources."""
    title: str
    url: str
    snippet: Optional[str] = None


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
    extracted_companies: List[CompanyCardData] = Field(default_factory=list)
    extracted_research: List[ResearchPaper] = Field(default_factory=list)
    extracted_patents: List[PatentItem] = Field(default_factory=list)
    extracted_sources: List[SourceItem] = Field(default_factory=list)


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
    collected_companies: List[CompanyCardData] = Field(default_factory=list)
    collected_research: List[ResearchPaper] = Field(default_factory=list)
    collected_patents: List[PatentItem] = Field(default_factory=list)
    collected_sources: List[SourceItem] = Field(default_factory=list)
    final_answer: Optional[str] = None
    error: Optional[str] = None


class ResearchResults(BaseModel):
    """Structured output returned by the specialized Research Agent."""
    research_objective: str
    company_data: List[CompanyCardData] = Field(default_factory=list)
    news: List[NewsArticle] = Field(default_factory=list)
    research: List[ResearchPaper] = Field(default_factory=list)
    patents: List[PatentItem] = Field(default_factory=list)
    sources: List[SourceItem] = Field(default_factory=list)
    summary: str = ""
    tools_used: List[str] = Field(default_factory=list)
    steps: List[StepActivity] = Field(default_factory=list)
    history: List[ToolExecutionRecord] = Field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


class AnalystReport(BaseModel):
    """Structured intelligence report returned by the specialized Intelligence Analyst Agent."""
    executive_overview: str = ""
    key_findings: List[str] = Field(default_factory=list)
    competitive_impact: str = ""
    trends: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    sources: List[SourceItem] = Field(default_factory=list)
    full_markdown_report: str = ""
    steps: List[StepActivity] = Field(default_factory=list)
    success: bool = True
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
    max_tool_calls: Optional[int] = Field(
        default=8,
        ge=1,
        le=20,
        description="Maximum tool calls allowed across the investigation graph.",
    )
    chat_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Optional prior conversation turns for contextual research follow-ups.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Unique session/conversation ID for stateful memory management.",
    )
    adversarial_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional test-mode configuration for simulating tool failures or conflicting evidence.",
    )


class AgentRunResponse(BaseModel):
    """Response model returning the agent's completed execution and findings."""
    success: bool
    answer: str
    steps: List[StepActivity]
    tools_used: List[str]
    iterations: int
    session_id: Optional[str] = None
    # Backward compatible field aliases
    news_results: List[NewsArticle] = Field(default_factory=list)
    # Multi-source structured results
    companies: List[CompanyCardData] = Field(default_factory=list)
    news: List[NewsArticle] = Field(default_factory=list)
    research: List[ResearchPaper] = Field(default_factory=list)
    patents: List[PatentItem] = Field(default_factory=list)
    sources: List[SourceItem] = Field(default_factory=list)
    confidence: Optional[str] = "high"
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    conflicting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None



