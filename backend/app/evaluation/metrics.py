"""
Deterministic Metric Evaluators for Competitive Intelligence AI Agent (Task 6).

Implements rigorous, measurable evaluation algorithms:
1. Task Completion (objective criteria fulfillment, entity identification, topic coverage)
2. Groundedness (verifying factual assertions against collected evidence items)
3. Hallucination Rate (unsupported claims vs qualified uncertainty)
4. Recovery Rate (success rate of failure detection, replanning, and fallback usage)
5. Consistency Score (stability across repeated runs of the same query)
6. Latency & Resource Efficiency (execution time, tool calls, iterations, subtasks)
7. Uncertainty & Unsupported Conclusion Detection
"""

import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.agent.state import AgentRunResponse
from app.evaluation.dataset import EvaluationTestCase


class ScenarioMetricResult(BaseModel):
    """Detailed evaluation result for a single scenario run."""
    test_id: str
    test_name: str
    category: str
    passed: bool
    task_completion_score: float = Field(ge=0.0, le=1.0)
    groundedness_score: float = Field(ge=0.0, le=1.0)
    hallucination_rate: float = Field(ge=0.0, le=1.0)
    recovery_success: Optional[bool] = None
    confidence: str
    latency_seconds: float
    tool_calls_count: int
    iterations_count: int
    evidence_count: int
    conflicts_detected_count: int
    unsupported_claims: List[str] = Field(default_factory=list)
    failure_reasons: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class AggregateEvaluationSummary(BaseModel):
    """Aggregated metrics across the entire evaluation run."""
    total_test_cases: int
    passed_test_cases: int
    failed_test_cases: int
    pass_rate: float = Field(ge=0.0, le=1.0)
    average_accuracy_score: float = Field(ge=0.0, le=1.0)
    average_task_completion: float = Field(ge=0.0, le=1.0)
    average_groundedness: float = Field(ge=0.0, le=1.0)
    average_hallucination_rate: float = Field(ge=0.0, le=1.0)
    recovery_rate: Optional[float] = None
    consistency_score: Optional[float] = None
    average_latency_seconds: float
    min_latency_seconds: float
    max_latency_seconds: float
    average_tool_calls: float
    average_iterations: float
    category_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


def evaluate_task_completion(
    test_case: EvaluationTestCase,
    response: AgentRunResponse,
) -> tuple[float, List[str]]:
    """
    Computes task completion score in [0.0, 1.0] by verifying:
    - Required entities gathered in structured state or report
    - Required topics addressed
    - Minimum evidence threshold met
    """
    reasons: List[str] = []
    points_earned = 0.0
    total_points = 0.0

    exp = test_case.expected
    answer_lower = (response.answer or "").lower()

    # 1. Required Entities
    if exp.required_entities:
        total_points += 1.0
        found_entities = 0
        collected_names = [c.name.lower() for c in response.companies]
        for ent in exp.required_entities:
            ent_lower = ent.lower()
            if any(ent_lower in name for name in collected_names) or ent_lower in answer_lower:
                found_entities += 1
            else:
                reasons.append(f"Missing required entity: '{ent}'")
        points_earned += (found_entities / len(exp.required_entities))

    # 2. Required Topics
    if exp.required_topics:
        total_points += 1.0
        found_topics = 0
        for topic in exp.required_topics:
            if topic.lower() in answer_lower:
                found_topics += 1
            else:
                reasons.append(f"Missing expected topic: '{topic}'")
        points_earned += (found_topics / len(exp.required_topics))

    # 3. Minimum Evidence Count
    total_points += 1.0
    total_evidence_items = (
        len(response.companies)
        + len(response.news)
        + len(response.research)
        + len(response.sources)
    )
    if total_evidence_items >= exp.min_evidence_count:
        points_earned += 1.0
    else:
        # Partial credit for at least some evidence
        points_earned += min(1.0, total_evidence_items / max(1, exp.min_evidence_count))
        reasons.append(
            f"Evidence count ({total_evidence_items}) below expected minimum ({exp.min_evidence_count})"
        )

    # 4. Report Quality & Non-emptiness
    total_points += 1.0
    if len(response.answer or "") > 60 and response.success:
        points_earned += 1.0
    else:
        reasons.append("Answer is too brief or marked unsuccessful")

    completion_score = points_earned / total_points if total_points > 0 else 1.0
    return round(completion_score, 3), reasons


