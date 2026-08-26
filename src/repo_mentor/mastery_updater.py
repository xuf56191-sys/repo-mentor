"""根据实际评估结果构建证据驱动的掌握度画像。"""

from __future__ import annotations

from collections import defaultdict

from repo_mentor.models import (
    EvaluationResult,
    KnowledgeMasteryEvidence,
    MasteryProfile,
    TargetTask,
)


# 24 日知识点状态和 25 日重新规划共用同一组阈值。
MASTERED_THRESHOLD = 0.8
PRACTICE_THRESHOLD = 0.6


def append_unique(
    items: list[str],
    value: str,
) -> None:
    """保持首次出现顺序地去重追加。"""
    if value not in items:
        items.append(value)


def normalized_result_score(
    result: EvaluationResult,
) -> float | None:
    """只把已经可靠评分的结果转换为 0 到 1。"""
    if (
        result.status != "evaluated"
        or result.score is None
    ):
        return None

    return result.score / result.max_score


def mastery_status_from_score(
    score: float,
) -> str:
    """把知识点分数转换为掌握状态。"""
    if score >= MASTERED_THRESHOLD:
        return "mastered"

    if score >= PRACTICE_THRESHOLD:
        return "developing"

    return "weak"


def build_mastery_profile(
    target_task: TargetTask,
    evaluation_results: list[EvaluationResult],
    *,
    profile_id: str = "mastery-current",
) -> MasteryProfile:
    """根据实际评估证据构建 MasteryProfile。"""
    if not evaluation_results:
        raise ValueError(
            "更新掌握度前必须存在评估结果"
        )

    result_ids = [
        result.item_id
        for result in evaluation_results
    ]

    if len(result_ids) != len(set(result_ids)):
        raise ValueError(
            "评估结果中存在重复 item_id"
        )

    reliable_results: list[
        tuple[EvaluationResult, float]
    ] = []

    point_scores: dict[
        str,
        list[float],
    ] = defaultdict(list)
    point_items: dict[
        str,
        list[str],
    ] = defaultdict(list)
    point_sources: dict[
        str,
        list[str],
    ] = defaultdict(list)
    point_order: list[str] = []

    for result in evaluation_results:
        normalized_score = normalized_result_score(
            result
        )

        # uncertain 和 needs_human_review 不参与分数计算。
        if normalized_score is None:
            continue

        reliable_results.append(
            (result, normalized_score)
        )

        for raw_point in result.knowledge_points:
            knowledge_point = raw_point.strip()

            if knowledge_point not in point_order:
                point_order.append(knowledge_point)

            point_scores[knowledge_point].append(
                normalized_score
            )
            append_unique(
                point_items[knowledge_point],
                result.item_id,
            )

            for source_file in result.source_files:
                append_unique(
                    point_sources[knowledge_point],
                    source_file,
                )

    knowledge_scores: dict[str, float] = {}
    knowledge_evidence: list[
        KnowledgeMasteryEvidence
    ] = []
    mastered_skills: list[str] = []
    weak_points: list[str] = []

    for knowledge_point in point_order:
        scores = point_scores[knowledge_point]
        average_score = round(
            sum(scores) / len(scores),
            4,
        )
        status = mastery_status_from_score(
            average_score
        )

        knowledge_scores[knowledge_point] = (
            average_score
        )

        knowledge_evidence.append(
            KnowledgeMasteryEvidence(
                knowledge_point=knowledge_point,
                score=average_score,
                status=status,
                assessment_item_ids=point_items[
                    knowledge_point
                ],
                source_files=point_sources[
                    knowledge_point
                ],
            )
        )

        if status == "mastered":
            mastered_skills.append(
                knowledge_point
            )
        elif status == "weak":
            weak_points.append(
                knowledge_point
            )

    reliable_scores = [
        score
        for _, score in reliable_results
    ]

    if reliable_scores:
        overall_score = round(
            sum(reliable_scores)
            / len(reliable_scores),
            4,
        )
    else:
        overall_score = 0.0

    completed_tasks = [
        result.item_id
        for result, _ in reliable_results
    ]

    confidence = round(
        len(reliable_results)
        / len(evaluation_results),
        4,
    )

    return MasteryProfile(
        profile_id=profile_id,
        target_task_title=target_task.title,
        overall_score=overall_score,
        knowledge_scores=knowledge_scores,
        strengths=list(mastered_skills),
        weak_points=weak_points,
        mastered_skills=mastered_skills,
        completed_tasks=completed_tasks,
        confidence=confidence,
        knowledge_evidence=knowledge_evidence,
        # 保留所有结果，包括 uncertain 和待人工复核，
        # 以便解释为什么 confidence 尚未达到 1。
        evaluation_results=list(
            evaluation_results
        ),
    )