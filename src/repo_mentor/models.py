"""RepoMentor核心数据模型。"""

from __future__ import annotations

#限制变量只能填写指定的几个固定字符串 / 数值，不能随便乱写。
from typing import Any, Literal


#Pydantic 是 Python 最常用数据校验、结构化数据工具（LLM 项目标配，用来规范大模型输出 JSON）
#BaseModel基础模型类。新建类继承它，就能实现：自动类型校验字典 ↔ 对象互相转换自动解析 JSON 字符串
#Field给字段附加规则、默认值、注释、描述。
#ConfigDict：给整个模型设置全局配置。
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


TaskType = Literal[
    "understand_module",
    "learn_technology",
    "add_feature",
    "add_test",
    "update_docs",
    "solve_issue",
    "other",
]

KnowledgeMasteryStatus = Literal[
    "mastered",
    "developing",
    "weak",
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

QuizQuestionType = Literal[
    "concept",
    "code_location",
]

AssessmentDifficulty = Literal[
    "beginner",
    "intermediate",
    "advanced",
]

AssessmentItemType = Literal[
    "quiz_question",
    "practice_task",
]

EvaluationMethod = Literal[
    "rule",
    "model",
    "human",
]

ReplanAction = Literal[
    "advance",
    "add_practice",
    "add_review",
    "stop",
]

EvaluationStatus = Literal[
    "evaluated",
    "needs_human_review",
    "uncertain",
]

class StrictModel(BaseModel):
    """RepoMentor严格数据模型基类。"""

    model_config = ConfigDict(
        extra="forbid",#不允许出现没定义的字段
        str_strip_whitespace=True,#允许一些特殊类型
    )

class RepositoryEvidence(StrictModel):
    """从真实仓库中获得的一条可追溯证据。"""

    source_path: str = Field(
        min_length=1,
        description="证据来自哪个真实仓库文件",
    )

    snippet: str | None = Field(
        default=None,
        description="真实读取到的证据片段；没有内容证据时为空",
    )

    reason: str = Field(
        min_length=1,
        description="为什么这条证据与目标任务有关",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="证据可信度",
    )

class RankedRepositoryFile(StrictModel):
    """一个目标相关的仓库候选文件。"""

    file_path: str = Field(
        min_length=1,
    )

    score: float = Field(
        ge=0.0,
    )

    reasons: list[str] = Field(
        min_length=1,
    )

    evidence: list[RepositoryEvidence] = Field(
        min_length=1,
    )

    content_status: Literal[
        "verified",
        "needs_confirmation",
    ]


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


ConfirmationAction = Literal[
    "approve",
    "revise",
]


class RoadmapConfirmation(StrictModel):
    """用户对生成路线作出的确认或修改决定。"""

    action: ConfirmationAction = Field(
        description="批准当前路线，或请求修改后重新生成",
    )
    target_updates: dict[str, Any] = Field(
        default_factory=dict,
        description="需要合并进 target_input 的目标修改",
    )
    learner_updates: dict[str, Any] = Field(
        default_factory=dict,
        description="需要合并进 learner_input 的学习者修改",
    )

    @model_validator(mode="after")
    def validate_action_payload(
        self,
    ) -> "RoadmapConfirmation":
        """确保 action 与修改内容保持一致。"""
        has_updates = bool(
            self.target_updates
            or self.learner_updates
        )

        if self.action == "approve" and has_updates:
            raise ValueError(
                "批准路线时不能同时提交修改内容"
            )

        if self.action == "revise" and not has_updates:
            raise ValueError(
                "请求修改时必须提供目标或学习者更新"
            )

        return self


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


class QuizQuestion(StrictModel):
    """与当前路线任务及仓库证据相关的结构化测验题。"""

    question_id: str = Field(
        min_length=1,
        description="题目在本次测验中的唯一标识",
    )
    question_type: QuizQuestionType = Field(
        description="概念解释题或代码定位题",
    )
    prompt: str = Field(
        min_length=5,
        description="向学习者展示的问题",
    )
    expected_answer: str = Field(
        min_length=2,
        description="用于评估回答的参考答案",
    )
    difficulty: AssessmentDifficulty = Field(
        description="题目难度",
    )
    related_task_title: str = Field(
        min_length=2,
        description="题目对应的当前路线任务标题",
    )
    evidence_sources: list[EvidenceSource] = Field(
        min_length=1,
        description="支持该题目的真实仓库来源",
    )
    knowledge_points: list[str] = Field(
        min_length=1,
        description="该题考查的知识点",
    )
    max_score: int = Field(
        default=10,
        ge=1,
        le=100,
        description="该题最高分",
    )

class PracticeTask(StrictModel):
    """与当前路线和仓库证据相关的结构化实践任务。"""

    practice_id: str = Field(
        min_length=1,
        description="实践任务在本次评估中的唯一标识",
    )
    title: str = Field(
        min_length=2,
        description="实践任务标题",
    )
    instructions: str = Field(
        min_length=5,
        description="学习者需要执行的具体操作",
    )
    expected_outcome: str = Field(
        min_length=5,
        description="完成实践后应该达到的结果",
    )
    deliverable: str = Field(
        min_length=2,
        description="学习者需要提交的代码、测试或说明",
    )
    difficulty: AssessmentDifficulty = Field(
        description="实践任务难度",
    )
    related_task_title: str = Field(
        min_length=2,
        description="实践任务对应的当前路线任务标题",
    )
    evidence_sources: list[EvidenceSource] = Field(
        min_length=1,
        description="实践任务依据的真实仓库来源",
    )
    knowledge_points: list[str] = Field(
        min_length=1,
        description="该实践任务训练的知识点",
    )
    completion_criteria: list[str] = Field(
        min_length=1,
        description="可验证的完成条件",
    )
    max_score: int = Field(
        default=10,
        ge=1,
        le=100,
        description="实践任务最高分",
    )

    estimated_hours: float = Field(
        ge=0.25,
        le=12,
        description="预计完成时间",
    )
    requires_human_review: bool = Field(
        default=True,
        description="实践产物是否需要人工检查",
    )

class AssessmentPackage(StrictModel):
    """围绕一个路线任务生成的完整评估包。"""

    assessment_id: str = Field(
        min_length=1,
        description="本次评估包的唯一标识",
    )
    related_task_title: str = Field(
        min_length=2,
        description="评估包对应的当前路线任务",
    )
    difficulty: AssessmentDifficulty = Field(
        description="整组评估的统一难度",
    )
    questions: list[QuizQuestion] = Field(
        min_length=2,
        max_length=2,
        description="一题概念题和一题代码定位题",
    )
    practice_task: PracticeTask = Field(
        description="一个基于真实仓库证据的实践任务",
    )

    @model_validator(mode="after")
    def validate_assessment_package(
        self,
    ) -> "AssessmentPackage":
        """校验题型、任务、难度和标识的一致性。"""
        question_types = {
            question.question_type
            for question in self.questions
        }

        if question_types != {
            "concept",
            "code_location",
        }:
            raise ValueError(
                "评估包必须同时包含一题概念题和一题代码定位题"
            )

        all_items = [
            *self.questions,
            self.practice_task,
        ]

        if any(
            item.related_task_title
            != self.related_task_title
            for item in all_items
        ):
            raise ValueError(
                "所有评估项目必须对应同一个路线任务"
            )

        if any(
            item.difficulty != self.difficulty
            for item in all_items
        ):
            raise ValueError(
                "所有评估项目的难度必须与评估包一致"
            )

        item_ids = [
            question.question_id
            for question in self.questions
        ]
        item_ids.append(
            self.practice_task.practice_id
        )

        if len(item_ids) != len(set(item_ids)):
            raise ValueError(
                "评估项目标识不能重复"
            )

        return self

class AssessmentSubmission(StrictModel):
    """学习者从 interrupt 恢复时提交的答案集。"""

    answers: dict[str, str] = Field(
        min_length=1,
        description="题目或实践 ID 到学习者回答的映射",
    )


class ConceptEvaluationDraft(StrictModel):
    """LLM 对概念题回答产生的受限评分草稿。"""

    status: Literal[
        "evaluated",
        "uncertain",
    ] = Field(
        description="可以可靠评分，或当前证据不足以评分",
    )
    score: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="建议得分；不确定时必须为空",
    )
    feedback: str = Field(
        min_length=5,
        description="基于参考答案和证据的具体评分理由",
    )
    matched_points: list[str] = Field(
        default_factory=list,
        description="回答已经体现的关键点",
    )
    missing_points: list[str] = Field(
        default_factory=list,
        description="回答缺少或错误的关键点",
    )

    @model_validator(mode="after")
    def validate_concept_evaluation(
        self,
    ) -> "ConceptEvaluationDraft":
        """不允许在不确定状态下给出看似精确的分数。"""
        if (
            self.status == "evaluated"
            and self.score is None
        ):
            raise ValueError(
                "可以评分时必须提供建议得分"
            )

        if (
            self.status == "uncertain"
            and self.score is not None
        ):
            raise ValueError(
                "评分不确定时不能提供建议得分"
            )

        return self

