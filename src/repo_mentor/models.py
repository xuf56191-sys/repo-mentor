"""RepoMentor核心数据模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TaskType = Literal[
    "understand_module",
    "learn_technology",
    "add_feature",
    "add_test",
    "update_docs",
    "solve_issue",
    "other",
]

EvidenceType = Literal[
    "readme",
    "directory",
    "source",
    "test",
    "config",
    "contributing",
    "docs",
]


class StrictModel(BaseModel):
    """RepoMentor严格数据模型基类。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class LearnerProfile(StrictModel):
    """学习者的基础、目标和时间信息。"""

    current_level: str = Field(
        min_length=2,
        description="用户当前技术水平",
    )
    known_skills: list[str] = Field(
        default_factory=list,
        description="用户已经掌握的技能",
    )
    unfamiliar_skills: list[str] = Field(
        default_factory=list,
        description="用户尚不熟悉的技能",
    )
    learning_goal: str = Field(
        min_length=2,
        description="用户希望达到的学习目标",
    )
    daily_hours: float = Field(
        ge=0.5,
        le=12,
        description="用户每天可投入的学习时间",
    )
    available_days: int = Field(
        ge=1,
        le=90,
        description="本次计划可使用的天数",
    )


class TargetTask(StrictModel):
    """用户希望完成的具体学习或贡献任务。"""

    title: str = Field(
        min_length=2,
        description="目标任务标题",
    )
    description: str = Field(
        min_length=5,
        description="目标任务详细说明",
    )
    task_type: TaskType = Field(
        description="目标任务类型",
    )
    expected_outcome: str = Field(
        min_length=5,
        description="完成任务后应达到的结果",
    )
    reference: str | None = Field(
        default=None,
        description="可选的Issue、文档或其他参考信息",
    )


class EvidenceSource(StrictModel):
    """学习任务所依据的仓库证据。"""

    file_path: str = Field(
        min_length=1,
        description="仓库中的真实文件路径",
    )
    evidence_type: EvidenceType = Field(
        description="证据类型",
    )
    reason: str = Field(
        min_length=3,
        description="该文件与学习任务相关的原因",
    )
    excerpt: str | None = Field(
        default=None,
        description="可选的仓库内容片段",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="当前证据可信度",
    )


class LearningTask(StrictModel):
    """一项可以执行和验收的学习任务。"""

    title: str = Field(
        min_length=2,
        description="任务标题",
    )
    objective: str = Field(
        min_length=5,
        description="任务学习目标",
    )
    evidence_sources: list[EvidenceSource] = Field(
        min_length=1,
        description="支持该任务的仓库证据",
    )
    reading_task: str = Field(
        min_length=5,
        description="具体阅读任务",
    )
    code_location_task: str = Field(
        min_length=5,
        description="代码定位任务",
    )
    practice_task: str = Field(
        min_length=5,
        description="小型实践任务",
    )
    completion_criteria: list[str] = Field(
        min_length=1,
        description="可验证的完成标准",
    )
    estimated_hours: float = Field(
        ge=0.5,
        le=12,
        description="预计完成时间",
    )


class DailyPlan(StrictModel):
    """一天的学习安排。"""

    day: int = Field(
        ge=1,
        description="学习计划中的第几天",
    )
    theme: str = Field(
        min_length=2,
        description="当天学习主题",
    )
    tasks: list[LearningTask] = Field(
        min_length=1,
        description="当天学习任务",
    )
    daily_outcome: str = Field(
        min_length=5,
        description="当天完成后应该达到的结果",
    )


class LearningRoadmap(StrictModel):
    """RepoMentor生成的完整学习路线。"""

    learner_profile: LearnerProfile
    target_task: TargetTask

    learner_summary: str = Field(
        min_length=5,
        description="对学习者当前能力的总结",
    )
    skill_gaps: list[str] = Field(
        description="为了完成目标仍然缺少的能力",
    )
    daily_plans: list[DailyPlan] = Field(
        min_length=1,
        description="每日学习计划",
    )
    risks_and_uncertainties: list[str] = Field(
        default_factory=list,
        description="风险和无法从当前仓库确认的信息",
    )
    total_estimated_hours: float = Field(
        ge=0.5,
        description="整份路线预计总时间",
    )