"""
Context Manager for Competitive Intelligence.

Handles:
1. Multi-turn conversation context tracking and pronoun/anaphora resolution.
2. Extraction of relevant context (companies, topics, objectives, prior findings).
3. Entity lifecycle management across session turns.
4. Seamless integration with MemoryService.
"""

import re
import uuid
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone

from app.context.models import (
    EntityState,
    ConversationTurn,
    SessionContext,
    RelevantContext,
)
from app.context.session_memory import MemoryService, default_memory_service

logger = logging.getLogger("context_manager")

# Common tech/enterprise companies for fast recognition with standard casing
KNOWN_COMPANIES: Dict[str, str] = {
    "nvidia": "NVIDIA",
    "amd": "AMD",
    "intel": "Intel",
    "apple": "Apple",
    "microsoft": "Microsoft",
    "google": "Google",
    "alphabet": "Alphabet",
    "amazon": "Amazon",
    "meta": "Meta",
    "facebook": "Meta",
    "tesla": "Tesla",
    "qualcomm": "Qualcomm",
    "tsmc": "TSMC",
    "broadcom": "Broadcom",
    "arm": "ARM",
    "asml": "ASML",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "ibm": "IBM",
    "samsung": "Samsung",
    "cisco": "Cisco",
    "oracle": "Oracle",
    "dell": "Dell",
    "hpe": "HPE",
    "snowflake": "Snowflake",
    "palantir": "Palantir",
    "salesforce": "Salesforce",
}

# Common topics / domains in competitive intelligence
KNOWN_TOPICS = {
    "ai chips": ["ai chip", "ai chips", "accelerator", "accelerators", "gpu", "gpus", "npu", "blackwell", "h100", "b200", "mi300", "mi350", "gaudi"],
    "large language models": ["llm", "llms", "large language model", "reasoning model", "generative ai", "genai", "gpt", "claude", "gemini", "llama"],
    "datacenter & cloud": ["datacenter", "data center", "cloud", "aws", "azure", "gcp", "hyperscaler", "servers"],
    "semiconductor manufacturing": ["semiconductor", "foundry", "fab", "nanometer", "3nm", "2nm", "packaging", "cowos"],
    "financials & revenue": ["earnings", "revenue", "guidance", "market cap", "valuation", "quarterly results"],
}

PRONOUN_PATTERNS = [
    r"\b(its|it's|it)\b",
    r"\b(their|theirs|them|they)\b",
    r"\b(these|this)\s+(company|companies|chips|products|models|technologies|results|announcements)\b",
    r"\b(this\s+comparison|this\s+analysis|this\s+report)\b",
    r"\b(former|latter|both)\b",
    r"\b(supports?\s+this|about\s+this|related\s+to\s+this)\b",
]


