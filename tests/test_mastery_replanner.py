"""掌握度驱动重规划的单元测试。"""

import pytest

from repo_mentor.mastery_replanner import (
    build_supplemental_task,
    decide_replan,
    select_focus_evidence_for_replan,
)
from repo_mentor.models import (
    KnowledgeMasteryEvidence,
    MasteryProfile,
    ReplanDecision,
)


def make_evidence(
    knowledge_point: str,
    score: float,
    status: str,
    source_file: str = "src/repo_mentor/adaptive_workflow.py",
) -> KnowledgeMasteryEvidence:
    """创建一条可追溯的知识点掌握证据。"""
    return KnowledgeMasteryEvidence(
        knowledge_point=knowledge_point,
        score=score,
        status=status,
        assessment_item_ids=[
            f"question-{knowledge_point}",
        ],
        source_files=[source_file],
    )


def make_mastery(
    overall_score: float,
    evidence_items: list[KnowledgeMasteryEvidence],
) -> MasteryProfile:
    """创建供重规划测试使用的掌握度画像。"""
    return MasteryProfile(
        profile_id="mastery-replan-test",
        target_task_title="理解自适应工作流",
        overall_score=overall_score,
        knowledge_scores={
            item.knowledge_point: item.score
            for item in evidence_items
        },
        strengths=[
            item.knowledge_point
            for item in evidence_items
            if item.status == "mastered"
        ],
        weak_points=[
            item.knowledge_point
            for item in evidence_items
            if item.status == "weak"
        ],
        mastered_skills=[
            item.knowledge_point
            for item in evidence_items
            if item.status == "mastered"
        ],
        knowledge_evidence=evidence_items,
    )


@pytest.mark.parametrize(
    (
        "score",
        "status",
        "expected_action",
    ),
    [
        (0.80, "mastered", "advance"),
        (0.79, "developing", "add_practice"),
        (0.60, "developing", "add_practice"),
        (0.59, "weak", "add_review"),
    ],
)
def test_decide_replan_uses_score_thresholds(
    score: float,
    status: str,
    expected_action: str,
):
    """80%、60% 两个边界值必须归入正确区间。"""
    mastery = make_mastery(
        score,
        [
            make_evidence(
                "条件路由",
                score,
                status,
            ),
        ],
    )

    decision = decide_replan(
        mastery,
        replan_count=0,
        max_replans=1,
    )

    assert decision.action == expected_action
    assert decision.overall_score == score


def test_practice_targets_developing_and_weak_points():
    """中间分数段应针对发展中和薄弱知识点补充实践。"""
    mastery = make_mastery(
        0.70,
        [
            make_evidence(
                "条件路由",
                0.70,
                "developing",
            ),
            make_evidence(
                "状态更新",
                0.50,
                "weak",
                "src/repo_mentor/workflow_state.py",
            ),
            make_evidence(
                "节点注册",
                0.90,
                "mastered",
            ),
        ],
    )

    decision = decide_replan(
        mastery,
        replan_count=0,
        max_replans=1,
    )

    assert decision.action == "add_practice"
    assert decision.focus_points == [
        "条件路由",
        "状态更新",
    ]


def test_review_prioritizes_only_weak_points():
    """低分段的复习任务应优先对应 weak 知识点。"""
    mastery = make_mastery(
        0.50,
        [
            make_evidence(
                "条件路由",
                0.65,
                "developing",
            ),
            make_evidence(
                "循环终止条件",
                0.40,
                "weak",
                "src/repo_mentor/adaptive_nodes.py",
            ),
        ],
    )

    decision = decide_replan(
        mastery,
        replan_count=0,
        max_replans=1,
    )

    assert decision.action == "add_review"
    assert decision.focus_points == [
        "循环终止条件",
    ]


def test_replan_stops_after_reaching_limit():
    """已经重新规划一次后，不允许再次添加补充任务。"""
    mastery = make_mastery(
        0.70,
        [
            make_evidence(
                "条件路由",
                0.70,
                "developing",
            ),
        ],
    )

    decision = decide_replan(
        mastery,
        replan_count=1,
        max_replans=1,
    )

    assert decision.action == "stop"
    assert decision.focus_points == []


