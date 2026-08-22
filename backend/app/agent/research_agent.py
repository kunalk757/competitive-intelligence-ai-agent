import logging
from typing import List, Optional
from app.agent.state import (
    ResearchResults,
    StepActivity,
    ToolExecutionRecord,
    CompanyCardData,
    NewsArticle,
    ResearchPaper,
    PatentItem,
    SourceItem,
)
from app.agent.tool_registry import ToolRegistry, default_tool_registry
from app.services.gnews_service import detect_company

logger = logging.getLogger("research_agent")


class ResearchAgent:
    """
    Specialized Research Agent.
    
    Responsibility:
    Collect factual multi-source intelligence (company profiles, news, research papers,
    patents, and verified web citations) required for an investigation objective.
    Reuses existing Tavily, GNews, Company, and ToolRegistry services.
    """

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry or default_tool_registry

    async def execute_research(
        self,
        objective: str,
        max_iterations: int = 5,
        chat_history: Optional[List[dict]] = None,
    ) -> ResearchResults:
        """
        Execute multi-source research pipeline for the given objective.
        """
        clean_objective = objective.strip()
        logger.info(f"Research Agent started investigation: '{clean_objective}'")

        steps: List[StepActivity] = []
        history: List[ToolExecutionRecord] = []
        tools_used: List[str] = []

        collected_companies: List[CompanyCardData] = []
        collected_news: List[NewsArticle] = []
        collected_research: List[ResearchPaper] = []
        collected_patents: List[PatentItem] = []
        collected_sources: List[SourceItem] = []

        step_counter = 1

        steps.append(
            StepActivity(
                step=step_counter,
                action="tool",
                summary=f"Research Agent initialized research on: '{clean_objective}'",
                status="completed",
            )
        )
        step_counter += 1

        # Detect recognized company entity
        company = detect_company(clean_objective)

        # Plan required research tools based on objective
        planned_tools = []

        if company:
            # Multi-entity query check (e.g. "Compare NVIDIA and AMD")
            tokens = clean_objective.upper().split()
            found_companies = []
            for known in ["NVIDIA", "AMD", "INTEL", "MICROSOFT", "GOOGLE", "APPLE", "AMAZON", "META", "OPENAI", "ANTHROPIC", "TESLA", "QUALCOMM", "TSMC", "BROADCOM"]:
                if known in tokens or known in clean_objective.upper():
                    found_companies.append(known)

            if len(found_companies) > 1:
                for c in found_companies:
                    planned_tools.append(("search_company_intelligence", {"company_name": c}, f"Gathering verified company profile and strategic intelligence for {c}"))
            else:
                planned_tools.append(("search_company_intelligence", {"company_name": company}, f"Gathering verified company profile and strategic intelligence for {company}"))

            planned_tools.append(("search_news", {"query": company}, f"Querying recent news articles and market signals for {company}"))
            planned_tools.append(("search_web", {"query": f"{clean_objective} strategic analysis"}, f"Searching verified web intelligence for '{clean_objective}'"))
            planned_tools.append(("search_research_papers", {"query": clean_objective}, f"Searching technical publications and papers on '{clean_objective}'"))
        else:
            planned_tools.append(("search_web", {"query": clean_objective}, f"Searching live web intelligence on '{clean_objective}'"))
            planned_tools.append(("search_news", {"query": clean_objective}, f"Querying recent news developments for '{clean_objective}'"))
            planned_tools.append(("search_research_papers", {"query": clean_objective}, f"Searching academic repositories and research on '{clean_objective}'"))

        # Limit to max_iterations tools
        planned_tools = planned_tools[:max_iterations]

        # Execute each planned research tool gracefully
        for tool_name, tool_input, step_summary in planned_tools:
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                logger.warning(f"Research Agent requested tool '{tool_name}' which is not registered.")
                continue

            if tool_name not in tools_used:
                tools_used.append(tool_name)

            tool_service_name = "Tavily" if tool_name in ["search_web", "search_research_papers"] else ("GNews" if tool_name == "search_news" else "Company Intelligence")
            
            steps.append(
                StepActivity(
                    step=step_counter,
                    action="tool",
                    tool=tool_name,
                    summary=f"Research Agent selected {tool_service_name} ({tool_name})",
                    status="completed",
                )
            )
            step_counter += 1

            try:
                observation = await tool.execute(**tool_input)
                
                # Extract structured multi-source entities
                extracted_news = tool.extract_news(observation)
                extracted_companies = tool.extract_companies(observation)
                extracted_research = tool.extract_research(observation)
                extracted_patents = tool.extract_patents(observation)
                extracted_sources = tool.extract_sources(observation)

                if extracted_news:
                    collected_news.extend(extracted_news)
                if extracted_companies:
                    collected_companies.extend(extracted_companies)
                if extracted_research:
                    collected_research.extend(extracted_research)
                if extracted_patents:
                    collected_patents.extend(extracted_patents)
                if extracted_sources:
                    collected_sources.extend(extracted_sources)

                history.append(
                    ToolExecutionRecord(
                        step=step_counter,
                        tool_name=tool_name,
                        tool_input=tool_input,
                        observation=observation,
                        success=True,
                        extracted_news=extracted_news,
                        extracted_companies=extracted_companies,
                        extracted_research=extracted_research,
                        extracted_patents=extracted_patents,
                        extracted_sources=extracted_sources,
                    )
                )

                steps.append(
                    StepActivity(
                        step=step_counter,
                        action="tool",
                        tool=tool_name,
                        summary=f"{tool_service_name} execution completed ({step_summary})",
                        status="completed",
                    )
                )
                step_counter += 1

            except Exception as tool_err:
                logger.warning(f"Error during {tool_name} execution: {tool_err}")
                history.append(
                    ToolExecutionRecord(
                        step=step_counter,
                        tool_name=tool_name,
                        tool_input=tool_input,
                        observation=f"Error: {str(tool_err)}",
                        success=False,
                        error=str(tool_err),
                    )
                )
                steps.append(
                    StepActivity(
                        step=step_counter,
                        action="error",
                        tool=tool_name,
                        summary=f"{tool_service_name} query encountered non-critical error: {str(tool_err)}. Continuing with available tools.",
                        status="failed",
                    )
                )
                step_counter += 1

        # Deduplicate results
        unique_companies: List[CompanyCardData] = []
        seen_comps = set()
        for c in collected_companies:
            norm = c.name.lower().strip()
            if norm not in seen_comps:
                seen_comps.add(norm)
                unique_companies.append(c)

        unique_news: List[NewsArticle] = []
        seen_news = set()
        for n in collected_news:
            key = n.url or n.title
            if key not in seen_news:
                seen_news.add(key)
                unique_news.append(n)

        unique_research: List[ResearchPaper] = []
        seen_res = set()
        for r in collected_research:
            key = r.url or r.title
            if key not in seen_res:
                seen_res.add(key)
                unique_research.append(r)

        unique_sources: List[SourceItem] = []
        seen_sources = set()
        for s in collected_sources:
            if s.url and s.url not in seen_sources:
                seen_sources.add(s.url)
                unique_sources.append(s)

        summary_msg = (
            f"Research Agent completed data collection: {len(unique_companies)} company profile(s), "
            f"{len(unique_news)} news article(s), {len(unique_research)} research paper(s), and "
            f"{len(unique_sources)} verified external source(s)."
        )

        steps.append(
            StepActivity(
                step=step_counter,
                action="final",
                summary=summary_msg,
                status="completed",
            )
        )

        logger.info(summary_msg)

        return ResearchResults(
            research_objective=clean_objective,
            company_data=unique_companies,
            news=unique_news,
            research=unique_research,
            patents=collected_patents,
            sources=unique_sources,
            summary=summary_msg,
            tools_used=tools_used,
            steps=steps,
            history=history,
            success=True,
        )


default_research_agent = ResearchAgent()
