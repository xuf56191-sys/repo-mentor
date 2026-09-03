"""受限的 openEuler 本地贡献准备模式。"""

from __future__ import annotations

from pathlib import Path

from repo_mentor.contribution_models import (
    ContributionChecklistItem,
    ContributionGapAnalysis,
    OpenEulerContributionPlan,
    TargetIssue,
)
from repo_mentor.repository_reader import (
    read_repository_onboarding_docs,
    read_text_document,
)
from repo_mentor.repository_service import validate_repository_path
from repo_mentor.repository_tree import build_tree


COMMUNITY_CANDIDATES = (
    "COMMUNITY.md",
    "CODE_OF_CONDUCT.md",
    "OWNERS",
    "docs/community.md",
)


def build_openeuler_contribution_plan(
    repository_path: str | Path,
    issue: TargetIssue,
    gap: ContributionGapAnalysis,
) -> OpenEulerContributionPlan:
    """读取本地贡献资料并生成环境、规范和前置知识清单。"""
    repository = validate_repository_path(repository_path)
    target_issue = TargetIssue.model_validate(issue)
    analysis = ContributionGapAnalysis.model_validate(gap)
    if analysis.target_issue != target_issue:
        raise ValueError("贡献差距报告必须对应同一个 TargetIssue")

    onboarding = read_repository_onboarding_docs(repository.absolute_path)
    documents = [item.relative_path for item in onboarding.documents]
    document_types = {
        item.document_type: item.relative_path for item in onboarding.documents
    }
    tree = build_tree(
        repository.absolute_path,
        max_depth=4,
        max_files=300,
    )
    warnings = list(onboarding.warnings)
    community_path: str | None = None
    for candidate in COMMUNITY_CANDIDATES:
        try:
            community_document = read_text_document(
                repository.absolute_path,
                candidate,
                "community",
            )
        except ValueError as error:
            warnings.append(str(error))
            continue
        if community_document is not None:
            community_path = community_document.relative_path
            documents.append(community_path)
            break
    warnings.extend(tree.warnings)
    if tree.truncated:
        warnings.append(
            "仓库目录超过 300 个文件的受限扫描预算；"
            "请先选择与实习或 Issue 直接相关的小模块。"
        )

    contributing_path = document_types.get("contributing")
    metadata_path = document_types.get("project_metadata")
    checklist = [
        ContributionChecklistItem(
            category="environment",
            item="确认使用本地克隆并保留独立贡献分支。",
            source_path=None,
            status=("confirmed" if repository.has_git_metadata else "needs_confirmation"),
        ),
        ContributionChecklistItem(
            category="environment",
            item="从项目元数据确认依赖安装和测试命令。",
            source_path=metadata_path,
            status=("confirmed" if metadata_path else "needs_confirmation"),
        ),
        ContributionChecklistItem(
            category="standards",
            item="阅读仓库 CONTRIBUTING 并遵守提交、测试和 PR 规范。",
            source_path=contributing_path,
            status=("confirmed" if contributing_path else "needs_confirmation"),
        ),
        ContributionChecklistItem(
            category="standards",
            item="阅读本地社区行为或维护者说明。",
            source_path=community_path,
            status=("confirmed" if community_path else "needs_confirmation"),
        ),
        ContributionChecklistItem(
            category="standards",
            item="人工确认目标 Issue 所属 SIG、维护者意见和验收要求。",
            source_path=None,
            status="needs_confirmation",
        ),
    ]
    checklist.extend(
        ContributionChecklistItem(
            category="prerequisite",
            item=f"补足前置能力：{skill}",
            source_path=None,
            status="needs_confirmation",
        )
        for skill in analysis.missing_knowledge
    )
    checklist.extend(
        ContributionChecklistItem(
            category="prerequisite",
            item=f"已由学习画像支持：{skill}",
            source_path=None,
            status="confirmed",
        )
        for skill in analysis.mastered_skills
    )

    return OpenEulerContributionPlan(
        repository_name=repository.name,
        issue=target_issue,
        documents_read=documents,
        checklist=checklist,
        recommended_files=analysis.recommended_files,
        warnings=warnings,
        scope_statement=(
            "仅基于用户选择的本地小仓库、手动粘贴的目标 Issue "
            "和受控读取的贡献资料生成准备清单；"
            "不自动访问社区、不修改代码、不声称自动解决 Issue。"
        ),
    )
