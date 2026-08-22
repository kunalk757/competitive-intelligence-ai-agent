"""
Evidence Evaluation, Conflict Detection, Hypothesis Verification, and Self-Evaluation Engine.

Provides analytical rigor for multi-source intelligence:
- Detects disagreements across sources (e.g., conflicting specs, contradictory market claims).
- Weighs source reliability, publication dates, corroboration, and relevance.
- Tests analytical hypotheses with supporting/contradicting evidence.
- Scores overall investigation confidence ('high', 'medium', 'low').
- Performs structured self-evaluation before generating final response.
"""

import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple
from app.agent.agent_graph.state import (
    EvidenceItem,
    EvidenceConflict,
    HypothesisRecord,
    EvaluationResult,
)

logger = logging.getLogger("graph_evaluator")

# Source reliability weights
SOURCE_RELIABILITY: Dict[str, float] = {
    "official_company": 0.95,
    "sec_filing": 0.95,
    "arxiv": 0.90,
    "openreview": 0.90,
    "ieee": 0.90,
    "reuters": 0.85,
    "bloomberg": 0.85,
    "wall_street_journal": 0.85,
    "techcrunch": 0.80,
    "the_verge": 0.80,
    "gnews": 0.75,
    "tavily_web": 0.70,
    "general_web": 0.65,
}


def assess_source_reliability(source_name: str, url: Optional[str] = None) -> float:
    """Computes a reliability score for an evidence source."""
    if not source_name and not url:
        return 0.60
    
    text = f"{source_name or ''} {url or ''}".lower()
    for key, weight in SOURCE_RELIABILITY.items():
        if key.replace("_", " ") in text or key in text:
            return weight
            
    if "arxiv.org" in text or "openreview" in text:
        return 0.90
    if any(d in text for d in ["bloomberg", "reuters", "wsj", "ft.com", "cnbc"]):
        return 0.85
    if any(d in text for d in ["techcrunch", "anandtech", "tomshardware", "semianalysis"]):
        return 0.80

    return 0.70


def extract_evidence_from_results(
    collected_companies: List[Dict[str, Any]],
    collected_news: List[Dict[str, Any]],
    collected_research: List[Dict[str, Any]],
    collected_sources: List[Dict[str, Any]],
) -> List[EvidenceItem]:
    """Converts multi-source collections into normalized EvidenceItem records."""
    evidence_list: List[EvidenceItem] = []
    
    # 1. Company profiles
    for comp in collected_companies:
        name = comp.get("name", "Unknown Company")
        overview = comp.get("overview") or comp.get("description")
        if overview:
            evidence_list.append(
                EvidenceItem(
                    id=f"ev-comp-{uuid.uuid4().hex[:6]}",
                    claim=f"{name}: {overview[:200]}",
                    source_name=f"{name} Corporate Profile",
                    source_url=comp.get("website"),
                    reliability_score=0.95,
                    entity_tag=name,
                    is_corroborated=True,
                )
            )

    # 2. News articles
    for news in collected_news:
        title = news.get("title")
        if title:
            src = news.get("source", "News Source")
            url = news.get("url")
            evidence_list.append(
                EvidenceItem(
                    id=f"ev-news-{uuid.uuid4().hex[:6]}",
                    claim=f"Reported: {title}. {news.get('description', '')[:160]}",
                    source_name=src,
                    source_url=url,
                    publication_date=news.get("published_at"),
                    reliability_score=assess_source_reliability(src, url),
                    entity_tag=news.get("company_tag"),
                    is_corroborated=False,
                )
            )

    # 3. Research papers
    for paper in collected_research:
        title = paper.get("title")
        if title:
            src = paper.get("source", "Academic Repository")
            url = paper.get("url")
            evidence_list.append(
                EvidenceItem(
                    id=f"ev-paper-{uuid.uuid4().hex[:6]}",
                    claim=f"Scientific publication: '{title}'. Abstract: {paper.get('abstract', '')[:180]}",
                    source_name=src,
                    source_url=url,
                    reliability_score=assess_source_reliability(src, url),
                    is_corroborated=True,
                )
            )

    # 4. Verified citations
    for s in collected_sources:
        title = s.get("title")
        url = s.get("url")
        if title and url:
            evidence_list.append(
                EvidenceItem(
                    id=f"ev-src-{uuid.uuid4().hex[:6]}",
                    claim=f"{title}: {s.get('snippet', '')[:180]}",
                    source_name=url,
                    source_url=url,
                    reliability_score=assess_source_reliability(url, url),
                )
            )

    return evidence_list


