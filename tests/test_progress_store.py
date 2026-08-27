"""SQLite 学习进度持久化层的单元测试。"""

from pathlib import Path
import sqlite3

import pytest

from repo_mentor.progress_store import SQLiteProgressStore
from repo_mentor.models import (
    DailyPlan,
    EvaluationResult,
    EvidenceSource,
    KnowledgeMasteryEvidence,
    LearnerProfile,
    LearningRoadmap,
    LearningTask,
    MasteryProfile,
    ReplanDecision,
    TargetTask,
)


SOURCE_PATH = "src/repo_mentor/adaptive_workflow.py"


def make_store(tmp_path: Path) -> SQLiteProgressStore:
    """为每个测试创建彼此隔离的数据库。"""
    return SQLiteProgressStore(
        tmp_path / "data" / "repo_mentor.db"
    )


def make_learner() -> LearnerProfile:
    return LearnerProfile(
        current_level="beginner",
        known_skills=["python"],
        unfamiliar_skills=["langgraph"],
        learning_goal="理解自适应工作流",
        daily_hours=2.0,
        available_days=7,
    )


def make_task(title: str) -> LearningTask:
    return LearningTask(
        title=title,
        objective="能够解释条件路由和状态更新",
        evidence_sources=[
            EvidenceSource(
                file_path=SOURCE_PATH,
                evidence_type="source",
                reason="该文件定义自适应工作流",
            ),
        ],
        reading_task="阅读自适应工作流源码",
        code_location_task="定位掌握度条件路由",
        practice_task="为分数边界增加测试",
        completion_criteria=["能解释三个分数区间"],
        estimated_hours=1.0,
    )


def make_roadmap(
    *,
    target_title: str = "理解自适应工作流",
) -> LearningRoadmap:
    learner = make_learner()
    target = TargetTask(
        title=target_title,
        description="理解评估、画像更新和重规划流程",
        task_type="understand_module",
        expected_outcome="能够解释完整学习闭环",
    )
    task = make_task("理解掌握度路由")

    return LearningRoadmap(
        learner_profile=learner,
        target_task=target,
        learner_summary="具备 Python 基础，需要学习 Agent 闭环",
        skill_gaps=["langgraph", "sqlite"],
        daily_plans=[
            DailyPlan(
                day=1,
                theme="掌握度闭环",
                tasks=[task],
                daily_outcome="能解释掌握度路由流程",
            ),
        ],
        total_estimated_hours=1.0,
    )


def make_result(
    *,
    score: int = 5,
) -> EvaluationResult:
    return EvaluationResult(
        item_id="question-routing",
        item_type="quiz_question",
        learner_response="条件路由根据分数决定下一步",
        status="evaluated",
        evaluation_method="rule",
        score=score,
        max_score=10,
        feedback="需要继续加强边界值理解",
        knowledge_points=["条件路由"],
        source_files=[SOURCE_PATH],
    )


def make_mastery(
    *,
    score: float = 0.5,
    status: str = "weak",
) -> MasteryProfile:
    result = make_result(score=round(score * 10))
    knowledge_point = "条件路由"

    return MasteryProfile(
        profile_id="mastery-persisted",
        target_task_title="理解自适应工作流",
        overall_score=score,
        knowledge_scores={knowledge_point: score},
        strengths=(
            [knowledge_point]
            if status == "mastered"
            else []
        ),
        weak_points=(
            [knowledge_point]
            if status == "weak"
            else []
        ),
        mastered_skills=(
            [knowledge_point]
            if status == "mastered"
            else []
        ),
        completed_tasks=[result.item_id],
        confidence=1.0,
        knowledge_evidence=[
            KnowledgeMasteryEvidence(
                knowledge_point=knowledge_point,
                score=score,
                status=status,
                assessment_item_ids=[result.item_id],
                source_files=[SOURCE_PATH],
            ),
        ],
        evaluation_results=[result],
    )


def make_decision() -> ReplanDecision:
    return ReplanDecision(
        action="add_review",
        overall_score=0.5,
        reason="掌握度低于 60%，需要先复习。",
        focus_points=["条件路由"],
        replan_count=0,
        max_replans=1,
    )


