"""9 月 3—4 日：目标 Issue 与可解释准备度。"""

from repo_mentor.contribution_analyzer import analyze_contribution_gap
from repo_mentor.contribution_models import TargetIssue
from repo_mentor.models import LearnerProfile
from repo_mentor.target_issue import review_target_issue_input


def make_issue() -> TargetIssue:
    return TargetIssue(
        title="补充配置加载测试",
        description="为配置文件加载失败场景增加 pytest 回归测试并更新说明。",
        labels=["python", "test", "docs"],
        expected_outcome="新增测试通过且文档说明与行为一致",
        deadline="2026-09-30",
        reference="手动粘贴的 Issue #42",
    )


def make_learner() -> LearnerProfile:
    return LearnerProfile(
        current_level="beginner",
        known_skills=["Python", "pytest"],
        unfamiliar_skills=["Git 贡献流程"],
        learning_goal="完成第一个文档和测试贡献",
        daily_hours=2,
        available_days=7,
    )


def test_missing_issue_description_requests_clarification():
    review = review_target_issue_input(
        {"title": "修复问题", "description": "太短", "expected_outcome": "测试通过"}
    )

    assert review.ready is False
    assert "description" in review.missing_fields
    assert review.issue is None


def test_valid_manual_issue_is_structured():
    raw = make_issue().model_dump(mode="json")
    review = review_target_issue_input(raw)

    assert review.ready is True
    assert review.issue == make_issue()


def test_readiness_is_sum_of_explainable_components():
    report = analyze_contribution_gap(make_issue(), make_learner())

    assert len(report.readiness_components) == 5
    assert report.readiness_score == round(
        sum(item.score for item in report.readiness_components), 2
    )
    assert sum(item.max_score for item in report.readiness_components) == 100
    assert "Python" in report.mastered_skills
    assert "自动化测试" in report.mastered_skills
    assert "Git 贡献流程" in report.missing_knowledge
    assert report.practice_tasks


def test_more_verified_skills_raise_readiness_deterministically():
    beginner = analyze_contribution_gap(make_issue(), make_learner())
    prepared_learner = make_learner().model_copy(
        update={
            "known_skills": [
                "Python",
                "pytest",
                "Git 贡献流程",
                "仓库代码定位",
                "技术文档写作",
                "文档结构",
                "配置文件",
            ]
        }
    )
    prepared = analyze_contribution_gap(make_issue(), prepared_learner)

    assert prepared.readiness_score > beginner.readiness_score
    assert prepared.missing_knowledge == []