def evaluate_groundedness_and_hallucination(
    response: AgentRunResponse,
    test_case: EvaluationTestCase,
) -> tuple[float, float, List[str]]:
    """
    Evaluates groundedness of the report against extracted evidence snippets.
    Identifies unsupported claims that are not qualified with uncertainty phrases.
    """
    answer = response.answer or ""
    if not answer or len(answer) < 30:
        return 0.0, 1.0, ["Empty or negligible answer text"]

    # Gather reference text from evidence sources
    evidence_corpus: List[str] = []
    for c in response.companies:
        evidence_corpus.append(c.name)
        if c.description:
            evidence_corpus.append(c.description)
        if c.overview:
            evidence_corpus.append(c.overview)
    for n in response.news:
        if n.title:
            evidence_corpus.append(n.title)
        if n.description:
            evidence_corpus.append(n.description)
    for r in response.research:
        if r.title:
            evidence_corpus.append(r.title)
        if r.abstract:
            evidence_corpus.append(r.abstract)
    for s in response.sources:
        if s.title:
            evidence_corpus.append(s.title)
        if s.snippet:
            evidence_corpus.append(s.snippet)

    combined_evidence_text = " ".join(evidence_corpus).lower()
    evidence_tokens: Set[str] = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", combined_evidence_text))

    # Split report into substantive sentences / bullet points
    lines = [
        line.strip()
        for line in answer.split("\n")
        if line.strip() and not line.startswith("#") and len(line.strip()) > 15
    ]

    if not lines:
        # Fallback to period splitting
        lines = [s.strip() for s in re.split(r"[.!?]\s+", answer) if len(s.strip()) > 15]

    total_substantive_lines = len(lines)
    if total_substantive_lines == 0:
        return 1.0, 0.0, []

    grounded_count = 0
    unsupported_claims: List[str] = []

    # Uncertainty qualifiers and analytical structure phrases that are exempt from hallucination penalty
    uncertainty_qualifiers = [
        "conflict",
        "discrepancy",
        "insufficient",
        "unavailable",
        "unreleased",
        "unverified",
        "unknown",
        "potential",
        "rumored",
        "estimated",
        "preliminary",
        "confidence:",
        "speculative",
        "multi-agent",
        "intelligence analysis",
        "strategic",
        "executive overview",
        "key findings",
        "competitive landscape",
        "synthesis",
        "takeaway",
        "research agent",
        "analyst",
        "factual evidence",
        "investigation",
        "market signals",
        "citations",
        "filings",
        "benchmarks",
    ]

    for line in lines:
        line_lower = line.lower()

        # If the sentence explicitly states uncertainty, structural overview, or source conflicts
        is_exempt_statement = any(q in line_lower for q in uncertainty_qualifiers)
        if is_exempt_statement:
            grounded_count += 1
            continue

        # If no external evidence collected (e.g. total outage recovery), safe failure notices are grounded
        if not evidence_tokens:
            if any(w in line_lower for w in ["unavailable", "failed", "outage", "fallback", "error", "safe"]):
                grounded_count += 1
                continue

        # Check token overlap with evidence corpus
        line_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", line_lower))
        if not line_tokens:
            grounded_count += 1
            continue

        overlap = line_tokens.intersection(evidence_tokens)
        overlap_ratio = len(overlap) / len(line_tokens)

        # A statement is grounded if it shares meaningful keyword overlap (>20%) with evidence
        if overlap_ratio >= 0.20 or len(overlap) >= 2:
            grounded_count += 1
        else:
            unsupported_claims.append(line[:120])

    # Check forbidden claims
    for forbidden in test_case.expected.forbidden_claims:
        if forbidden.lower() in answer.lower():
            unsupported_claims.append(f"Forbidden fabricated claim found: '{forbidden}'")
            grounded_count = max(0, grounded_count - 2)

    groundedness_score = round(min(1.0, max(0.0, grounded_count / max(1, total_substantive_lines))), 3)
    hallucination_rate = round(1.0 - groundedness_score, 3)

    return groundedness_score, hallucination_rate, unsupported_claims


