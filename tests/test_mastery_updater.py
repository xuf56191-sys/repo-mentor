import pytest

from repo_mentor.mastery_updater import (
    build_mastery_profile,
    mastery_status_from_score,
    normalized_result_score,
)
from repo_mentor.models import (
    EvaluationResult,
    TargetTask,
)


def make_target() -> TargetTask:
    return TargetTask(
        title="理解 LangGraph 掌握度闭环",
        description="实现评估、画像更新和重新规划流程",
        task_type="understand_module",
        expected_outcome="能够解释并实现掌握度闭环",
    )


def make_result(
    item_id: str,
    *,
    score: float | None,
    max_score: float = 10,
    status: str = "evaluated",
    method: str = "rule",
    knowledge_points: list[str] | None = None,
    source_files: list[str] | None = None,
) -> EvaluationResult:
    return EvaluationResult(
        item_id=item_id,
        item_type=(
            "practice_task"
            if status == "needs_human_review"
            else "quiz_question"
        ),
        learner_response="测试回答",
        status=status,
        evaluation_method=method,
        score=score,
        max_score=max_score,
        feedback="用于掌握度更新测试的具体反馈",
        knowledge_points=(
            knowledge_points
            or ["checkpoint"]
        ),
        source_files=(
            source_files
            or [
                "src/repo_mentor/adaptive_workflow.py",
            ]
        ),
    )


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (1.0, "mastered"),
        (0.8, "mastered"),
        (0.79, "developing"),
        (0.6, "developing"),
        (0.59, "weak"),
        (0.0, "weak"),
    ],
)
def test_mastery_status_thresholds(
    score,
    expected,
):
    assert (
        mastery_status_from_score(score)
        == expected
    )


def test_profile_uses_only_reliably_scored_results():
    concept = make_result(
        "question-concept",
        score=8,
        knowledge_points=[
            "checkpoint",
            "thread_id",
        ],
    )
    location = make_result(
        "question-location",
        score=10,
        knowledge_points=["代码定位"],
    )
    practice = make_result(
        "practice-workflow",
        score=None,
        status="needs_human_review",
        method="human",
        knowledge_points=["pytest"],
    )

    profile = build_mastery_profile(
        make_target(),
        [
            concept,
            location,
            practice,
        ],
    )

    assert profile.overall_score == 0.9
    assert profile.confidence == 0.6667
    assert profile.completed_tasks == [
        "question-concept",
        "question-location",
    ]
    assert "practice-workflow" not in (
        profile.completed_tasks
    )
    assert profile.mastered_skills == [
        "checkpoint",
        "thread_id",
        "代码定位",
    ]
    assert "pytest" not in profile.knowledge_scores


def test_weak_point_is_traceable_to_item_and_source():
    result = make_result(
        "question-reducer",
        score=4,
        knowledge_points=["reducer"],
        source_files=[
            "src/repo_mentor/workflow_state.py",
        ],
    )

    profile = build_mastery_profile(
        make_target(),
        [result],
    )

    assert profile.weak_points == ["reducer"]
    assert "reducer" not in profile.mastered_skills

    evidence = profile.knowledge_evidence[0]
    assert evidence.knowledge_point == "reducer"
    assert evidence.score == 0.4
    assert evidence.status == "weak"
    assert evidence.assessment_item_ids == [
        "question-reducer",
    ]
    assert evidence.source_files == [
        "src/repo_mentor/workflow_state.py",
    ]


def test_self_report_does_not_override_low_evidence():
    """即使用户自述会 Python，函数也只接受评估结果。"""
    result = make_result(
        "question-python",
        score=3,
        knowledge_points=["python"],
    )

    profile = build_mastery_profile(
        make_target(),
        [result],
    )

    assert "python" in profile.weak_points
    assert "python" not in profile.mastered_skills


def test_uncertain_result_does_not_change_score():
    reliable = make_result(
        "question-reliable",
        score=8,
        knowledge_points=["checkpoint"],
    )
    uncertain = make_result(
        "question-uncertain",
        score=None,
        status="uncertain",
        method="model",
        knowledge_points=["reflection"],
    )

    profile = build_mastery_profile(
        make_target(),
        [
            reliable,
            uncertain,
        ],
    )

    assert profile.overall_score == 0.8
    assert profile.confidence == 0.5
    assert profile.completed_tasks == [
        "question-reliable",
    ]
    assert "reflection" not in profile.knowledge_scores


def test_profile_with_no_reliable_scores_is_conservative():
    pending = make_result(
        "practice-pending",
        score=None,
        status="needs_human_review",
        method="human",
    )
    uncertain = make_result(
        "question-uncertain",
        score=None,
        status="uncertain",
        method="model",
    )

    profile = build_mastery_profile(
        make_target(),
        [
            pending,
            uncertain,
        ],
    )

    assert profile.overall_score == 0.0
    assert profile.confidence == 0.0
    assert profile.completed_tasks == []
    assert profile.mastered_skills == []
    assert profile.weak_points == []
    assert profile.knowledge_evidence == []


def test_normalized_result_score_ignores_pending_result():
    pending = make_result(
        "practice-pending",
        score=None,
        status="needs_human_review",
        method="human",
    )

    assert normalized_result_score(pending) is None


def test_profile_rejects_duplicate_result_ids():
    first = make_result(
        "duplicate-id",
        score=8,
    )
    second = make_result(
        "duplicate-id",
        score=6,
    )

    with pytest.raises(
        ValueError,
        match="重复 item_id",
    ):
        build_mastery_profile(
            make_target(),
            [first, second],
        )


def test_profile_requires_evaluation_results():
    with pytest.raises(
        ValueError,
        match="必须存在评估结果",
    ):
        build_mastery_profile(
            make_target(),
            [],
        )