class EvaluationResult(StrictModel):
    """一道测验题或实践任务的结构化评估结果。"""

    item_id: str = Field(
        min_length=1,
        description="被评估题目或实践任务的标识",
    )
    item_type: AssessmentItemType = Field(
        description="被评估的是测验题还是实践任务",
    )
    learner_response: str | None = Field(
        default=None,
        description="学习者提交的答案或实践结果说明",
    )
    status: EvaluationStatus = Field(
        description="已评分、待人工复核或评分不确定",
    )
    evaluation_method: EvaluationMethod = Field(
        description="规则、模型或人工评分",
    )
    score: float | None = Field(
        default=None,
        ge=0,
        description="实际得分；尚未评分时为空",
    )
    max_score: float = Field(
        gt=0,
        le=100,
        description="最高分",
    )
    feedback: str = Field(
        min_length=2,
        description="具体评分理由和改进建议",
    )
    knowledge_points: list[str] = Field(
        min_length=1,
        description="本次结果涉及的知识点",
    )
    source_files: list[str] = Field(
        min_length=1,
        description="评估内容对应的仓库来源文件",
    )

    @model_validator(mode="after")
    def validate_evaluation_result(
        self,
    ) -> "EvaluationResult":
        """校验评分状态、评分方式和分数的一致性。"""
        if (
            self.score is not None
            and self.score > self.max_score
        ):
            raise ValueError("实际得分不能高于最高分")

        if (
            self.status == "evaluated"
            and self.score is None
        ):
            raise ValueError("已完成评分时必须提供实际得分")

        if (
            self.status == "needs_human_review"
            and self.evaluation_method != "human"
        ):
            raise ValueError(
                "待人工复核时 evaluation_method 必须是 human"
            )

        return self