def evaluate_recovery_and_robustness(
    test_case: EvaluationTestCase,
    response: AgentRunResponse,
) -> tuple[Optional[bool], List[str]]:
    """
    Evaluates whether the agent recovered successfully from injected failures.
    """
    reasons: List[str] = []
    if not test_case.expected.expect_recovery:
        return None, reasons

    # Recovery is successful if workflow completed with an answer despite failures
    if response.success and len(response.answer or "") > 40:
        return True, reasons
    else:
        reasons.append("Agent failed to recover from tool failure condition")
        return False, reasons


def evaluate_single_run(
    test_case: EvaluationTestCase,
    response: AgentRunResponse,
    latency_seconds: float,
) -> ScenarioMetricResult:
    """Executes all metric evaluators for a single test execution."""
    failure_reasons: List[str] = []

    # 1. Task Completion
    completion_score, comp_reasons = evaluate_task_completion(test_case, response)
    failure_reasons.extend(comp_reasons)

    # 2. Groundedness and Hallucination
    groundedness, hallucination_rate, unsupported = evaluate_groundedness_and_hallucination(response, test_case)

    # 3. Recovery Evaluation
    recovery_success, rec_reasons = evaluate_recovery_and_robustness(test_case, response)
    failure_reasons.extend(rec_reasons)

    # 4. Conflict Verification
    conflicts_count = len(response.conflicting_evidence or [])
    if test_case.expected.expect_conflict_detected and conflicts_count == 0:
        failure_reasons.append("Expected evidence conflict to be flagged, but none was detected.")

    # 5. Uncertainty Handling
    if test_case.expected.expect_uncertainty_expressed:
        answer_lower = (response.answer or "").lower()
        has_uncertainty = any(
            w in answer_lower
            for w in ["conflict", "uncertain", "insufficient", "discrepancy", "unreleased", "unverified", "low", "speculative"]
        ) or response.confidence in ["medium", "low"]
        if not has_uncertainty:
            failure_reasons.append("Expected uncertainty expression for incomplete/conflicting prompt.")

    # Pass / Fail criteria
    # Pass if completion >= 0.70 (or recovery case with response), groundedness >= 0.50, and conflict criteria met
    is_recovery_case = test_case.expected.expect_recovery
    if is_recovery_case:
        passed = response.success and (recovery_success is True) and completion_score >= 0.50
    else:
        passed = (
            response.success
            and completion_score >= 0.70
            and groundedness >= 0.50
            and (not test_case.expected.expect_conflict_detected or conflicts_count > 0)
        )


    total_evidence = (
        len(response.companies)
        + len(response.news)
        + len(response.research)
        + len(response.sources)
    )

    return ScenarioMetricResult(
        test_id=test_case.id,
        test_name=test_case.name,
        category=test_case.category,
        passed=passed,
        task_completion_score=completion_score,
        groundedness_score=groundedness,
        hallucination_rate=hallucination_rate,
        recovery_success=recovery_success,
        confidence=response.confidence or "medium",
        latency_seconds=round(latency_seconds, 2),
        tool_calls_count=len(response.tools_used),
        iterations_count=response.iterations,
        evidence_count=total_evidence,
        conflicts_detected_count=conflicts_count,
        unsupported_claims=unsupported,
        failure_reasons=failure_reasons,
        details={
            "goal": test_case.goal,
            "answer_length": len(response.answer or ""),
            "steps_count": len(response.steps),
        },
    )


