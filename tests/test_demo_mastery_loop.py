"""V0.7 离线学习闭环演示的冒烟测试。"""

from pathlib import Path

from repo_mentor.demo_mastery_loop import run_demo


def test_demo_persists_and_restores_adjusted_plan(
    tmp_path: Path,
):
    restored = run_demo(
        tmp_path / "repo_mentor_progress.db"
    )

    assert restored.mastery is not None
    assert restored.mastery.weak_points
    assert restored.replan_decision is not None
    assert restored.replan_decision.action == "add_review"
    assert len(restored.supplemental_tasks) == 1
