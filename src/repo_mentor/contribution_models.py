"""V0.9/V1.0 Issue 驱动贡献准备的严格数据模型。"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from repo_mentor.models import EvidenceSource, StrictModel


class TargetIssue(StrictModel):
    """用户手动粘贴的目标 Issue；不承诺自动修复。"""

    title: str = Field(min_length=2)
    description: str = Field(min_length=10)
    labels: list[str] = Field(default_factory=list)
    expected_outcome: str = Field(min_length=5)
    deadline: date | None = None
    reference: str | None = None


class TargetIssueReview(StrictModel):
    """把宽松表单输入转换为严格 Issue 前的检查结果。"""

    ready: bool
    issue: TargetIssue | None = None
    missing_fields: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_review(self) -> "TargetIssueReview":
        if self.ready != (self.issue is not None):
            raise ValueError("ready 必须与 issue 是否存在保持一致")
        if self.ready and self.missing_fields:
            raise ValueError("已就绪的 Issue 不能仍有缺失字段")
        return self


ReadinessCategory = Literal[
    "issue_clarity",
    "skill_coverage",
    "evidence_coverage",
    "testing_readiness",
    "workflow_readiness",
]


class ReadinessComponent(StrictModel):
    """准备度的一个可解释、可复算组成项。"""

    category: ReadinessCategory
    score: float = Field(ge=0.0)
    max_score: float = Field(gt=0.0)
    rationale: str = Field(min_length=5)

    @model_validator(mode="after")
    def validate_score(self) -> "ReadinessComponent":
        if self.score > self.max_score:
            raise ValueError("组成项得分不能超过满分")
        return self


class ContributionGapAnalysis(StrictModel):
    """目标 Issue 对应的能力差距与准备度报告。"""

    target_issue: TargetIssue
    required_skills: list[str] = Field(min_length=1)
    mastered_skills: list[str] = Field(default_factory=list)
    missing_knowledge: list[str] = Field(default_factory=list)
    recommended_files: list[EvidenceSource] = Field(default_factory=list)
    practice_tasks: list[str] = Field(default_factory=list)
    readiness_components: list[ReadinessComponent] = Field(min_length=5)
    readiness_score: float = Field(ge=0.0, le=100.0)
    interpretation: str = Field(min_length=5)

    @model_validator(mode="after")
    def validate_readiness_total(self) -> "ContributionGapAnalysis":
        categories = [item.category for item in self.readiness_components]
        if len(categories) != len(set(categories)):
            raise ValueError("准备度组成项类别不能重复")
        calculated = round(sum(item.score for item in self.readiness_components), 2)
        if abs(calculated - self.readiness_score) > 0.01:
            raise ValueError("readiness_score 必须等于组成项得分之和")
        if round(sum(item.max_score for item in self.readiness_components), 2) != 100.0:
            raise ValueError("准备度组成项满分之和必须为 100")
        return self


ChecklistCategory = Literal[
    "environment",
    "standards",
    "prerequisite",
]


class ContributionChecklistItem(StrictModel):
    category: ChecklistCategory
    item: str = Field(min_length=3)
    source_path: str | None = None
    status: Literal["confirmed", "needs_confirmation"]


class OpenEulerContributionPlan(StrictModel):
    """本地、手动资料驱动的 openEuler 贡献准备清单。"""

    mode: Literal["openEuler"] = "openEuler"
    repository_name: str = Field(min_length=1)
    issue: TargetIssue
    documents_read: list[str] = Field(default_factory=list)
    checklist: list[ContributionChecklistItem] = Field(min_length=1)
    recommended_files: list[EvidenceSource] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    scope_statement: str = Field(min_length=10)
