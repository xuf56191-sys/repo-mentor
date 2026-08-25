"""根据路线任务和真实仓库证据生成结构化评估。"""

from __future__ import annotations

import json

from repo_mentor.llm_service import create_llm
from repo_mentor.models import (
    AssessmentDifficulty,
    AssessmentPackage,
    LearnerProfile,
    LearningTask,
    RepositoryEvidence,
)
from repo_mentor.prompts import ASSESSMENT_PROMPT


def normalize_repo_path(path: str) -> str:
    """统一路径分隔符和大小写，用于仓库路径比对。"""
    return path.replace("\\", "/").strip().lower()


def infer_assessment_difficulty(
    learner_profile: LearnerProfile,
) -> AssessmentDifficulty:
    """根据学习者当前水平确定测验难度。"""
    level = learner_profile.current_level.strip().lower()

    advanced_markers = (
        "advanced",
        "高级",
        "资深",
        "专家",
    )
    intermediate_markers = (
        "intermediate",
        "中级",
        "进阶",
    )

    if any(
        marker in level
        for marker in advanced_markers
    ):
        return "advanced"

    if any(
        marker in level
        for marker in intermediate_markers
    ):
        return "intermediate"

    # 未知描述采用保守难度，不因为无法识别而生成过难题目。
    return "beginner"


def select_assessment_evidence(
    learning_task: LearningTask,
    repo_evidence: list[RepositoryEvidence],
) -> list[RepositoryEvidence]:
    """选择同时满足任务相关和内容已验证的仓库证据。"""
    task_paths = {
        normalize_repo_path(source.file_path)
        for source in learning_task.evidence_sources
    }

    selected: list[RepositoryEvidence] = []
    selected_paths: set[str] = set()

    for evidence in repo_evidence:
        normalized_path = normalize_repo_path(
            evidence.source_path
        )

        # 只允许当前路线任务已经引用的文件。
        if normalized_path not in task_paths:
            continue

        # 路径匹配不等于内容证据。
        # 没有 snippet 时不能据此询问文件内部实现。
        if not (evidence.snippet or "").strip():
            continue

        # 同一文件只向 LLM 提供一次。
        if normalized_path in selected_paths:
            continue

        selected.append(evidence)
        selected_paths.add(normalized_path)

    if not selected:
        raise ValueError(
            "当前路线任务没有可用于生成测验的真实内容证据"
        )

    return selected


def validate_assessment_against_context(
    assessment: AssessmentPackage,
    learning_task: LearningTask,
    difficulty: AssessmentDifficulty,
    evidence: list[RepositoryEvidence],
) -> AssessmentPackage:
    """验证 LLM 输出没有越过任务、难度和证据边界。"""
    if (
        assessment.related_task_title
        != learning_task.title
    ):
        raise ValueError(
            "评估包没有对应当前路线任务"
        )

    if assessment.difficulty != difficulty:
        raise ValueError(
            "评估包难度与学习者当前水平不一致"
        )

    evidence_by_path = {
        normalize_repo_path(item.source_path): item
        for item in evidence
    }

    all_items = [
        *assessment.questions,
        assessment.practice_task,
    ]

    for item in all_items:
        for source in item.evidence_sources:
            normalized_path = normalize_repo_path(
                source.file_path
            )
            actual_evidence = evidence_by_path.get(
                normalized_path
            )

            if actual_evidence is None:
                raise ValueError(
                    "评估项目引用了未授权仓库文件："
                    f"{source.file_path}"
                )

            if source.excerpt:
                actual_snippet = (
                    actual_evidence.snippet or ""
                )

                if source.excerpt not in actual_snippet:
                    raise ValueError(
                        "评估项目引用了证据中不存在的 excerpt："
                        f"{source.file_path}"
                    )

    if not assessment.practice_task.requires_human_review:
        raise ValueError(
            "实践任务必须标记为需要人工复核"
        )

    location_question = next(
        question
        for question in assessment.questions
        if question.question_type == "code_location"
    )

    normalized_answer = normalize_repo_path(
        location_question.expected_answer
    )

    if not any(
        allowed_path in normalized_answer
        for allowed_path in evidence_by_path
    ):
        raise ValueError(
            "代码定位题的参考答案必须包含真实来源路径"
        )

    return assessment


def generate_structured_assessment(
    learner_profile: LearnerProfile,
    learning_task: LearningTask,
    repo_evidence: list[RepositoryEvidence],
) -> AssessmentPackage:
    """根据学习者、路线任务和内容证据生成评估包。"""
    difficulty = infer_assessment_difficulty(
        learner_profile
    )
    selected_evidence = select_assessment_evidence(
        learning_task,
        repo_evidence,
    )

    llm = create_llm(
        thinking_enabled=False,
    )
    structured_llm = llm.with_structured_output(
        AssessmentPackage,
        method="function_calling",
        include_raw=True,
    )

    evidence_payload = [
        {
            "source_path": item.source_path,
            "snippet": item.snippet,
            "reason": item.reason,
            "confidence": item.confidence,
        }
        for item in selected_evidence
    ]

    messages = ASSESSMENT_PROMPT.format_messages(
        learner_profile=json.dumps(
            learner_profile.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        ),
        learning_task=json.dumps(
            learning_task.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        ),
        difficulty=difficulty,
        evidence=json.dumps(
            evidence_payload,
            ensure_ascii=False,
            indent=2,
        ),
    )

    result = structured_llm.invoke(messages)

    parsing_error = result.get("parsing_error")
    parsed = result.get("parsed")

    if parsing_error is not None:
        raise ValueError(
            "模型返回内容无法解析为 AssessmentPackage："
            f"{parsing_error}"
        )

    if parsed is None:
        raise ValueError(
            "模型没有返回可用的 AssessmentPackage"
        )

    if not isinstance(parsed, AssessmentPackage):
        raise TypeError(
            "结构化输出类型错误，"
            "预期 AssessmentPackage，"
            f"实际为 {type(parsed).__name__}"
        )

    return validate_assessment_against_context(
        assessment=parsed,
        learning_task=learning_task,
        difficulty=difficulty,
        evidence=selected_evidence,
    )
