"""V0.8 真实来源 Top-3 检索评测。"""

from repo_mentor.retrieval_evaluation import (
    run_retrieval_evaluation,
)


def test_ten_learning_questions_find_real_sources():
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

    assert report.total_count == 10
    assert report.passed_count == 10, failed
    assert report.unrelated_question_rejected is True
    assert report.all_passed is True