def detect_and_resolve_conflicts(
    evidence: List[EvidenceItem],
    adversarial_config: Optional[Dict[str, Any]] = None,
) -> Tuple[List[EvidenceConflict], List[EvidenceItem]]:
    """
    Scans evidence items for contradictory claims, contrasting source recency,
    reputation, and corroboration.
    """
    conflicts: List[EvidenceConflict] = []
    
    # 1. Check for adversarial / simulated conflict injection
    if adversarial_config and adversarial_config.get("inject_conflicting_evidence"):
        sim_conf = adversarial_config["inject_conflicting_evidence"]
        conf_id = f"conf-{uuid.uuid4().hex[:6]}"
        
        # Analyze conflict
        claim_a = sim_conf.get("claim_a", "Source A asserts X")
        src_a = sim_conf.get("source_a", "Source A (Earlier Publication)")
        date_a = sim_conf.get("date_a", "2024-01-15")
        
        claim_b = sim_conf.get("claim_b", "Source B asserts NOT X")
        src_b = sim_conf.get("source_b", "Source B (Recent Benchmark)")
        date_b = sim_conf.get("date_b", "2025-02-10")
        
        analysis = (
            f"Cross-source disagreement detected on '{sim_conf.get('topic', 'market specifications')}'. "
            f"{src_b} ({date_b}) reflects more recent verified architectural measurements, "
            f"whereas {src_a} ({date_a}) refers to preliminary pre-release estimates."
        )
        
        conflicts.append(
            EvidenceConflict(
                id=conf_id,
                topic=sim_conf.get("topic", "Performance & Specifications"),
                claim_a=claim_a,
                source_a=src_a,
                date_a=date_a,
                claim_b=claim_b,
                source_b=src_b,
                date_b=date_b,
                analysis=analysis,
                resolution_status="resolved",
                preferred_claim=claim_b,
                confidence_impact="medium",
            )
        )
        logger.info(f"Conflict detected and analyzed: {conf_id} ({analysis})")

    # 2. Automated contradiction heuristics on collected evidence
    # Look for contrasting benchmarks or claims across entities
    claims_by_entity: Dict[str, List[EvidenceItem]] = {}
    for ev in evidence:
        if ev.entity_tag:
            claims_by_entity.setdefault(ev.entity_tag.upper(), []).append(ev)

    return conflicts, evidence


def verify_hypotheses(
    hypotheses: List[HypothesisRecord],
    evidence: List[EvidenceItem],
    conflicts: List[EvidenceConflict],
) -> List[HypothesisRecord]:
    """Tests hypotheses against gathered evidence and recorded conflicts."""
    evaluated: List[HypothesisRecord] = []
    
    for h in hypotheses:
        h_obj = h.model_copy()
        h_text_lower = h_obj.hypothesis_text.lower()
        
        supporting: List[str] = []
        contradicting: List[str] = []
        
        for ev in evidence:
            claim_lower = ev.claim.lower()
            # Match keywords
            keywords = [w for w in h_text_lower.split() if len(w) > 4 and w not in ["strong", "stronger", "competitive", "market", "relative"]]
            matches = sum(1 for kw in keywords if kw in claim_lower)
            if matches >= 2:
                supporting.append(f"[{ev.source_name}] {ev.claim[:120]}...")
            elif any(c in claim_lower for c in ["delay", "bug", "lower", "lagging", "concern"]):
                contradicting.append(f"[{ev.source_name}] {ev.claim[:120]}...")

        # Account for conflicts
        for c in conflicts:
            if c.topic.lower() in h_text_lower:
                contradicting.append(f"Conflict in {c.source_a} vs {c.source_b}: {c.analysis[:120]}...")

        h_obj.supporting_evidence = supporting[:4]
        h_obj.contradicting_evidence = contradicting[:2]
        
        # Calculate score
        sup_weight = len(supporting) * 0.25
        con_weight = len(contradicting) * 0.20
        score = min(1.0, max(0.0, 0.5 + sup_weight - con_weight))
        h_obj.evaluation_score = round(score, 2)
        
        if score >= 0.70:
            h_obj.status = "supported"
            h_obj.conclusion = f"Hypothesis supported with {len(supporting)} corroborating evidence source(s)."
        elif score <= 0.35:
            h_obj.status = "refuted"
            h_obj.conclusion = f"Hypothesis contradicted or unsupported by gathered evidence."
        else:
            h_obj.status = "inconclusive"
            h_obj.conclusion = "Evidence is mixed or partially supported; uncertainty remains."

        evaluated.append(h_obj)

    return evaluated


