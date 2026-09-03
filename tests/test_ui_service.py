"""9 月 7—8 日：Streamlit 背后的离线应用服务。"""

from pathlib import Path

from repo_mentor.contribution_models import TargetIssue
from repo_mentor.models import LearnerProfile
from repo_mentor.progress_store import SQLiteProgressStore
from repo_mentor.ui_service import (
    analyze_ui_request,
    evaluate_ui_answers,
    save_ui_progress,
)


def make_repository(root: Path) -> Path:
    (root / ".git").mkdir(parents=True)
    (root / "README.md").write_text(
        "# Demo\nRun pytest before contribution.", encoding="utf-8"
    )
    (root / "CONTRIBUTING.md").write_text(
        "Create a branch and run pytest.", encoding="utf-8"
    )
    (root / "config_loader.py").write_text(
        "def load_config(path):\n    return path\n", encoding="utf-8"
    )
    (root / "test_config_loader.py").write_text(
        "def test_load_config():\n    assert True\n", encoding="utf-8"
    )
    return root


def make_inputs() -> tuple[LearnerProfile, TargetIssue]:
    learner = LearnerProfile(
        current_level="beginner",
        known_skills=["Python", "pytest"],
        learning_goal="完成第一个测试贡献",
        daily_hours=2,
        available_days=5,
    )
    issue = TargetIssue(
        title="补充配置加载测试",
        description="为配置加载失败路径增加 pytest 回归测试和使用说明。",
        labels=["python", "test", "docs"],
        expected_outcome="新增测试通过且文档说明可执行",
    )
    return learner, issue


def test_ui_analysis_reuses_evidence_for_route_assessment_and_gap(tmp_path: Path):
    repository = make_repository(tmp_path)
    learner, issue = make_inputs()

    bundle = analyze_ui_request(repository, learner, issue)

    assert bundle.evidence_layer.chunks
    assert bundle.roadmap.daily_plans
    assert len(bundle.assessment.questions) == 2
    assert bundle.gap.readiness_components
    assert bundle.contribution_plan.mode == "openEuler"


def test_ui_evaluation_and_sqlite_progress_are_readable(tmp_path: Path):
    repository = make_repository(tmp_path / "repo")
    learner, issue = make_inputs()
    bundle = analyze_ui_request(repository, learner, issue)
    location = next(
        question
        for question in bundle.assessment.questions
        if question.question_type == "code_location"
    )
    answers = {
        location.question_id: location.expected_answer,
        bundle.assessment.practice_task.practice_id: "已提交测试输出",
    }

    results, mastery = evaluate_ui_answers(bundle, answers)

    assert len(results) == 3
    assert results[1].score == results[1].max_score
    assert results[2].status == "needs_human_review"
    database = tmp_path / "progress.db"
    plan_id = save_ui_progress(
        database, repository, bundle, results, mastery
    )
    restored = SQLiteProgressStore(database).load_latest_progress(
        repository, profile_key="streamlit-user"
    )

    assert plan_id > 0
    assert restored is not None
    assert restored.plan_id == plan_id
    assert restored.mastery == mastery
    assert restored.assessment_results == results


def test_app_module_import_does_not_require_streamlit():
    import app

    assert callable(app.main)
