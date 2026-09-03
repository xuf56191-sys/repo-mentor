"""V0.8 真实来源 Top-3 检索评测。"""

from repo_mentor.retrieval_evaluation import (
    run_retrieval_evaluation,
)


def test_twenty_questions_measure_sources_and_refusals():
    report = run_retrieval_evaluation()

    failed = [
        {
            "question": outcome.question,
            "expected": outcome.expected_paths,
            "returned": outcome.returned_paths,
        }
        for outcome in report.outcomes
        if not outcome.passed
    ]

    assert report.total_count == 20
    assert len(report.source_cases) == 16
    assert len(report.refusal_cases) == 4
    assert report.passed_count == 20, failed
    assert report.top3_hit_rate == 1.0
    assert report.refusal_rate == 1.0
    assert report.unrelated_question_rejected is True
    assert report.scoped_unsupported_answer_rate == 0.0
    assert (
        report.unbounded_baseline_unsupported_answer_rate
        == 1.0
    )
    assert report.all_passed is True
