import pytest
from pydantic import ValidationError

from repo_mentor.models import (
    EvaluationResult,
    EvidenceSource,
    MasteryProfile,
    PracticeTask,
    QuizQuestion,
)


def make_source() -> EvidenceSource:
    """构造所有评估模型共用的真实仓库来源。"""
    return EvidenceSource(
        file_path="src/repo_mentor/adaptive_workflow.py",
        evidence_type="source",
        reason="该文件定义 V0.6 正式工作流",
        confidence=1.0,
    )


def make_evaluation(
    item_id: str = "question-checkpoint",
    **updates,
) -> EvaluationResult:
    """构造默认有效的单项评估结果。"""
    data = {
        "item_id": item_id,
        "item_type": "quiz_question",
        "learner_response": "thread_id 用于定位 checkpoint",
        "status": "evaluated",
        "evaluation_method": "rule",
        "score": 8,
        "max_score": 10,
        "feedback": "能够说明 thread_id 的基本作用",
        "knowledge_points": ["thread_id", "checkpoint"],
        "source_files": [
            "src/repo_mentor/adaptive_workflow.py",
        ],
    }
    data.update(updates)
    return EvaluationResult(**data)


def test_concept_question_can_be_structured():
    question = QuizQuestion(
        question_id="concept-checkpoint",
        question_type="concept",
        prompt="为什么恢复时必须使用相同的 thread_id？",
        expected_answer="thread_id 用于定位对应会话的 checkpoint",
        difficulty="beginner",
        related_task_title="人工确认与短期记忆",
        evidence_sources=[make_source()],
        knowledge_points=["thread_id", "checkpoint"],
    )

    dumped = question.model_dump(mode="json")

    assert dumped["question_type"] == "concept"
    assert dumped["evidence_sources"][0]["file_path"] == (
        "src/repo_mentor/adaptive_workflow.py"
    )
    assert dumped["knowledge_points"] == [
        "thread_id",
        "checkpoint",
    ]


def test_code_location_question_can_be_structured():
    question = QuizQuestion(
        question_id="location-checkpointer",
        question_type="code_location",
        prompt="create_memory_checkpointer 定义在哪个文件？",
        expected_answer="src/repo_mentor/adaptive_workflow.py",
        difficulty="beginner",
        related_task_title="V0.6 集成与图示",
        evidence_sources=[make_source()],
        knowledge_points=["JsonPlusSerializer"],
    )

    assert question.question_type == "code_location"
    assert question.expected_answer.endswith(
        "adaptive_workflow.py"
    )


def test_question_requires_repository_source():
    with pytest.raises(ValidationError):
        QuizQuestion(
            question_id="missing-source",
            question_type="concept",
            prompt="什么是 checkpoint？",
            expected_answer="工作流状态快照",
            difficulty="beginner",
            related_task_title="人工确认与短期记忆",
            evidence_sources=[],
            knowledge_points=["checkpoint"],
        )


def test_mermaid_practice_task_can_be_structured():
    practice = PracticeTask(
        practice_id="practice-v06-mermaid",
        title="绘制 V0.6 工作流图",
        instructions=(
            "根据 adaptive_workflow.py 绘制 Mermaid 流程图"
        ),
        expected_outcome="流程图与十节点工作流代码一致",
        deliverable="README 中的 Mermaid 图",
        difficulty="beginner",
        related_task_title="V0.6 集成与图示",
        evidence_sources=[make_source()],
        knowledge_points=[
            "StateGraph",
            "Conditional Edge",
            "Checkpoint",
        ],
        completion_criteria=[
            "包含十个业务节点",
            "包含证据补读循环",
            "包含人工修订循环",
        ],
        estimated_hours=0.5,
    )

    dumped = practice.model_dump(mode="json")

    assert dumped["practice_id"] == (
        "practice-v06-mermaid"
    )
    assert dumped["requires_human_review"] is True
    assert dumped["evidence_sources"][0]["file_path"] == (
        "src/repo_mentor/adaptive_workflow.py"
    )
    assert "Checkpoint" in dumped["knowledge_points"]


def test_evaluation_result_can_be_structured():
    result = make_evaluation()

    assert result.score == 8
    assert result.max_score == 10
    assert result.status == "evaluated"


def test_evaluation_rejects_score_above_maximum():
    with pytest.raises(
        ValidationError,
        match="实际得分不能高于最高分",
    ):
        make_evaluation(
            score=11,
            max_score=10,
        )


def test_evaluated_result_requires_score():
    with pytest.raises(
        ValidationError,
        match="已完成评分时必须提供实际得分",
    ):
        make_evaluation(
            status="evaluated",
            score=None,
        )


def test_pending_human_review_requires_human_method():
    with pytest.raises(
        ValidationError,
        match="evaluation_method 必须是 human",
    ):
        make_evaluation(
            item_type="practice_task",
            status="needs_human_review",
            evaluation_method="model",
            score=None,
        )


def test_mastery_profile_aggregates_results():
    result = make_evaluation()

    profile = MasteryProfile(
        profile_id="mastery-v07-demo",
        target_task_title="理解 LangGraph checkpoint",
        overall_score=0.8,
        knowledge_scores={
            "thread_id": 0.9,
            "checkpoint": 0.8,
            "reducer": 0.5,
        },
        strengths=["thread_id", "checkpoint"],
        weak_points=["reducer"],
        evaluation_results=[result],
    )

    dumped = profile.model_dump(mode="json")

    assert dumped["overall_score"] == 0.8
    assert dumped["knowledge_scores"]["reducer"] == 0.5
    assert dumped["evaluation_results"][0]["item_id"] == (
        "question-checkpoint"
    )


def test_mastery_rejects_invalid_knowledge_score():
    with pytest.raises(
        ValidationError,
        match="知识点掌握度必须在 0 到 1 之间",
    ):
        MasteryProfile(
            profile_id="invalid-score",
            target_task_title="理解 checkpoint",
            overall_score=0.8,
            knowledge_scores={
                "checkpoint": 1.2,
            },
        )


def test_mastery_rejects_duplicate_results():
    result = make_evaluation()

    with pytest.raises(
        ValidationError,
        match="同一个评估项目不能重复",
    ):
        MasteryProfile(
            profile_id="duplicate-results",
            target_task_title="理解 checkpoint",
            overall_score=0.8,
            knowledge_scores={
                "checkpoint": 0.8,
            },
            evaluation_results=[
                result,
                result,
            ],
        )