class KnowledgeMasteryEvidence(StrictModel):
    """一个知识点的掌握结论及其评估来源。"""

    knowledge_point: str = Field(
        min_length=1,
        description="被评估的知识点",
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="该知识点的归一化掌握度",
    )
    status: KnowledgeMasteryStatus = Field(
        description="已掌握、发展中或薄弱",
    )
    assessment_item_ids: list[str] = Field(
        min_length=1,
        description="支持该结论的题目或任务 ID",
    )
    source_files: list[str] = Field(
        min_length=1,
        description="支持该结论的真实仓库文件",
    )

class MasteryProfile(StrictModel):
    """围绕当前目标任务形成的学习者掌握度汇总。"""

    profile_id: str = Field(
        min_length=1,
        description="本次掌握度画像的唯一标识",
    )
    target_task_title: str = Field(
        min_length=2,
        description="掌握度画像对应的目标任务",
    )
    overall_score: float = Field(
        ge=0.0,
        le=1.0,
        description="当前目标的总体掌握度，范围为 0 到 1",
    )
    knowledge_scores: dict[str, float] = Field(
        default_factory=dict,
        description="各知识点的掌握度，范围为 0 到 1",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="已经掌握较好的知识点",
    )
    weak_points: list[str] = Field(
        default_factory=list,
        description="仍需加强的知识点",
    )
    evaluation_results: list[EvaluationResult] = Field(
        default_factory=list,
        description="构成本次掌握度画像的评估结果",
    )
    mastered_skills: list[str] = Field(
        default_factory=list,
        description="由实际评估证据确认掌握的知识点",
    )
    completed_tasks: list[str] = Field(
        default_factory=list,
        description="已经可靠评分完成的题目或任务 ID",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="当前画像的证据覆盖度",
    )
    knowledge_evidence: list[
        KnowledgeMasteryEvidence
    ] = Field(
        default_factory=list,
        description="各知识点结论与题目、源码的对应关系",
    )

    @model_validator(mode="after")
    def validate_mastery_profile(
        self,
    ) -> "MasteryProfile":
        """校验知识点分数范围和评估结果唯一性。"""
        for knowledge_point, score in (
            self.knowledge_scores.items()
        ):
            if not knowledge_point.strip():
                raise ValueError("知识点名称不能为空")

            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    "知识点掌握度必须在 0 到 1 之间"
                )

        item_ids = [
            result.item_id
            for result in self.evaluation_results
        ]

        if len(item_ids) != len(set(item_ids)):
            raise ValueError(
                "同一个评估项目不能重复计入掌握度画像"
            )

        return self

class ReplanDecision(StrictModel):
    """掌握度 Reflection 产生的确定性重新规划决定。"""

    action: ReplanAction = Field(
        description="进入下一模块、增加实践、增加复习或停止",
    )
    overall_score: float = Field(
        ge=0.0,
        le=1.0,
        description="作出决定时使用的总体掌握度",
    )
    reason: str = Field(
        min_length=5,
        description="为什么选择该重新规划动作",
    )
    focus_points: list[str] = Field(
        default_factory=list,
        description="新增任务必须对应的薄弱或发展中知识点",
    )
    replan_count: int = Field(
        ge=0,
        description="作出决定前已经重新规划的次数",
    )
    max_replans: int = Field(
        ge=1,
        description="最多允许重新规划的次数",
    )

    @model_validator(mode="after")
    def validate_replan_decision(
        self,
    ) -> "ReplanDecision":
        """新增任务时必须说明针对哪些知识点。"""
        if (
            self.action in {
                "add_practice",
                "add_review",
            }
            and not self.focus_points
        ):
            raise ValueError(
                "新增实践或复习任务时必须提供 focus_points"
            )

        if self.replan_count > self.max_replans:
            raise ValueError(
                "replan_count 不能超过 max_replans"
            )

        return self

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
