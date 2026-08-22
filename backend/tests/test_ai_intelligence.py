import asyncio
import json
import logging
import sys
import os
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.agent import CompetitiveIntelligenceAgent
from app.agent.state import AgentRunRequest, AgentDecision
from app.agent.tool_registry import ToolRegistry, WebSearchTool, CompanyIntelligenceTool, NewsSearchTool, ResearchPaperTool
from app.agent.reasoning import ReasoningEngine

logging.basicConfig(level=logging.INFO)

async def test_all_ai_intelligence_query_flows():
    registry = ToolRegistry()
    mock_reasoning = AsyncMock(spec=ReasoningEngine)

    # 1. Query: "NVIDIA latest AI developments"
    print("\n==================================================")
    print("TEST 1: 'NVIDIA latest AI developments'")
    print("==================================================")
    mock_reasoning.decide_next_step.side_effect = [
        AgentDecision(
            action="tool",
            tool_name="search_company_intelligence",
            tool_input={"company_name": "NVIDIA"},
            thought_summary="Querying NVIDIA verified company intelligence and product focus.",
        ),
        AgentDecision(
            action="final",
            answer="### Executive Summary\nNVIDIA continues to lead enterprise AI hardware infrastructure with Blackwell architectures.\n\n### Key Findings\n- GB200 NVL72 rack-scale systems.\n- CUDA-X software ecosystem dominance.\n\n### Competitive Impact\nMaintains high barrier to entry against traditional x86 and custom ASICs.",
            thought_summary="Synthesizing NVIDIA intelligence report.",
        ),
    ]

    agent = CompetitiveIntelligenceAgent(tool_registry=registry, reasoning=mock_reasoning)
    resp1 = await agent.run(AgentRunRequest(goal="NVIDIA latest AI developments", max_iterations=4))
    print(f"Success: {resp1.success}")
    print(f"Tools Used: {resp1.tools_used}")
    print(f"Companies Extracted: {len(resp1.companies)} -> {[c.name for c in resp1.companies]}")
    print(f"News Extracted: {len(resp1.news)}")
    print(f"Sources Extracted: {len(resp1.sources)}")
    assert resp1.success is True
    assert "search_company_intelligence" in resp1.tools_used
    assert len(resp1.companies) >= 1
    assert resp1.companies[0].name == "NVIDIA"
    assert resp1.companies[0].logo_url is not None
    print(">>> Test 1 Passed!")

    # 2. Query: "Latest news about AMD"
    print("\n==================================================")
    print("TEST 2: 'Latest news about AMD'")
    print("==================================================")
    mock_reasoning.decide_next_step.side_effect = [
        AgentDecision(
            action="tool",
            tool_name="search_news",
            tool_input={"query": "AMD"},
            thought_summary="Fetching breaking news for AMD.",
        ),
        AgentDecision(
            action="final",
            answer="### Executive Summary\nAMD accelerates Instinct MI300X and MI325X adoption across major hyperscalers.\n\n### Key Findings\n- Major cloud partnerships expanding.\n- ROCm open-source stack maturation.",
            thought_summary="Finalizing AMD news report.",
        ),
    ]

    resp2 = await agent.run(AgentRunRequest(goal="Latest news about AMD", max_iterations=4))
    print(f"Success: {resp2.success}")
    print(f"Tools Used: {resp2.tools_used}")
    assert resp2.success is True
    assert "search_news" in resp2.tools_used
    print(">>> Test 2 Passed!")

    # 3. Query: "Research papers about large language models"
    print("\n==================================================")
    print("TEST 3: 'Research papers about large language models'")
    print("==================================================")
    mock_reasoning.decide_next_step.side_effect = [
        AgentDecision(
            action="tool",
            tool_name="search_research_papers",
            tool_input={"query": "large language models reasoning"},
            thought_summary="Searching academic papers on arXiv and open repositories.",
        ),
        AgentDecision(
            action="final",
            answer="### Executive Summary\nRecent frontier research emphasizes test-time compute scaling and chain-of-thought verification.\n\n### Key Findings\n- Post-training reinforcement learning breakthroughs.\n- Multimodal attention mechanisms.",
            thought_summary="Synthesizing academic research overview.",
        ),
    ]

    resp3 = await agent.run(AgentRunRequest(goal="Research papers about large language models", max_iterations=4))
    print(f"Success: {resp3.success}")
    print(f"Tools Used: {resp3.tools_used}")
    assert resp3.success is True
    assert "search_research_papers" in resp3.tools_used
    print(">>> Test 3 Passed!")

    # 4. Query: "Compare NVIDIA and AMD in AI chips"
    print("\n==================================================")
    print("TEST 4: 'Compare NVIDIA and AMD in AI chips'")
    print("==================================================")
    mock_reasoning.decide_next_step.side_effect = [
        AgentDecision(
            action="tool",
            tool_name="search_company_intelligence",
            tool_input={"company_name": "NVIDIA"},
            thought_summary="Gathering NVIDIA AI chip profile.",
        ),
        AgentDecision(
            action="tool",
            tool_name="search_company_intelligence",
            tool_input={"company_name": "AMD"},
            thought_summary="Gathering AMD AI accelerator profile.",
        ),
        AgentDecision(
            action="final",
            answer="### Executive Overview\nNVIDIA leads in software moat with CUDA, while AMD offers competitive raw compute and memory capacity.\n\n### Comparison\n- Architecture: Blackwell vs CDNA 3\n- Memory: HBM3e vs High-capacity HBM3\n\n### Strategic Outlook\nBoth vendors are driving datacenter infrastructure expansion.",
            thought_summary="Compiling comparative intelligence synthesis.",
        ),
    ]

    resp4 = await agent.run(AgentRunRequest(goal="Compare NVIDIA and AMD in AI chips", max_iterations=5))
    print(f"Success: {resp4.success}")
    print(f"Tools Used: {resp4.tools_used}")
    print(f"Companies Extracted: {len(resp4.companies)} -> {[c.name for c in resp4.companies]}")
    assert resp4.success is True
    assert len(resp4.companies) == 2
    comp_names = [c.name for c in resp4.companies]
    assert "NVIDIA" in comp_names
    assert "AMD" in comp_names
    print(">>> Test 4 Passed!")
    print("\n=== ALL 4 AI INTELLIGENCE TEST QUERIES PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(test_all_ai_intelligence_query_flows())
