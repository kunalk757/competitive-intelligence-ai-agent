from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import json
from app.agent.state import NewsArticle


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool action and return an observation string."""
        pass

    def extract_news(self, observation: str) -> List[NewsArticle]:
        """Optionally extract structured NewsArticle items from observation."""
        return []

    def to_schema(self) -> Dict[str, Any]:
        """Return the tool schema description for LLM prompting."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class SearchDemoTool(BaseTool):
    """
    Temporary development tool used exclusively to verify ReAct agent orchestration.
    NOTE: Returns structured mock demonstration signal for the query without claiming to be live search.
    """

    name = "search_demo"
    description = (
        "Temporary demonstration tool for verifying agent orchestration and reasoning. "
        "Accepts a search 'query' string and returns a structured demo response detailing "
        "market context and testing signals."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query or keyword phrase to test.",
            }
        },
        "required": ["query"],
    }

    async def execute(self, query: str, **kwargs) -> str:
        if not query or not query.strip():
            return "Error: query parameter cannot be empty."

        clean_query = query.strip()
        result = {
            "status": "success",
            "source": "search_demo (orchestration verification tool)",
            "query_received": clean_query,
            "verified_signals": [
                {
                    "title": f"Competitive overview for '{clean_query}'",
                    "summary": f"Demonstration market data captured for query: '{clean_query}'. Major competitors are investing heavily in custom silicon, micro-architectures, and high-bandwidth interconnects.",
                    "relevance": "High",
                },
                {
                    "title": f"Recent technological shifts in {clean_query}",
                    "summary": f"Key shifts noted in power efficiency, specialized tensor processing units, and open-source compiler toolchains related to {clean_query}.",
                    "relevance": "Medium",
                }
            ],
            "note": "Verified agent execution and tool connectivity successfully.",
        }
        return json.dumps(result, indent=2)

    def extract_news(self, observation: str) -> List[NewsArticle]:
        # SearchDemoTool is only for orchestration testing and does NOT return news articles
        return []


class ToolRegistry:
    """Registry managing available tools for the ReAct agent."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Register default initial verification tool
        self.register_tool(SearchDemoTool())

    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_tools_description(self) -> str:
        """Generate a formatted description of all available tools for LLM prompts."""
        descriptions = []
        for tool in self._tools.values():
            schema_json = json.dumps(tool.to_schema(), indent=2)
            descriptions.append(f"Tool Name: {tool.name}\nSchema: {schema_json}")
        return "\n\n".join(descriptions)


# Global default registry
default_tool_registry = ToolRegistry()