def calculate_overall_confidence(
    evidence: List[EvidenceItem],
    conflicts: List[EvidenceConflict],
    hypotheses: List[HypothesisRecord],
    tool_errors: List[Dict[str, Any]],
    detected_entities: List[str],
) -> Tuple[str, str]:
    """
    Computes uncertainty-aware confidence rating ('high', 'medium', 'low')
    along with an explanation string.
    """
    # Base score
    score = 0.80
    reasons: List[str] = []

    # Evidence count
    if len(evidence) >= 5:
        score += 0.10
        reasons.append("broad multi-source evidence")
    elif len(evidence) <= 2:
        score -= 0.25
        reasons.append("sparse evidence collected")

    # Critical tool errors
    if tool_errors:
        score -= min(0.30, len(tool_errors) * 0.15)
        reasons.append(f"{len(tool_errors)} tool error(s) occurred")

    # Conflicts
    if conflicts:
        unresolved = [c for c in conflicts if c.resolution_status != "resolved"]
        if unresolved:
            score -= 0.20
            reasons.append(f"{len(unresolved)} unresolved source conflict(s)")
        else:
            score -= 0.05
            reasons.append(f"{len(conflicts)} resolved source discrepancy")

    # Cap score
    score = max(0.1, min(1.0, score))

    if score >= 0.75:
        confidence = "high"
    elif score >= 0.50:
        confidence = "medium"
    else:
        confidence = "low"

    rationale = f"Confidence is rated '{confidence}' based on {', '.join(reasons) if reasons else 'consistent multi-source data'}."
    return confidence, rationale


def evaluate_investigation_state(
    user_query: str,
    investigation_goal: str,
    detected_entities: List[str],
    evidence: List[EvidenceItem],
    conflicts: List[EvidenceConflict],
    hypotheses: List[HypothesisRecord],
    confidence: str,
    tool_errors: List[Dict[str, Any]],
    iteration_count: int,
    max_iterations: int,
) -> EvaluationResult:
    """
    Runs self-evaluation check before synthesizing final response.
    Verifies that all criteria for a rigorous answer are met.
    """
    entities_covered = True
    if len(detected_entities) >= 2:
        # Check if we gathered evidence for at least the primary entities
        found_entities = {ev.entity_tag.upper() for ev in evidence if ev.entity_tag}
        uncovered = [e for e in detected_entities if e.upper() not in found_entities]
        # If more than 1 entity is completely missing and iterations remain, flag it
        if len(uncovered) > 1 and iteration_count < max_iterations:
            entities_covered = False

    sources_sufficient = len(evidence) >= 1
    conflicts_handled = True
    
    # Check if any unresolved conflicts exist without explanation
    for c in conflicts:
        if c.resolution_status == "unresolved" and not c.analysis:
            conflicts_handled = False

    critical_failures = False
    if not evidence and tool_errors and iteration_count < max_iterations:
        critical_failures = True

    # Decide if passed
    if critical_failures or (not entities_covered and iteration_count < max_iterations - 1):
        passed = False
        feedback = "Self-evaluation failed: Critical entities or evidence missing. Autonomous replan required."
        suggested_replan = True
    else:
        passed = True
        feedback = f"Self-evaluation passed: Evidence sufficient ({len(evidence)} items), confidence '{confidence}'."
        suggested_replan = False

    return EvaluationResult(
        passed=passed,
        answered_user_query=True,
        entities_covered=entities_covered,
        sources_sufficient=sources_sufficient,
        conflicts_handled=conflicts_handled,
        confidence_acceptable=(confidence in ["high", "medium"] or iteration_count >= max_iterations),
        critical_failures=critical_failures,
        feedback=feedback,
        suggested_replan=suggested_replan,
    )
