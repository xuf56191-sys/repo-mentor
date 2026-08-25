import pytest

from repo_mentor import assessment_evaluator
from repo_mentor.assessment_evaluator import (
    collect_source_files,
    evaluate_code_location_answer,
    evaluate_concept_answer,
    mark_practice_for_human_review,
)
from repo_mentor.models import (
    ConceptEvaluationDraft,
    EvidenceSource,
    PracticeTask,
    QuizQuestion,
)


SOURCE_PATH = "src/repo_mentor/adaptive_workflow.py"


def make_source(
    file_path: str = SOURCE_PATH,
) -> EvidenceSource:
    return EvidenceSource(
        file_path=file_path,
        evidence_type="source",
        reason="该文件定义正式工作流",
        excerpt="def build_adaptive_graph():",
        confidence=1.0,
    )


def make_location_question() -> QuizQuestion:
    return QuizQuestion(
        question_id="question-location",
        question_type="code_location",
        prompt="build_adaptive_graph 定义在哪个文件？",
        expected_answer=SOURCE_PATH,
        difficulty="beginner",
        related_task_title="理解自适应工作流",
        evidence_sources=[make_source()],
        knowledge_points=["代码定位"],
        max_score=10,
    )

def make_concept_question() -> QuizQuestion:
    return QuizQuestion(
        question_id="question-concept",
        question_type="concept",
        prompt="为什么恢复工作流需要相同的 thread_id？",
        expected_answer=(
            "thread_id 用于定位对应会话保存的 checkpoint"
        ),
        difficulty="beginner",
        related_task_title="理解自适应工作流",
        evidence_sources=[make_source()],
        knowledge_points=["thread_id", "checkpoint"],
        max_score=10,
    )

def make_practice_task() -> PracticeTask:
    return PracticeTask(
        practice_id="practice-workflow",
        title="补充工作流测试",
        instructions="为工作流增加一个节点结构测试",
        expected_outcome="测试能够验证正式节点集合",
        deliverable="一个 pytest 测试函数",
        difficulty="beginner",
        related_task_title="理解自适应工作流",
        evidence_sources=[make_source()],
        knowledge_points=["StateGraph", "pytest"],
        completion_criteria=[
            "测试能够通过",
            "断言正式节点集合",
        ],
        max_score=20,
        estimated_hours=0.5,
    )

class FakeConceptStructuredLLM:
    def __init__(
        self,
        *,
        parsed=None,
        parsing_error=None,
        invoke_error=None,
    ):
        self.parsed = parsed
        self.parsing_error = parsing_error
        self.invoke_error = invoke_error

    def invoke(self, messages):
        if self.invoke_error is not None:
            raise self.invoke_error

        return {
            "parsed": self.parsed,
            "parsing_error": self.parsing_error,
            "raw": None,
        }


class FakeConceptLLM:
    def __init__(self, structured):
        self.structured = structured

    def with_structured_output(
        self,
        schema,
        **kwargs,
    ):
        assert schema is ConceptEvaluationDraft
        assert kwargs["method"] == "function_calling"
        assert kwargs["include_raw"] is True
        return self.structured

def test_code_location_full_path_gets_full_score():
    result = evaluate_code_location_answer(
        make_location_question(),
        (
            "函数位于 "
            "src/repo_mentor/adaptive_workflow.py"
        ),
    )

    assert result.score == 10
    assert result.evaluation_method == "rule"
    assert result.status == "evaluated"
    assert "完整" in result.feedback


def test_code_location_filename_gets_partial_score():
    result = evaluate_code_location_answer(
        make_location_question(),
        "函数位于 adaptive_workflow.py",
    )

    assert result.score == 6
    assert result.max_score == 10
    assert "没有提供完整仓库路径" in result.feedback


def test_code_location_wrong_path_gets_zero():
    result = evaluate_code_location_answer(
        make_location_question(),
        "函数位于 src/repo_mentor/config.py",
    )

    assert result.score == 0
    assert SOURCE_PATH in result.feedback


def test_code_location_evaluator_rejects_concept_question():
    concept = QuizQuestion(
        question_id="question-concept",
        question_type="concept",
        prompt="为什么工作流需要 checkpoint？",
        expected_answer="用于保存并恢复工作流状态",
        difficulty="beginner",
        related_task_title="理解自适应工作流",
        evidence_sources=[make_source()],
        knowledge_points=["checkpoint"],
    )

    with pytest.raises(
        ValueError,
        match="只接受 code_location",
    ):
        evaluate_code_location_answer(
            concept,
            "保存状态",
        )