def test_first_run_creates_repository_table(
    tmp_path: Path,
):
    """首次实例化应自动创建数据库和表。"""
    store = make_store(tmp_path)

    assert store.database_path.exists()

    with store._session() as connection:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'repositories'
            """
        ).fetchone()
        foreign_keys_enabled = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

    assert row["name"] == "repositories"
    assert foreign_keys_enabled == 1


def test_register_repository_is_idempotent(
    tmp_path: Path,
):
    """同一规范路径重复注册应返回同一个 ID。"""
    store = make_store(tmp_path)
    repository = tmp_path / "demo-repository"

    first_id = store.register_repository(repository)
    second_id = store.register_repository(repository)

    with store._session() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM repositories"
        ).fetchone()[0]

    assert first_id == second_id
    assert count == 1


def test_different_repositories_are_isolated(
    tmp_path: Path,
):
    """不同仓库路径必须获得不同的隔离 ID。"""
    store = make_store(tmp_path)

    first_id = store.register_repository(
        tmp_path / "repository-a"
    )
    second_id = store.register_repository(
        tmp_path / "repository-b"
    )

    assert first_id != second_id

    with store._session() as connection:
        rows = connection.execute(
            """
            SELECT repository_id, canonical_path
            FROM repositories
            ORDER BY repository_id
            """
        ).fetchall()

    assert len(rows) == 2
    assert rows[0]["canonical_path"] != (
        rows[1]["canonical_path"]
    )


def test_register_repository_rejects_empty_path(
    tmp_path: Path,
):
    """空路径不能被注册成当前工作目录。"""
    store = make_store(tmp_path)

    with pytest.raises(
        ValueError,
        match="repository_path 不能为空",
    ):
        store.register_repository("   ")


def test_first_run_creates_complete_progress_schema(
    tmp_path: Path,
):
    """五张业务表应在首次运行时一次创建。"""
    store = make_store(tmp_path)

    with store._session() as connection:
        table_names = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

    assert {
        "repositories",
        "learner_profiles",
        "plans",
        "tasks",
        "assessment_results",
    } <= table_names


def test_progress_survives_store_restart(
    tmp_path: Path,
):
    """重新创建 Store 后仍能恢复路线、薄弱点和评估。"""
    database_path = (
        tmp_path / "data" / "repo_mentor.db"
    )
    repository_path = tmp_path / "repository-a"
    first_store = SQLiteProgressStore(database_path)
    supplemental_task = make_task(
        "重点复习：条件路由"
    )

    plan_id = first_store.save_progress(
        repository_path=repository_path,
        learner_profile=make_learner(),
        roadmap=make_roadmap(),
        mastery=make_mastery(),
        replan_decision=make_decision(),
        supplemental_tasks=[supplemental_task],
        assessment_results=[make_result()],
    )

    # 用同一数据库文件构造新对象，
    # 模拟 Python 进程重启后重新打开。
    reopened_store = SQLiteProgressStore(
        database_path
    )
    restored = reopened_store.load_latest_progress(
        repository_path
    )

    assert restored is not None
    assert restored.plan_id == plan_id
    assert restored.roadmap.target_task.title == (
        "理解自适应工作流"
    )
    assert restored.mastery is not None
    assert restored.mastery.weak_points == [
        "条件路由",
    ]
    assert restored.replan_decision is not None
    assert restored.replan_decision.action == "add_review"
    assert restored.supplemental_tasks == [
        supplemental_task,
    ]
    assert restored.assessment_results[0].item_id == (
        "question-routing"
    )
    assert restored.saved_at


def test_saved_tasks_and_results_are_queryable(
    tmp_path: Path,
):
    """路线任务、补充任务和评估结果应独立落表。"""
    store = make_store(tmp_path)
    plan_id = store.save_progress(
        repository_path=tmp_path / "repository-a",
        learner_profile=make_learner(),
        roadmap=make_roadmap(),
        mastery=make_mastery(),
        supplemental_tasks=[
            make_task("重点复习：条件路由"),
        ],
        assessment_results=[make_result()],
    )

    with store._session() as connection:
        task_rows = connection.execute(
            """
            SELECT task_kind, task_order
            FROM tasks
            WHERE plan_id = ?
            ORDER BY task_kind, task_order
            """,
            (plan_id,),
        ).fetchall()
        result_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM assessment_results
            WHERE plan_id = ?
            """,
            (plan_id,),
        ).fetchone()[0]

    assert {
        row["task_kind"]
        for row in task_rows
    } == {"roadmap", "supplemental"}
    assert len(task_rows) == 2
    assert result_count == 1


def test_repository_progress_is_isolated(
    tmp_path: Path,
):
    """一个仓库不能恢复到另一个仓库的路线。"""
    store = make_store(tmp_path)
    repository_a = tmp_path / "repository-a"
    repository_b = tmp_path / "repository-b"

    store.save_progress(
        repository_path=repository_a,
        learner_profile=make_learner(),
        roadmap=make_roadmap(
            target_title="理解仓库 A"
        ),
    )
    store.save_progress(
        repository_path=repository_b,
        learner_profile=make_learner(),
        roadmap=make_roadmap(
            target_title="理解仓库 B"
        ),
    )

    restored_a = store.load_latest_progress(
        repository_a
    )
    restored_b = store.load_latest_progress(
        repository_b
    )

    assert restored_a is not None
    assert restored_b is not None
    assert restored_a.repository_id != (
        restored_b.repository_id
    )
    assert restored_a.roadmap.target_task.title == (
        "理解仓库 A"
    )
    assert restored_b.roadmap.target_task.title == (
        "理解仓库 B"
    )


def test_failed_progress_save_rolls_back_child_rows(
    tmp_path: Path,
):
    """重复结果导致失败时，plan 和 tasks 不能残留。"""
    store = make_store(tmp_path)
    duplicate_result = make_result()

    with pytest.raises(sqlite3.IntegrityError):
        store.save_progress(
            repository_path=tmp_path / "repository-a",
            learner_profile=make_learner(),
            roadmap=make_roadmap(),
            assessment_results=[
                duplicate_result,
                duplicate_result,
            ],
        )

    with store._session() as connection:
        plan_count = connection.execute(
            "SELECT COUNT(*) FROM plans"
        ).fetchone()[0]
        task_count = connection.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]
        result_count = connection.execute(
            "SELECT COUNT(*) FROM assessment_results"
        ).fetchone()[0]

    assert plan_count == 0
    assert task_count == 0
    assert result_count == 0
