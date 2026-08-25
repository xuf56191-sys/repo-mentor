"""使用规则、模型和人工复核组合评估学习结果。"""

from __future__ import annotations

import json

from repo_mentor.assessment_generator import (
    normalize_repo_path,
)
from repo_mentor.llm_service import create_llm
from repo_mentor.models import (
    ConceptEvaluationDraft,
    EvaluationResult,
    PracticeTask,
    QuizQuestion,
)
from repo_mentor.prompts import (
    CONCEPT_EVALUATION_PROMPT,
)


def collect_source_files(
    evidence_sources,
) -> list[str]:
    """按原顺序收集并去重仓库来源路径。"""
    files: list[str] = []
    normalized_files: set[str] = set()

    for source in evidence_sources:
        normalized = normalize_repo_path(
            source.file_path
        )

        if normalized in normalized_files:
            continue

        files.append(source.file_path)
        normalized_files.add(normalized)

    return files


def make_uncertain_concept_result(
    question: QuizQuestion,
    learner_answer: str,
    reason: str,
) -> EvaluationResult:
    """构造不带高分的保守概念题结果。"""
    return EvaluationResult(
        item_id=question.question_id,
        item_type="quiz_question",
        learner_response=learner_answer or None,
        status="uncertain",
        evaluation_method="model",
        score=None,
        max_score=float(question.max_score),
        feedback=reason,
        knowledge_points=list(
            question.knowledge_points
        ),
        source_files=collect_source_files(
            question.evidence_sources
        ),
    )


def evaluate_concept_answer(
    question: QuizQuestion,
    learner_answer: str,
) -> EvaluationResult:
    """使用结构化 LLM 评估概念题回答。"""
    if question.question_type != "concept":
        raise ValueError(
            "概念评估器只接受 concept 题目"
        )

    answer = (learner_answer or "").strip()
    source_files = collect_source_files(
        question.evidence_sources
    )

    # 空回答不需要调用模型，可以确定为零分。
    if not answer:
        return EvaluationResult(
            item_id=question.question_id,
            item_type="quiz_question",
            learner_response=None,
            status="evaluated",
            evaluation_method="rule",
            score=0.0,
            max_score=float(question.max_score),
            feedback="学习者没有提交概念题回答。",
            knowledge_points=list(
                question.knowledge_points
            ),
            source_files=source_files,
        )

    llm = create_llm(
        thinking_enabled=False,
    )
    structured_llm = llm.with_structured_output(
        ConceptEvaluationDraft,
        method="function_calling",
        include_raw=True,
    )

    evidence_payload = [
        source.model_dump(mode="json")
        for source in question.evidence_sources
    ]

    messages = (
        CONCEPT_EVALUATION_PROMPT.format_messages(
            question=question.prompt,
            learner_answer=answer,
            expected_answer=question.expected_answer,
            max_score=question.max_score,
            knowledge_points=json.dumps(
                question.knowledge_points,
                ensure_ascii=False,
            ),
            evidence_sources=json.dumps(
                evidence_payload,
                ensure_ascii=False,
                indent=2,
            ),
        )
    )

    try:
        raw_result = structured_llm.invoke(messages)
    except Exception as error:
        return make_uncertain_concept_result(
            question,
            answer,
            (
                "概念题模型评分调用失败，"
                f"暂不自动给分：{type(error).__name__}。"
            ),
        )

    parsing_error = raw_result.get("parsing_error")
    draft = raw_result.get("parsed")

    if parsing_error is not None:
        return make_uncertain_concept_result(
            question,
            answer,
            "模型评分结果无法可靠解析，暂不自动给分。",
        )

    if not isinstance(draft, ConceptEvaluationDraft):
        return make_uncertain_concept_result(
            question,
            answer,
            "模型没有返回有效评分草稿，暂不自动给分。",
        )

    if (
        draft.score is not None
        and draft.score > question.max_score
    ):
        return make_uncertain_concept_result(
            question,
            answer,
            "模型建议得分超过题目最高分，结果已标记为不确定。",
        )

    feedback_parts = [draft.feedback]

    if draft.matched_points:
        feedback_parts.append(
            "已体现："
            + "、".join(draft.matched_points)
            + "。"
        )

    if draft.missing_points:
        feedback_parts.append(
            "仍缺少："
            + "、".join(draft.missing_points)
            + "。"
        )

    return EvaluationResult(
        item_id=question.question_id,
        item_type="quiz_question",
        learner_response=answer,
        status=draft.status,
        evaluation_method="model",
        score=draft.score,
        max_score=float(question.max_score),
        feedback=" ".join(feedback_parts),
        knowledge_points=list(
            question.knowledge_points
        ),
        source_files=source_files,
    )


def evaluate_code_location_answer(
    question: QuizQuestion,
    learner_answer: str,
) -> EvaluationResult:
    """使用仓库路径规则评估代码定位题。"""
    if question.question_type != "code_location":
        raise ValueError(
            "规则定位评估器只接受 code_location 题目"
        )

    answer = (learner_answer or "").strip()
    normalized_answer = normalize_repo_path(answer)

    source_files = collect_source_files(
        question.evidence_sources
    )
    normalized_sources = [
        normalize_repo_path(path)
        for path in source_files
    ]

    full_path_matches = [
        path
        for path in normalized_sources
        if path in normalized_answer
    ]

    filenames = [
        path.rsplit("/", 1)[-1]
        for path in normalized_sources
    ]
    filename_matches = [
        filename
        for filename in filenames
        if filename in normalized_answer
    ]

    if full_path_matches:
        score = float(question.max_score)
        feedback = (
            "回答包含完整且允许的仓库路径："
            f"{full_path_matches[0]}。"
        )
    elif filename_matches:
        score = round(
            question.max_score * 0.6,
            2,
        )
        feedback = (
            "回答定位到了正确文件名 "
            f"{filename_matches[0]}，"
            "但没有提供完整仓库路径。"
        )
    else:
        score = 0.0
        expected = "、".join(source_files)
        feedback = (
            "回答没有包含允许的仓库来源路径。"
            f"应定位到：{expected}。"
        )

    return EvaluationResult(
        item_id=question.question_id,
        item_type="quiz_question",
        learner_response=answer or None,
        status="evaluated",
        evaluation_method="rule",
        score=score,
        max_score=float(question.max_score),
        feedback=feedback,
        knowledge_points=list(
            question.knowledge_points
        ),
        source_files=source_files,
    )


def mark_practice_for_human_review(
    practice_task: PracticeTask,
    learner_submission: str,
) -> EvaluationResult:
    """实践产物不自动给分，交由人工按完成标准检查。"""
    submission = (learner_submission or "").strip()
    source_files = collect_source_files(
        practice_task.evidence_sources
    )
    criteria = "；".join(
        practice_task.completion_criteria
    )

    if submission:
        feedback = (
            "已收到实践提交说明，需要人工检查："
            f"{criteria}。"
        )
    else:
        feedback = (
            "尚未提交实践产物，需要人工确认以下标准："
            f"{criteria}。"
        )

    return EvaluationResult(
        item_id=practice_task.practice_id,
        item_type="practice_task",
        learner_response=submission or None,
        status="needs_human_review",
        evaluation_method="human",
        score=None,
        max_score=float(practice_task.max_score),
        feedback=feedback,
        knowledge_points=list(
            practice_task.knowledge_points
        ),
        source_files=source_files,
    )
