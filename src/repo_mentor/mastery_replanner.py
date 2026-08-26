"""根据掌握度生成确定性的自适应重规划决定。"""

from repo_mentor.mastery_updater import (
    MASTERED_THRESHOLD,
    PRACTICE_THRESHOLD,
)
from repo_mentor.models import (
    EvidenceSource,
    KnowledgeMasteryEvidence,
    LearningTask,
    MasteryProfile,
    ReplanDecision,
)

def select_focus_points(
    evidence_items: list[KnowledgeMasteryEvidence],
    allowed_statuses: set[str],
) -> list[str]:
    """按原始证据顺序选出需要加强的知识点。"""
    focus_points = [
        item.knowledge_point
        for item in evidence_items
        if item.status in allowed_statuses
    ]

    # 如果状态没有匹配项，保守选择得分最低的知识点。
    if not focus_points and evidence_items:
        weakest_item = min(
            evidence_items,
            key=lambda item: item.score,
        )
        focus_points.append(weakest_item.knowledge_point)

    return focus_points


def decide_replan(
    mastery: MasteryProfile,
    *,
    replan_count: int,
    max_replans: int,
) -> ReplanDecision:
    """根据总体掌握度和重规划上限决定下一步。"""
    if replan_count < 0:
        raise ValueError("replan_count 不能小于 0")

    if max_replans < 1:
        raise ValueError("max_replans 必须至少为 1")

    if replan_count > max_replans:
        raise ValueError(
            "replan_count 不能超过 max_replans"
        )

    score = mastery.overall_score
    evidence_items = mastery.knowledge_evidence

    # 1. score >= 0.8 时返回 advance。
    # 注意：advance 不是重新规划，所以应在次数上限之前判断。
    if score >= MASTERED_THRESHOLD:
        return ReplanDecision(
            action="advance",
            overall_score=score,
            reason="总体掌握度达到 80%，可以进入下一个学习模块。",
            focus_points=[],
            replan_count=replan_count,
            max_replans=max_replans,
        )

    # 没有知识点证据，就无法生成可追溯的补充任务。
    if not evidence_items:
        return ReplanDecision(
            action="stop",
            overall_score=score,
            reason="缺少可追溯的知识点评估证据，无法安全重新规划。",
            focus_points=[],
            replan_count=replan_count,
            max_replans=max_replans,
        )

    # 2. 已经达到重规划次数上限时返回 stop。
    if replan_count >= max_replans:
        return ReplanDecision(
            action="stop",
            overall_score=score,
            reason=f"已经达到最多 {max_replans} 次重新规划上限。",
            focus_points=[],
            replan_count=replan_count,
            max_replans=max_replans,
        )

    # 3. 0.6 <= score < 0.8 时增加实践任务。
    # 实践任务可以针对 developing 和 weak 两种知识点。
    if score >= PRACTICE_THRESHOLD:
        focus_points = select_focus_points(
            evidence_items,
            {"developing", "weak"},
        )

        return ReplanDecision(
            action="add_practice",
            overall_score=score,
            reason="总体掌握度处于 60% 到 79% 之间，需要增加针对性实践。",
            focus_points=focus_points,
            replan_count=replan_count,
            max_replans=max_replans,
        )

    # 4. score < 0.6 时增加复习任务，只优先选择 weak 知识点。
    focus_points = select_focus_points(
        evidence_items,
        {"weak"},
    )

    return ReplanDecision(
        action="add_review",
        overall_score=score,
        reason="总体掌握度低于 60%，需要先复习薄弱知识点。",
        focus_points=focus_points,
        replan_count=replan_count,
        max_replans=max_replans,
    )

def select_focus_evidence_for_replan(
    mastery: MasteryProfile,
    decision: ReplanDecision,
) -> list[KnowledgeMasteryEvidence]:
    """取得 focus_points 对应的可追溯掌握证据。"""
    # TODO 1：
    # 把 mastery.knowledge_evidence 转换成字典：
    # key 是 knowledge_point，value 是证据对象。
    evidence_map = {
        item.knowledge_point: item
        for item in mastery.knowledge_evidence
    }

    # TODO 2：
    # 检查 decision.focus_points 中是否存在找不到证据的知识点。
    # 如果存在，抛出 ValueError：
    # f"以下重规划知识点缺少评估证据：{missing_points}"
    missing_points = [
        knowledge_point
        for knowledge_point in decision.focus_points
        if knowledge_point not in evidence_map
    ]
    if missing_points:
        raise ValueError(
            "以下重规划知识点缺少评估证据："
            f"{missing_points}"
        )

    # TODO 3：
    # 按 decision.focus_points 的原始顺序返回对应证据。
    # 不能按字典顺序或分数顺序返回。
    return [
        evidence_map[knowledge_point]
        for knowledge_point in decision.focus_points
    ]


def build_supplemental_task(
    mastery: MasteryProfile,
    decision: ReplanDecision,
) -> LearningTask:
    """把重规划决定转换为可追溯的补充学习任务。"""
    if decision.action not in {
        "add_practice",
        "add_review",
    }:
        raise ValueError(
            "只有 add_practice 或 add_review "
            "决定才能生成补充任务"
        )

    focus_evidence = select_focus_evidence_for_replan(
        mastery,
        decision,
    )

    # 一个源文件可能同时支持多个知识点。
    # 用 dict 去重，并保留证据首次出现的顺序。
    source_points: dict[str, list[str]] = {}

    for evidence in focus_evidence:
        for source_file in evidence.source_files:
            related_points = source_points.setdefault(
                source_file,
                [],
            )
            if evidence.knowledge_point not in related_points:
                related_points.append(evidence.knowledge_point)

    evidence_sources = [
        EvidenceSource(
            file_path=source_file,
            evidence_type="source",
            reason=(
                "该文件为以下需加强知识点提供评估依据："
                f"{'、'.join(knowledge_points)}"
            ),
            confidence=1.0,
        )
        for source_file, knowledge_points
        in source_points.items()
    ]

    if not evidence_sources:
        raise ValueError(
            "补充任务必须至少对应一个源码证据"
        )

    focus_text = "、".join(decision.focus_points)

    if decision.action == "add_practice":
        title = f"补充实践：{focus_text}"
        objective = (
            "通过针对性编码实践加强知识点："
            f"{focus_text}"
        )
        practice_task = (
            f"围绕 {focus_text} 完成一个可运行的小练习，"
            "并补充自动化测试。"
        )
        action_criterion = "新增实践代码及测试能够通过"
    else:
        title = f"重点复习：{focus_text}"
        objective = (
            "基于真实源码重新理解薄弱知识点："
            f"{focus_text}"
        )
        practice_task = (
            f"先用自己的语言解释 {focus_text}，"
            "再画出它们在当前工作流中的关系。"
        )
        action_criterion = "能够指出每个知识点对应的源码位置"

    completion_criteria = [
        f"能够基于证据解释知识点：{knowledge_point}"
        for knowledge_point in decision.focus_points
    ]
    completion_criteria.append(action_criterion)

    return LearningTask(
        title=title,
        objective=objective,
        evidence_sources=evidence_sources,
        reading_task=(
            "重新阅读证据源码，记录以下知识点的"
            f"关键实现与数据流：{focus_text}"
        ),
        code_location_task=(
            "在证据文件中定位与以下知识点有关的"
            f"类、函数或路由：{focus_text}"
        ),
        practice_task=practice_task,
        completion_criteria=completion_criteria,
        estimated_hours=1.0,
    )
