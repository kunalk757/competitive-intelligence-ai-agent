"""
Evaluation Module for Competitive Intelligence AI Agent (Task 6).
"""

from app.evaluation.dataset import (
    EvaluationTestCase,
    EvaluationExpectedCriteria,
    get_evaluation_dataset,
)
from app.evaluation.metrics import (
    ScenarioMetricResult,
    AggregateEvaluationSummary,
    evaluate_single_run,
    evaluate_task_completion,
    evaluate_groundedness_and_hallucination,
    evaluate_recovery_and_robustness,
    compute_consistency_score,
    aggregate_evaluation_results,
)
from app.evaluation.baseline import SingleShotBaselineRunner
from app.evaluation.runner import AutomatedEvaluationRunner, run_and_save_evaluation
from app.evaluation.reporter import generate_markdown_report, save_markdown_report

__all__ = [
    "EvaluationTestCase",
    "EvaluationExpectedCriteria",
    "get_evaluation_dataset",
    "ScenarioMetricResult",
    "AggregateEvaluationSummary",
    "evaluate_single_run",
    "evaluate_task_completion",
    "evaluate_groundedness_and_hallucination",
    "evaluate_recovery_and_robustness",
    "compute_consistency_score",
    "aggregate_evaluation_results",
    "SingleShotBaselineRunner",
    "AutomatedEvaluationRunner",
    "run_and_save_evaluation",
    "generate_markdown_report",
    "save_markdown_report",
]