def test_advance_is_allowed_after_replan_limit():
    """次数上限只限制再次重规划，不能阻止正常前进。"""
    mastery = make_mastery(
        0.80,
        [
            make_evidence(
                "条件路由",
                0.80,
                "mastered",
            ),
        ],
    )

    decision = decide_replan(
        mastery,
        replan_count=1,
        max_replans=1,
    )

    assert decision.action == "advance"


def test_replan_stops_without_traceable_evidence():
    """没有知识点证据时不能凭空生成补充任务。"""
    mastery = make_mastery(
        0.50,
        [],
    )

    decision = decide_replan(
        mastery,
        replan_count=0,
        max_replans=1,
    )

    assert decision.action == "stop"
    assert "证据" in decision.reason


def test_focus_evidence_preserves_decision_order():
    """证据顺序应由重规划优先级决定。"""
    mastery = make_mastery(
        0.70,
        [
            make_evidence(
                "条件路由",
                0.70,
                "developing",
            ),
            make_evidence(
                "状态更新",
                0.50,
                "weak",
                "src/repo_mentor/workflow_state.py",
            ),
        ],
    )
    decision = ReplanDecision(
        action="add_practice",
        overall_score=0.70,
        reason="先加强得分更低的知识点。",
        focus_points=["状态更新", "条件路由"],
        replan_count=0,
        max_replans=1,
    )

    selected = select_focus_evidence_for_replan(
        mastery,
        decision,
    )

    assert [
        item.knowledge_point
        for item in selected
    ] == ["状态更新", "条件路由"]


def test_focus_evidence_rejects_untraceable_point():
    """没有评估证据的知识点不能进入补充任务。"""
    mastery = make_mastery(
        0.70,
        [
            make_evidence(
                "条件路由",
                0.70,
                "developing",
            ),
        ],
    )
    decision = ReplanDecision(
        action="add_practice",
        overall_score=0.70,
        reason="需要增加针对性编码实践。",
        focus_points=["不存在的知识点"],
        replan_count=0,
        max_replans=1,
    )

    with pytest.raises(
        ValueError,
        match="缺少评估证据",
    ):
        select_focus_evidence_for_replan(
            mastery,
            decision,
        )


def test_practice_task_is_traceable_to_focus_points():
    """补充实践应对应薄弱点，并对重复源文件去重。"""
    shared_source = "src/repo_mentor/adaptive_workflow.py"
    mastery = make_mastery(
        0.70,
        [
            make_evidence(
                "条件路由",
                0.70,
                "developing",
                shared_source,
            ),
            make_evidence(
                "节点连边",
                0.50,
                "weak",
                shared_source,
            ),
        ],
    )
    decision = decide_replan(
        mastery,
        replan_count=0,
        max_replans=1,
    )

    task = build_supplemental_task(
        mastery,
        decision,
    )

    assert task.title == "补充实践：条件路由、节点连边"
    assert len(task.evidence_sources) == 1
    assert task.evidence_sources[0].file_path == shared_source
    assert "条件路由" in task.evidence_sources[0].reason
    assert "节点连边" in task.evidence_sources[0].reason
    assert "自动化测试" in task.practice_task


def test_review_task_uses_weak_point_and_source_file():
    """低分段应生成对应 weak 知识点的复习任务。"""
    source_file = "src/repo_mentor/adaptive_nodes.py"
    mastery = make_mastery(
        0.50,
        [
            make_evidence(
                "循环终止条件",
                0.40,
                "weak",
                source_file,
            ),
        ],
    )
    decision = decide_replan(
        mastery,
        replan_count=0,
        max_replans=1,
    )

    task = build_supplemental_task(
        mastery,
        decision,
    )

    assert task.title == "重点复习：循环终止条件"
    assert task.evidence_sources[0].file_path == source_file
    assert "自己的语言" in task.practice_task


def test_advance_cannot_create_supplemental_task():
    """advance 只表示前进，不应生成补充任务。"""
    mastery = make_mastery(
        0.80,
        [
            make_evidence(
                "条件路由",
                0.80,
                "mastered",
            ),
        ],
    )
    decision = decide_replan(
        mastery,
        replan_count=0,
        max_replans=1,
    )

    with pytest.raises(
        ValueError,
        match="才能生成补充任务",
    ):
        build_supplemental_task(
            mastery,
            decision,
        )