def test_practice_submission_requires_human_review():
    result = mark_practice_for_human_review(
        make_practice_task(),
        "已添加 test_graph_has_expected_nodes 测试",
    )

    assert result.status == "needs_human_review"
    assert result.evaluation_method == "human"
    assert result.score is None
    assert result.max_score == 20
    assert "测试能够通过" in result.feedback


def test_empty_practice_submission_is_not_auto_passed():
    result = mark_practice_for_human_review(
        make_practice_task(),
        "",
    )

    assert result.status == "needs_human_review"
    assert result.score is None
    assert result.learner_response is None
    assert "尚未提交" in result.feedback


def test_collect_source_files_removes_duplicates():
    source = make_source()

    assert collect_source_files([
        source,
        source,
        make_source(
            r"SRC\REPO_MENTOR\ADAPTIVE_WORKFLOW.PY"
        ),
    ]) == [SOURCE_PATH]

def test_concept_answer_uses_model_with_specific_feedback(
    monkeypatch,
):
    draft = ConceptEvaluationDraft(
        status="evaluated",
        score=8,
        feedback="回答正确说明了会话定位作用。",
        matched_points=["thread_id 定位 checkpoint"],
        missing_points=["没有说明不同会话相互隔离"],
    )
    fake_llm = FakeConceptLLM(
        FakeConceptStructuredLLM(parsed=draft)
    )

    monkeypatch.setattr(
        assessment_evaluator,
        "create_llm",
        lambda **kwargs: fake_llm,
    )

    result = evaluate_concept_answer(
        make_concept_question(),
        "thread_id 用于找到之前保存的 checkpoint。",
    )

    assert result.status == "evaluated"
    assert result.evaluation_method == "model"
    assert result.score == 8
    assert "已体现" in result.feedback
    assert "仍缺少" in result.feedback
    assert "不同会话相互隔离" in result.feedback


def test_empty_concept_answer_skips_model(
    monkeypatch,
):
    def fail_if_called(**kwargs):
        raise AssertionError("空回答不应该调用 LLM")

    monkeypatch.setattr(
        assessment_evaluator,
        "create_llm",
        fail_if_called,
    )

    result = evaluate_concept_answer(
        make_concept_question(),
        "   ",
    )

    assert result.score == 0
    assert result.status == "evaluated"
    assert result.evaluation_method == "rule"
    assert "没有提交" in result.feedback


def test_uncertain_concept_result_has_no_score(
    monkeypatch,
):
    draft = ConceptEvaluationDraft(
        status="uncertain",
        score=None,
        feedback="当前回答过于模糊，无法可靠评分。",
        matched_points=[],
        missing_points=["thread_id", "checkpoint"],
    )
    fake_llm = FakeConceptLLM(
        FakeConceptStructuredLLM(parsed=draft)
    )

    monkeypatch.setattr(
        assessment_evaluator,
        "create_llm",
        lambda **kwargs: fake_llm,
    )

    result = evaluate_concept_answer(
        make_concept_question(),
        "它用于恢复。",
    )

    assert result.status == "uncertain"
    assert result.score is None
    assert result.evaluation_method == "model"


def test_concept_parsing_failure_does_not_give_score(
    monkeypatch,
):
    fake_llm = FakeConceptLLM(
        FakeConceptStructuredLLM(
            parsing_error=ValueError("invalid output"),
        )
    )

    monkeypatch.setattr(
        assessment_evaluator,
        "create_llm",
        lambda **kwargs: fake_llm,
    )

    result = evaluate_concept_answer(
        make_concept_question(),
        "thread_id 用于恢复 checkpoint。",
    )

    assert result.status == "uncertain"
    assert result.score is None
    assert "无法可靠解析" in result.feedback


def test_concept_score_above_maximum_becomes_uncertain(
    monkeypatch,
):
    # Draft 的通用范围允许到 100，
    # 但当前题目的 max_score 只有 10。
    draft = ConceptEvaluationDraft(
        status="evaluated",
        score=11,
        feedback="模型给出了越界分数。",
        matched_points=["thread_id"],
        missing_points=[],
    )
    fake_llm = FakeConceptLLM(
        FakeConceptStructuredLLM(parsed=draft)
    )

    monkeypatch.setattr(
        assessment_evaluator,
        "create_llm",
        lambda **kwargs: fake_llm,
    )

    result = evaluate_concept_answer(
        make_concept_question(),
        "thread_id 用于定位 checkpoint。",
    )

    assert result.status == "uncertain"
    assert result.score is None
    assert "超过题目最高分" in result.feedback