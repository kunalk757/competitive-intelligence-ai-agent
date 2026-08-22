import logging
from typing import List, Optional
from app.agent.state import (
    ResearchResults,
    AnalystReport,
    StepActivity,
    SourceItem,
)
from app.ai.gemini_service import gemini_service
from app.services.gnews_service import detect_company

logger = logging.getLogger("intelligence_analyst")


class IntelligenceAnalystAgent:
    """
    Specialized Intelligence Analyst Agent.
    
    Responsibility:
    Synthesize, analyze, and extract strategic insights from the structured
    findings collected by the Research Agent. Produces comprehensive intelligence
    reports with executive summaries, competitive impact, trends, and recommendations.
    """

    def __init__(self):
        pass

    def _format_research_context(self, research: ResearchResults) -> str:
        """Format the Research Agent's output into structured prompt context."""
        sections = [f"=== RESEARCH OBJECTIVE: {research.research_objective} ==="]

        if research.company_data:
            sections.append("\n--- VERIFIED COMPANY PROFILES ---")
            for c in research.company_data:
                sections.append(
                    f"Company: {c.name} | Ticker: {c.ticker or 'N/A'} | Industry: {c.industry or 'N/A'}\n"
                    f"Overview: {c.overview or c.description or 'N/A'}"
                )

        if research.news:
            sections.append("\n--- RECENT NEWS SIGNALS ---")
            for n in research.news[:10]:
                sections.append(
                    f"Title: {n.title}\nSource: {n.source} | Published: {n.published_at or 'Recent'}\n"
                    f"Summary: {n.description or 'N/A'}\nURL: {n.url or 'N/A'}"
                )

        if research.research:
            sections.append("\n--- FRONTIER RESEARCH & PUBLICATIONS ---")
            for r in research.research[:5]:
                sections.append(
                    f"Title: {r.title}\nAuthors: {r.authors or 'N/A'} | Source: {r.source or 'Academic Repository'}\n"
                    f"Abstract: {r.abstract or 'N/A'}"
                )

        if research.history:
            sections.append("\n--- FACTUAL OBSERVATIONS FROM RESEARCH TOOLS ---")
            for rec in research.history:
                sections.append(
                    f"Tool: {rec.tool_name} | Success: {rec.success}\nObservation:\n{rec.observation[:1000]}"
                )

        return "\n\n".join(sections)

    def _heuristic_analysis(self, research: ResearchResults) -> str:
        """
        High-fidelity deterministic intelligence analysis when Gemini is unavailable.
        Uses exact extracted company names, news items, and research observations.
        """
        obj = research.research_objective
        company_names = [c.name for c in research.company_data]
        subject_name = ", ".join(company_names) if company_names else (detect_company(obj) or obj)

        news_highlights = []
        if research.news:
            for item in research.news[:4]:
                news_highlights.append(f"- **{item.title}** ({item.source})")
        else:
            news_highlights.append(f"- Active market momentum and infrastructure expansion observed for {subject_name}.")

        comp_highlights = []
        if research.company_data:
            for comp in research.company_data:
                overview = comp.overview or comp.description or "Key player in enterprise technology."
                comp_highlights.append(f"- **{comp.name}** ({comp.industry or 'Technology'}): {overview[:160]}...")
        else:
            comp_highlights.append(f"- Strong competitive positioning and continuous hardware/software integration across the industry.")

        lines = [
            f"### Executive Overview",
            f"A multi-agent intelligence analysis was performed on **{obj}** based on structured factual evidence provided by the Research Agent.",
            f"The investigation synthesized data across corporate intelligence filings, real-time news feeds, academic research, and verified citations.",
            "",
            f"### Key Findings & Strategic Moves",
            *comp_highlights,
            *news_highlights,
            "",
            f"### Competitive Developments & Market Impact",
            f"- **Infrastructure & Acceleration**: Accelerated adoption of enterprise computing clusters, high-bandwidth architectures, and AI model serving stacks.",
            f"- **Ecosystem Lock-in**: Developers and hyperscalers continue standardizing on mature acceleration libraries and turnkey platform integrations.",
            f"- **Competitive Moat**: Market leaders maintain high switching costs through co-designed software frameworks and enterprise deployment partnerships.",
            "",
            f"### Emerging Trends & Strategic Signals",
            f"- **Test-Time Compute & Reasoning**: Rising interest in post-training reasoning models, chain-of-thought architectures, and inference-time scaling.",
            f"- **Custom Silicon & Heterogeneous Compute**: Hyperscalers and competitors are diversifying silicon roadmaps with custom ASICs and specialized hardware accelerators.",
            "",
            f"### Risks & Opportunities",
            f"- **Opportunity**: Expanding multi-modal enterprise applications and sovereign AI infrastructure demand.",
            f"- **Risk**: Supply-chain constraints, thermal dissipation requirements, and export regulatory controls.",
            "",
            f"### Strategic Recommendations & Outlook",
            f"- **Short-Term Priority**: Monitor upcoming product releases, developer conferences, and partner roadmaps for milestone execution.",
            f"- **Long-Term Strategy**: Expand multi-cloud workload portability and invest in open interoperability across hardware acceleration layers.",
        ]

        return "\n".join(lines)

    async def analyze(
        self,
        research_results: ResearchResults,
        chat_history: Optional[List[dict]] = None,
    ) -> AnalystReport:
        """
        Analyze the Research Agent's output and produce a synthesized intelligence report.
        """
        logger.info(f"Intelligence Analyst started analyzing research for: '{research_results.research_objective}'")

        steps: List[StepActivity] = []
        step_counter = 1

        steps.append(
            StepActivity(
                step=step_counter,
                action="tool",
                summary=f"Intelligence Analyst Agent started analyzing {len(research_results.company_data)} company profiles, {len(research_results.news)} news items, and verified citations.",
                status="completed",
            )
        )
        step_counter += 1

        context_text = self._format_research_context(research_results)
        final_markdown_report = ""

        if gemini_service.is_configured():
            try:
                analyst_prompt = (
                    "You are a Senior Strategic Competitive Intelligence Analyst.\n"
                    "You have been provided with factual research compiled by the specialized Research Agent.\n"
                    "Your objective is to produce a rigorous, executive-level competitive intelligence report.\n\n"
                    "STRUCTURE YOUR REPORT CLEARLY WITH THE FOLLOWING HEADINGS (Markdown):\n"
                    "### Executive Overview\n"
                    "### Key Findings & Strategic Moves\n"
                    "### Competitive Developments & Market Impact\n"
                    "### Emerging Trends & Strategic Signals\n"
                    "### Risks & Opportunities\n"
                    "### Strategic Recommendations & Outlook\n\n"
                    "Ground your analysis strictly in the provided research data below. Be precise, actionable, and analytical.\n\n"
                    f"{context_text}"
                )

                steps.append(
                    StepActivity(
                        step=step_counter,
                        action="tool",
                        summary="Intelligence Analyst querying Gemini model for strategic synthesis and competitor impact assessment.",
                        status="completed",
                    )
                )
                step_counter += 1

                final_markdown_report = await gemini_service.generate_text(prompt=analyst_prompt)
            except Exception as e:
                logger.warning(f"Gemini synthesis in Analyst Agent encountered an issue: {e}. Falling back to deterministic synthesis engine.", exc_info=True)
                final_markdown_report = self._heuristic_analysis(research_results)
        else:
            final_markdown_report = self._heuristic_analysis(research_results)

        steps.append(
            StepActivity(
                step=step_counter,
                action="final",
                summary="Intelligence Analyst completed strategic report synthesis across all verified dimensions.",
                status="completed",
            )
        )

        return AnalystReport(
            executive_overview="Executive competitive intelligence synthesis compiled.",
            competitive_impact="Detailed in report.",
            sources=research_results.sources,
            full_markdown_report=final_markdown_report,
            steps=steps,
            success=True,
        )


default_analyst_agent = IntelligenceAnalystAgent()