class ContextManager:
    """
    Manages session context, resolves conversational references,
    and supplies relevant context to multi-agent pipelines.
    """

    def __init__(self, memory_service: Optional[MemoryService] = None):
        self.memory_service = memory_service or default_memory_service

    async def get_or_create_session(self, session_id: Optional[str] = None) -> SessionContext:
        """Retrieve an existing session or initialize a fresh SessionContext."""
        if not session_id or not session_id.strip():
            session_id = f"session-{uuid.uuid4().hex[:12]}"

        session = await self.memory_service.get_session(session_id)
        if not session:
            session = SessionContext(session_id=session_id)
            await self.memory_service.save_session(session)
            logger.info(f"Initialized new session context: '{session_id}'")
        return session

    def _extract_entities_from_text(self, text: str) -> EntityState:
        """Extracts known companies, topics, and comparison intents from text."""
        lower_text = text.lower()
        companies_found: List[str] = []
        topics_found: List[str] = []
        comparison_targets: List[str] = []

        # 1. Company extraction
        for comp_key, canonical_name in KNOWN_COMPANIES.items():
            # Match whole word
            if re.search(rf"\b{re.escape(comp_key)}\b", lower_text):
                if canonical_name not in companies_found:
                    companies_found.append(canonical_name)

        # 2. Topic extraction
        for topic_key, synonyms in KNOWN_TOPICS.items():
            for syn in synonyms:
                if re.search(rf"\b{re.escape(syn)}\b", lower_text):
                    if topic_key not in topics_found:
                        topics_found.append(topic_key)
                    break

        # 3. Comparison detection
        is_comparison = bool(
            re.search(r"\b(compare|comparison|versus|vs\.?|against|differ|difference|competing|head to head)\b", lower_text)
        )
        objective = "competitive comparison" if is_comparison else ("company overview" if companies_found else None)

        if is_comparison and len(companies_found) > 1:
            comparison_targets = companies_found[1:]

        return EntityState(
            companies=companies_found,
            topics=topics_found,
            comparison_targets=comparison_targets,
            active_objective=objective,
        )

    def _has_anaphora_or_follow_up(self, query: str) -> bool:
        """Checks if a user query contains pronouns or follow-up phrasing."""
        lower_q = query.lower()
        for pat in PRONOUN_PATTERNS:
            if re.search(pat, lower_q):
                return True
        # Short elliptical follow-ups e.g., "And AMD?", "What about revenue?", "Latest products?"
        if len(query.split()) <= 4 and ("what about" in lower_q or "how about" in lower_q or lower_q.startswith("and ") or "compare" in lower_q):
            return True
        return False

    def _rewrite_query_with_context(
        self,
        current_query: str,
        session: SessionContext
    ) -> Tuple[str, List[str]]:
        """
        Rewrites a follow-up query into an explicit, standalone query by resolving pronouns
        and referencing entities from active session state.
        """
        if not session.turns and not session.current_entities.companies:
            return current_query, []

        lower_q = current_query.lower().strip()
        context_notes: List[str] = []
        rewritten = current_query

        active_companies = session.current_entities.companies
        active_topics = session.current_entities.topics
        primary_company = active_companies[0] if active_companies else ""
        comparison_company = active_companies[1] if len(active_companies) > 1 else ""

        # Case 1: "Tell me about NVIDIA" -> "What are its latest AI chips?" -> "What are NVIDIA's latest AI chips?"
        if re.search(r"\b(its|it's)\b", lower_q) and primary_company:
            rewritten = re.sub(r"\b(its|it's)\b", f"{primary_company}'s", rewritten, flags=re.IGNORECASE)
            context_notes.append(f"Resolved 'its' -> {primary_company}")

        # Case 2: "it" -> primary_company
        elif re.search(r"\b(it)\b", lower_q) and primary_company and not re.search(r"\b(split|make it|take it)\b", lower_q):
            rewritten = re.sub(r"\b(it)\b", primary_company, rewritten, flags=re.IGNORECASE)
            context_notes.append(f"Resolved 'it' -> {primary_company}")

        # Case 3: "Compare them with AMD" / "Compare with AMD"
        if re.search(r"\b(compare\s+them\s+with|compare\s+with|compare\s+to|vs\.?)\s+([A-Za-z0-9]+)", lower_q):
            match = re.search(r"\b(compare\s+them\s+with|compare\s+with|compare\s+to|vs\.?)\s+([A-Za-z0-9]+)", current_query, flags=re.IGNORECASE)
            if match:
                target_comp = match.group(2).strip()
                topic_str = f" in {active_topics[0]}" if active_topics else ""
                if primary_company and primary_company.lower() != target_comp.lower():
                    rewritten = f"Compare {primary_company} and {target_comp}{topic_str}"
                    context_notes.append(f"Constructed comparative analysis between {primary_company} and {target_comp}")

        # Case 4: "What recent news supports this comparison?" / "What recent news supports this?"
        elif re.search(r"\b(supports?\s+this|about\s+this|related\s+to\s+this|supports?\s+this\s+comparison)\b", lower_q):
            if len(active_companies) >= 2:
                topic_str = f" in {active_topics[0]}" if active_topics else ""
                rewritten = f"Recent news and developments supporting the comparison between {active_companies[0]} and {active_companies[1]}{topic_str}"
                context_notes.append(f"Contextualized news query for {active_companies[0]} vs {active_companies[1]}")
            elif primary_company:
                topic_str = f" regarding {active_topics[0]}" if active_topics else ""
                rewritten = f"Recent news and developments for {primary_company}{topic_str}"
                context_notes.append(f"Contextualized news query for {primary_company}")

        # Case 5: Elliptical queries e.g. "What about their latest products?"
        elif re.search(r"\b(their|them|they)\b", lower_q):
            if len(active_companies) >= 2:
                comp_str = f"{active_companies[0]} and {active_companies[1]}"
                rewritten = re.sub(r"\b(their|theirs)\b", f"{comp_str}'s", rewritten, flags=re.IGNORECASE)
                rewritten = re.sub(r"\b(them|they)\b", comp_str, rewritten, flags=re.IGNORECASE)
                context_notes.append(f"Resolved 'their/them' -> {comp_str}")
            elif primary_company:
                rewritten = re.sub(r"\b(their|theirs)\b", f"{primary_company}'s", rewritten, flags=re.IGNORECASE)
                rewritten = re.sub(r"\b(them|they)\b", primary_company, rewritten, flags=re.IGNORECASE)
                context_notes.append(f"Resolved 'their/them' -> {primary_company}")

        return rewritten, context_notes

    async def get_relevant_context(
        self,
        session_id: str,
        current_query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> RelevantContext:
        """
        Retrieves query-relevant context from session memory, disambiguating
        pronouns and selecting pertinent entities and findings.
        """
        session = await self.get_or_create_session(session_id)

        # If session has no stored turns but chat_history was passed, bootstrap context
        if not session.turns and chat_history:
            for item in chat_history:
                if item.get("role") == "user":
                    extracted = self._extract_entities_from_text(item.get("content", ""))
                    session.current_entities.companies.extend(
                        [c for c in extracted.companies if c not in session.current_entities.companies]
                    )
                    session.current_entities.topics.extend(
                        [t for t in extracted.topics if t not in session.current_entities.topics]
                    )

        # Check if query needs contextual rewriting or entity grounding
        needs_resolution = self._has_anaphora_or_follow_up(current_query)
        rewritten_query, context_notes = self._rewrite_query_with_context(current_query, session)

        # Extract current query entities
        current_extracted = self._extract_entities_from_text(rewritten_query)

        # Merge active companies: give priority to current query companies, then memory
        combined_companies: List[str] = list(current_extracted.companies)
        for comp in session.current_entities.companies:
            if comp not in combined_companies:
                combined_companies.append(comp)

        # Merge active topics
        combined_topics: List[str] = list(current_extracted.topics)
        for top in session.current_entities.topics:
            if top not in combined_topics:
                combined_topics.append(top)

        # Active objective
        active_objective = (
            current_extracted.active_objective
            or session.current_entities.active_objective
            or ("competitive comparison" if len(combined_companies) > 1 else "company research")
        )

        # Gather concise relevant prior findings (from last 2 turns)
        prior_findings: List[str] = []
        for turn in reversed(session.turns[-2:]):
            if turn.key_findings:
                prior_findings.extend(turn.key_findings[:3])

        has_context = bool(session.turns or session.current_entities.companies or context_notes)

        recent_dialogue_summary = None
        if session.turns:
            last_turn = session.turns[-1]
            recent_dialogue_summary = f"Prior Turn: User asked '{last_turn.user_query}'"

        return RelevantContext(
            session_id=session.session_id,
            original_query=current_query,
            contextual_query=rewritten_query,
            active_companies=combined_companies,
            active_topics=combined_topics,
            active_objective=active_objective,
            comparison_targets=combined_companies[1:] if len(combined_companies) > 1 else [],
            relevant_prior_findings=prior_findings,
            recent_dialogue_summary=recent_dialogue_summary,
            has_context=has_context,
            context_notes=context_notes,
        )

    async def update_session(
        self,
        session_id: str,
        user_query: str,
        assistant_response: str,
        tools_used: Optional[List[str]] = None,
        key_findings: Optional[List[str]] = None,
        company_names: Optional[List[str]] = None,
        news_topics: Optional[List[str]] = None,
    ) -> SessionContext:
        """
        Updates session context and entities following a completed multi-agent execution.
        """
        session = await self.get_or_create_session(session_id)

        # Extract entities from both user query and assistant response
        query_entities = self._extract_entities_from_text(user_query)
        response_entities = self._extract_entities_from_text(assistant_response)

        all_new_companies: List[str] = list(query_entities.companies)
        for c in (company_names or []) + response_entities.companies:
            if c not in all_new_companies:
                all_new_companies.append(c)

        all_new_topics: List[str] = list(query_entities.topics)
        for t in (news_topics or []) + response_entities.topics:
            if t not in all_new_topics:
                all_new_topics.append(t)

        turn_entities = EntityState(
            companies=all_new_companies,
            topics=all_new_topics,
            active_objective=query_entities.active_objective or ("competitive comparison" if len(all_new_companies) > 1 else "company research"),
        )

        turn = ConversationTurn(
            turn_id=f"turn-{uuid.uuid4().hex[:8]}",
            user_query=user_query,
            assistant_response=assistant_response[:1000],  # store compact summary
            entities=turn_entities,
            key_findings=key_findings or [],
            tools_used=tools_used or [],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        session.turns.append(turn)
        session.updated_at = datetime.now(timezone.utc).isoformat()

        # Update current persistent session entities
        # Put newly mentioned companies at the beginning of the focus list
        updated_companies = list(all_new_companies)
        for c in session.current_entities.companies:
            if c not in updated_companies:
                updated_companies.append(c)
        session.current_entities.companies = updated_companies[:6]  # keep top 6 focus companies

        updated_topics = list(all_new_topics)
        for t in session.current_entities.topics:
            if t not in updated_topics:
                updated_topics.append(t)
        session.current_entities.topics = updated_topics[:6]

        session.current_entities.active_objective = turn_entities.active_objective

        await self.memory_service.save_session(session)
        logger.info(
            f"Updated session context '{session_id}': total turns={len(session.turns)}, "
            f"active_companies={session.current_entities.companies}, active_topics={session.current_entities.topics}"
        )
        return session

    async def clear_session(self, session_id: str) -> bool:
        """Deletes a session from memory."""
        return await self.memory_service.delete_session(session_id)


# Default singleton instance
default_context_manager = ContextManager()
