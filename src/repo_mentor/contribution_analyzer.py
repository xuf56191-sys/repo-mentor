"""把目标 Issue 映射为可解释的贡献能力差距和准备度。"""

from __future__ import annotations

import re

from repo_mentor.contribution_models import (
    ContributionGapAnalysis,
    ReadinessComponent,
    TargetIssue,
)
from repo_mentor.learning_evidence import retrieval_context_from_chunks
from repo_mentor.models import (
    EvidenceSource,
    LearnerProfile,
    MasteryProfile,
)
from repo_mentor.retrieval_models import DocumentChunk


SKILL_RULES = (
    (("docs", "documentation", "文档", "readme"), ("技术文档写作", "文档结构")),
    (("bug", "fix", "错误", "修复"), ("调试", "自动化测试")),
    (("test", "pytest", "测试"), ("自动化测试",)),
    (("python", ".py"), ("Python",)),
    (("api", "接口"), ("接口设计", "自动化测试")),
    (("config", "yaml", "toml", "配置"), ("配置文件",)),
)


def _normalize(value: str) -> str:
    return re.sub(r"[\s_\-]+", "", value).casefold()


def infer_required_skills(issue: TargetIssue) -> list[str]:
    """用公开规则从 Issue 文本推导能力要求。"""
    text = " ".join(
        [issue.title, issue.description, issue.expected_outcome, *issue.labels]
    ).casefold()
    required = ["Git 贡献流程", "仓库代码定位", "自动化测试"]
    for markers, skills in SKILL_RULES:
        if any(marker.casefold() in text for marker in markers):
            required.extend(skills)
    return list(dict.fromkeys(required))


def _verified_skills(
    learner: LearnerProfile,
    mastery: MasteryProfile | None,
) -> list[str]:
    skills = list(learner.known_skills)
    if mastery is not None:
        skills.extend(mastery.mastered_skills)
        skills.extend(
            point
            for point, score in mastery.knowledge_scores.items()
            if score >= 0.8
        )
    return list(dict.fromkeys(skill for skill in skills if skill.strip()))


def _is_skill_covered(required: str, verified: list[str]) -> bool:
    required_key = _normalize(required)
    aliases = {
        "git贡献流程": ("git", "贡献流程", "pullrequest", "pr"),
        "仓库代码定位": ("代码定位", "仓库阅读", "codereading"),
        "自动化测试": ("测试", "pytest", "unittest"),
        "技术文档写作": ("文档", "markdown", "technicalwriting"),
        "文档结构": ("文档", "markdown", "documentation"),
        "调试": ("debug", "调试"),
        "python": ("python",),
        "接口设计": ("api", "接口"),
        "配置文件": ("配置", "yaml", "toml"),
    }
    candidates = (required_key, *aliases.get(required_key, ()))
    for skill in verified:
        skill_key = _normalize(skill)
        if any(
            candidate in skill_key or skill_key in candidate
            for candidate in candidates
            if candidate
        ):
            return True
    return False


def _recommended_files(
    issue: TargetIssue,
    retrieval_chunks: list[DocumentChunk],
) -> list[EvidenceSource]:
    if not retrieval_chunks:
        return []
    query = " ".join(
        [issue.title, issue.description, issue.expected_outcome, *issue.labels]
    )
    _, evidence = retrieval_context_from_chunks(
        retrieval_chunks,
        query,
        top_k=5,
    )
    return [
        EvidenceSource(
            file_path=item.source_path,
            evidence_type=(
                "test"
                if "/test" in item.source_path.casefold()
                or item.source_path.casefold().startswith("tests/")
                else "source"
            ),
            reason=item.reason,
            excerpt=item.snippet,
            confidence=item.confidence,
        )
        for item in evidence
    ]


def _clarity_score(issue: TargetIssue) -> float:
    return round(
        4.0
        + 8.0 * min(1.0, len(issue.description) / 80)
        + 6.0 * min(1.0, len(issue.expected_outcome) / 40)
        + (2.0 if issue.labels else 0.0),
        2,
    )


def analyze_contribution_gap(
    issue: TargetIssue,
    learner: LearnerProfile,
    *,
    mastery: MasteryProfile | None = None,
    retrieval_chunks: list[DocumentChunk] | None = None,
) -> ContributionGapAnalysis:
    """使用确定性公式分析差距；模型不能随意给百分比。"""
    target_issue = TargetIssue.model_validate(issue)
    profile = LearnerProfile.model_validate(learner)
    verified = _verified_skills(profile, mastery)
    required = infer_required_skills(target_issue)
    mastered = [
        skill for skill in required if _is_skill_covered(skill, verified)
    ]
    missing = [skill for skill in required if skill not in mastered]
    files = _recommended_files(target_issue, list(retrieval_chunks or []))

    clarity = _clarity_score(target_issue)
    skill_score = round(35.0 * len(mastered) / len(required), 2)
    evidence_score = round(25.0 * min(len(files), 3) / 3, 2)
    testing_score = 10.0 if "自动化测试" in mastered else 0.0
    workflow_score = 10.0 if "Git 贡献流程" in mastered else 0.0
    components = [
        ReadinessComponent(
            category="issue_clarity",
            score=clarity,
            max_score=20,
            rationale="由标题、描述、验收结果和 labels 的完整度计算。",
        ),
        ReadinessComponent(
            category="skill_coverage",
            score=skill_score,
            max_score=35,
            rationale=f"已覆盖 {len(mastered)}/{len(required)} 项目标能力。",
        ),
        ReadinessComponent(
            category="evidence_coverage",
            score=evidence_score,
            max_score=25,
            rationale=f"找到 {len(files)} 个与 Issue 对应的本地来源。",
        ),
        ReadinessComponent(
            category="testing_readiness",
            score=testing_score,
            max_score=10,
            rationale="只有已验证的测试能力才得分。",
        ),
        ReadinessComponent(
            category="workflow_readiness",
            score=workflow_score,
            max_score=10,
            rationale="只有已验证的 Git/贡献流程能力才得分。",
        ),
    ]
    total = round(sum(item.score for item in components), 2)
    if total >= 80:
        interpretation = "已具备在维护者复核下尝试该 Issue 的准备度。"
    elif total >= 60:
        interpretation = "可先完成推荐实践，再在指导下尝试该 Issue。"
    else:
        interpretation = "应先补足关键知识和仓库证据，不建议直接开始修改。"

    return ContributionGapAnalysis(
        target_issue=target_issue,
        required_skills=required,
        mastered_skills=mastered,
        missing_knowledge=missing,
        recommended_files=files,
        practice_tasks=[
            f"围绕“{skill}”完成一个可验证的小练习，并保存测试或说明。"
            for skill in missing
        ],
        readiness_components=components,
        readiness_score=total,
        interpretation=interpretation,
    )