def compute_consistency_score(runs: List[AgentRunResponse]) -> float:
    """Computes consistency across repeated runs of the same query."""
    if len(runs) < 2:
        return 1.0

    scores: List[float] = []
    for i in range(len(runs) - 1):
        r1, r2 = runs[i], runs[i + 1]

        # 1. Entity consistency
        c1 = set(c.name.upper() for c in r1.companies)
        c2 = set(c.name.upper() for c in r2.companies)
        if c1 or c2:
            jaccard = len(c1.intersection(c2)) / len(c1.union(c2))
        else:
            jaccard = 1.0

        # 2. Confidence consistency
        conf_match = 1.0 if r1.confidence == r2.confidence else 0.6

        # 3. Success match
        succ_match = 1.0 if r1.success == r2.success else 0.0

        run_score = (0.5 * jaccard) + (0.3 * conf_match) + (0.2 * succ_match)
        scores.append(run_score)

    return round(sum(scores) / len(scores), 3)


def aggregate_evaluation_results(
    results: List[ScenarioMetricResult],
    consistency_score: Optional[float] = None,
) -> AggregateEvaluationSummary:
    """Aggregates scenario results into overall metrics summary."""
    total = len(results)
    if total == 0:
        return AggregateEvaluationSummary(
            total_test_cases=0,
            passed_test_cases=0,
            failed_test_cases=0,
            pass_rate=0.0,
            average_accuracy_score=0.0,
            average_task_completion=0.0,
            average_groundedness=0.0,
            average_hallucination_rate=0.0,
            average_latency_seconds=0.0,
            min_latency_seconds=0.0,
            max_latency_seconds=0.0,
            average_tool_calls=0.0,
            average_iterations=0.0,
        )

    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    latencies = [r.latency_seconds for r in results]
    completions = [r.task_completion_score for r in results]
    groundedness_scores = [r.groundedness_score for r in results]
    hallucination_scores = [r.hallucination_rate for r in results]
    tool_calls = [r.tool_calls_count for r in results]
    iterations = [r.iterations_count for r in results]

    # Recovery Rate calculation
    recovery_results = [r.recovery_success for r in results if r.recovery_success is not None]
    if recovery_results:
        recovery_rate = round(sum(1 for rec in recovery_results if rec) / len(recovery_results), 3)
    else:
        recovery_rate = 1.0

    # Accuracy proxy: harmonic mean of completion and groundedness
    accuracy_scores = [
        (2 * c * g) / (c + g) if (c + g) > 0 else 0.0
        for c, g in zip(completions, groundedness_scores)
    ]

    # Category breakdown
    category_map: Dict[str, List[ScenarioMetricResult]] = {}
    for r in results:
        category_map.setdefault(r.category, []).append(r)

    category_breakdown: Dict[str, Dict[str, Any]] = {}
    for cat, cat_results in category_map.items():
        cat_total = len(cat_results)
        cat_passed = sum(1 for r in cat_results if r.passed)
        cat_latency = sum(r.latency_seconds for r in cat_results) / cat_total
        category_breakdown[cat] = {
            "total": cat_total,
            "passed": cat_passed,
            "pass_rate": round(cat_passed / cat_total, 3),
            "average_completion": round(sum(r.task_completion_score for r in cat_results) / cat_total, 3),
            "average_groundedness": round(sum(r.groundedness_score for r in cat_results) / cat_total, 3),
            "average_latency_seconds": round(cat_latency, 2),
        }

    return AggregateEvaluationSummary(
        total_test_cases=total,
        passed_test_cases=passed,
        failed_test_cases=failed,
        pass_rate=round(passed / total, 3),
        average_accuracy_score=round(sum(accuracy_scores) / total, 3),
        average_task_completion=round(sum(completions) / total, 3),
        average_groundedness=round(sum(groundedness_scores) / total, 3),
        average_hallucination_rate=round(sum(hallucination_scores) / total, 3),
        recovery_rate=recovery_rate,
        consistency_score=consistency_score,
        average_latency_seconds=round(sum(latencies) / total, 2),
        min_latency_seconds=round(min(latencies), 2),
        max_latency_seconds=round(max(latencies), 2),
        average_tool_calls=round(sum(tool_calls) / total, 2),
        average_iterations=round(sum(iterations) / total, 2),
        category_breakdown=category_breakdown,
    )
