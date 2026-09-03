"""目标 Issue 表单检查与严格转换。"""

from __future__ import annotations

from typing import Any

from repo_mentor.contribution_models import TargetIssue, TargetIssueReview


def review_target_issue_input(raw: dict[str, Any]) -> TargetIssueReview:
    """提示关键缺失项；只处理用户手动提供的信息。"""
    title = str(raw.get("title") or "").strip()
    description = str(raw.get("description") or "").strip()
    outcome = str(raw.get("expected_outcome") or "").strip()

    missing: list[str] = []
    questions: list[str] = []
    if len(title) < 2:
        missing.append("title")
        questions.append("请提供目标 Issue 的标题（至少 2 个字符）。")
    if len(description) < 10:
        missing.append("description")
        questions.append(
            "请粘贴更完整的 Issue 描述，包括现状、问题和影响（至少 10 个字符）。"
        )
    if len(outcome) < 5:
        missing.append("expected_outcome")
        questions.append("请说明该 Issue 验收时应看到的具体结果。")

    if missing:
        return TargetIssueReview(
            ready=False,
            missing_fields=missing,
            clarification_questions=questions,
        )

    return TargetIssueReview(
        ready=True,
        issue=TargetIssue.model_validate(raw),
    )
