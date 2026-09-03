"""9 月 5 日：openEuler 本地小仓库贡献模式。"""

from pathlib import Path

from repo_mentor.contribution_analyzer import analyze_contribution_gap
from repo_mentor.contribution_models import TargetIssue
from repo_mentor.models import LearnerProfile
from repo_mentor.openeuler_mode import build_openeuler_contribution_plan


def test_mode_reads_local_contributing_and_builds_checklist(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "README.md").write_text("# small repo", encoding="utf-8")
    (tmp_path / "CONTRIBUTING.md").write_text(
        "Run pytest before opening a pull request.", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='small-openeuler-demo'", encoding="utf-8"
    )
    (tmp_path / "OWNERS").write_text(
        "maintainers:\n  - demo-maintainer", encoding="utf-8"
    )
    issue = TargetIssue(
        title="补充文档测试",
        description="为当前小仓库补充贡献文档的测试说明和验收步骤。",
        labels=["docs", "test"],
        expected_outcome="文档步骤可执行且测试通过",
    )
    learner = LearnerProfile(
        current_level="beginner",
        known_skills=["Python", "pytest"],
        learning_goal="尝试第一个贡献",
        daily_hours=2,
        available_days=5,
    )
    gap = analyze_contribution_gap(issue, learner)

    plan = build_openeuler_contribution_plan(tmp_path, issue, gap)

    assert plan.mode == "openEuler"
    assert "CONTRIBUTING.md" in plan.documents_read
    assert "OWNERS" in plan.documents_read
    assert any(
        item.category == "standards"
        and item.source_path == "CONTRIBUTING.md"
        and item.status == "confirmed"
        for item in plan.checklist
    )
    assert "不修改代码" in plan.scope_statement
    assert "自动解决 Issue" in plan.scope_statement
