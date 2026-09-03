"""Streamlit 界面背后的纯 Python 应用服务。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from repo_mentor.assessment_evaluator import (
    evaluate_code_location_answer,
    mark_practice_for_human_review,
)
from repo_mentor.assessment_generator import infer_assessment_difficulty
from repo_mentor.contribution_analyzer import analyze_contribution_gap
from repo_mentor.contribution_models import (
    ContributionGapAnalysis,
    OpenEulerContributionPlan,
    TargetIssue,
)
from repo_mentor.document_loader import classify_scoped_file
from repo_mentor.learning_evidence import LearningEvidenceLayer
from repo_mentor.mastery_updater import build_mastery_profile
from repo_mentor.models import (
    AssessmentPackage,
    DailyPlan,
    EvidenceSource,
    EvaluationResult,
    LearnerProfile,
    LearningRoadmap,
    LearningTask,
    MasteryProfile,
    PracticeTask,
    QuizQuestion,
    TargetTask,
)
from repo_mentor.openeuler_mode import build_openeuler_contribution_plan
from repo_mentor.progress_store import SQLiteProgressStore
from repo_mentor.repository_ranker import rank_target_files
from repo_mentor.repository_reader import read_repository_onboarding_docs


@dataclass(frozen=True)
class UIAnalysisBundle:
    learner: LearnerProfile
    issue: TargetIssue
    target: TargetTask
    evidence_layer: LearningEvidenceLayer
    roadmap: LearningRoadmap
    assessment: AssessmentPackage
    gap: ContributionGapAnalysis
    contribution_plan: OpenEulerContributionPlan


def _target_from_issue(issue: TargetIssue) -> TargetTask:
    return TargetTask(
        title=issue.title,
        description=issue.description,
        task_type="solve_issue",
        expected_outcome=issue.expected_outcome,
        reference=issue.reference,
    )


def _scope_sources(
    repository_path: str | Path,
    target: TargetTask,
) -> list[EvidenceSource]:
    paths: list[str] = []
    onboarding = read_repository_onboarding_docs(repository_path)
    paths.extend(document.relative_path for document in onboarding.documents)
    paths.extend(
        item.file_path
        for item in rank_target_files(repository_path, target, top_n=12)
        if classify_scoped_file(item.file_path) is not None
    )
    return [
        EvidenceSource(
            file_path=path,
            evidence_type=(
                "readme"
                if Path(path).name.casefold().startswith("readme")
                else "contributing"
                if Path(path).name.casefold().startswith("contributing")
                else "test"
                if path.replace("\\", "/").casefold().startswith("tests/")
                else "source"
            ),
            reason="当前 Issue 的受控本地证据候选",
        )
        for path in dict.fromkeys(paths)
    ]


def _scope_task(
    repository_path: str | Path,
    target: TargetTask,
) -> LearningTask:
    sources = _scope_sources(repository_path, target)
    if not sources:
        raise ValueError(
            "当前仓库没有可用于学习路线的 README、CONTRIBUTING、"
            "Python、测试或配置证据。"
        )
    return LearningTask(
        title=f"定位 {target.title} 的仓库证据",
        objective="用受控本地来源理解目标 Issue 的实现位置和贡献要求",
        evidence_sources=sources,
        reading_task="阅读目标相关 README、贡献指南和源码片段",
        code_location_task="记录关键文件路径、符号和行号范围",
        practice_task="用自己的语言说明 Issue、实现位置和验证方法",
        completion_criteria=[
            "至少引用一个真实仓库文件",
            "说明一个需要执行的测试或人工验收步骤",
        ],
        estimated_hours=1.0,
    )


def _roadmap_sources(
    layer: LearningEvidenceLayer,
    gap: ContributionGapAnalysis,
) -> list[EvidenceSource]:
    if gap.recommended_files:
        return gap.recommended_files
    return [
        EvidenceSource(
            file_path=document.source_path,
            evidence_type=(
                "test" if document.source_type == "test" else "source"
            ),
            reason="当前学习模块已安全加载的来源",
            excerpt=document.content[:400],
            confidence=1.0,
        )
        for document in layer.load_result.documents[:3]
    ]


def build_offline_roadmap(
    learner: LearnerProfile,
    target: TargetTask,
    layer: LearningEvidenceLayer,
    gap: ContributionGapAnalysis,
) -> LearningRoadmap:
    """在无 API 时也能展示可执行、证据约束的贡献路线。"""
    sources = _roadmap_sources(layer, gap)
    focus_points = gap.missing_knowledge or ["贡献前证据复核"]
    daily_plans: list[DailyPlan] = []
    for day, focus in enumerate(
        focus_points[: learner.available_days], start=1
    ):
        daily_plans.append(
            DailyPlan(
                day=day,
                theme=f"补足 {focus}",
                tasks=[
                    LearningTask(
                        title=f"{focus}：阅读、定位与实践",
                        objective=f"为目标 Issue 建立可验证的 {focus} 能力",
                        evidence_sources=sources,
                        reading_task="阅读证据来源并记录关键约束",
                        code_location_task="定位相关文件、符号和行号",
                        practice_task=f"完成一个与 {focus} 对应的小练习",
                        completion_criteria=[
                            "结论包含真实来源",
                            "练习产物可由测试或人工检查",
                        ],
                        estimated_hours=min(learner.daily_hours, 2.0),
                    )
                ],
                daily_outcome=f"能够解释 {focus} 与目标 Issue 的关系",
            )
        )
    return LearningRoadmap(
        learner_profile=learner,
        target_task=target,
        learner_summary=f"当前水平：{learner.current_level}",
        skill_gaps=list(gap.missing_knowledge),
        daily_plans=daily_plans,
        risks_and_uncertainties=[
            "离线预览未调用 LLM，任务表达和贡献结论仍需人工复核。"
        ],
        total_estimated_hours=round(
            sum(
                task.estimated_hours
                for plan in daily_plans
                for task in plan.tasks
            ),
            2,
        ),
    )


def build_offline_assessment(
    learner: LearnerProfile,
    roadmap: LearningRoadmap,
) -> AssessmentPackage:
    """构造固定题型的离线预览；所有题目仍绑定真实来源。"""
    task = roadmap.daily_plans[0].tasks[0]
    source = task.evidence_sources[0]
    difficulty = infer_assessment_difficulty(learner)
    digest = hashlib.sha256(task.title.encode("utf-8")).hexdigest()[:10]
    questions = [
        QuizQuestion(
            question_id=f"concept-{digest}",
            question_type="concept",
            prompt=f"解释“{task.title}”为什么需要当前证据来源。",
            expected_answer=(
                source.excerpt or f"应依据 {source.file_path} 说明，不能脱离来源猜测。"
            ),
            difficulty=difficulty,
            related_task_title=task.title,
            evidence_sources=[source],
            knowledge_points=[task.title],
            max_score=10,
        ),
        QuizQuestion(
            question_id=f"location-{digest}",
            question_type="code_location",
            prompt="给出当前任务一个真实来源的完整仓库相对路径。",
            expected_answer=source.file_path,
            difficulty=difficulty,
            related_task_title=task.title,
            evidence_sources=[source],
            knowledge_points=["代码定位"],
            max_score=10,
        ),
    ]
    practice = PracticeTask(
        practice_id=f"practice-{digest}",
        title=f"完成 {task.title} 的最小实践",
        instructions=task.practice_task,
        expected_outcome=task.completion_criteria[0],
        deliverable="代码、测试输出或带来源的说明",
        difficulty=difficulty,
        related_task_title=task.title,
        evidence_sources=[source],
        knowledge_points=[task.title, "贡献实践"],
        completion_criteria=list(task.completion_criteria),
        max_score=10,
        estimated_hours=max(0.25, min(task.estimated_hours, 2.0)),
        requires_human_review=True,
    )
    return AssessmentPackage(
        assessment_id=f"assessment-{digest}",
        related_task_title=task.title,
        difficulty=difficulty,
        questions=questions,
        practice_task=practice,
    )


def analyze_ui_request(
    repository_path: str | Path,
    learner: LearnerProfile,
    issue: TargetIssue,
) -> UIAnalysisBundle:
    """一次建立证据层，再生成路线、测验和贡献准备结果。"""
    target = _target_from_issue(issue)
    scope_task = _scope_task(repository_path, target)
    layer = LearningEvidenceLayer.build(
        repository_path, target, scope_task
    )
    gap = analyze_contribution_gap(
        issue,
        learner,
        retrieval_chunks=list(layer.chunks),
    )
    contribution_plan = build_openeuler_contribution_plan(
        repository_path, issue, gap
    )
    roadmap = build_offline_roadmap(learner, target, layer, gap)
    assessment = build_offline_assessment(learner, roadmap)
    return UIAnalysisBundle(
        learner=learner,
        issue=issue,
        target=target,
        evidence_layer=layer,
        roadmap=roadmap,
        assessment=assessment,
        gap=gap,
        contribution_plan=contribution_plan,
    )


def evaluate_ui_answers(
    bundle: UIAnalysisBundle,
    answers: dict[str, str],
) -> tuple[list[EvaluationResult], MasteryProfile]:
    assessment = bundle.assessment
    concept = next(q for q in assessment.questions if q.question_type == "concept")
    location = next(q for q in assessment.questions if q.question_type == "code_location")
    concept_result = EvaluationResult(
        item_id=concept.question_id,
        item_type="quiz_question",
        learner_response=answers.get(concept.question_id) or None,
        status="uncertain",
        evaluation_method="rule",
        score=None,
        max_score=float(concept.max_score),
        feedback="概念开放题需要模型或人工结合来源复核，离线界面不猜测评分。",
        knowledge_points=list(concept.knowledge_points),
        source_files=[item.file_path for item in concept.evidence_sources],
    )
    results = [
        concept_result,
        evaluate_code_location_answer(
            location, answers.get(location.question_id, "")
        ),
        mark_practice_for_human_review(
            assessment.practice_task,
            answers.get(assessment.practice_task.practice_id, ""),
        ),
    ]
    return results, build_mastery_profile(bundle.target, results)


def save_ui_progress(
    database_path: str | Path,
    repository_path: str | Path,
    bundle: UIAnalysisBundle,
    results: list[EvaluationResult],
    mastery: MasteryProfile,
    *,
    profile_key: str = "streamlit-user",
) -> int:
    store = SQLiteProgressStore(database_path)
    return store.save_progress(
        repository_path=repository_path,
        learner_profile=bundle.learner,
        roadmap=bundle.roadmap,
        mastery=mastery,
        assessment_results=results,
        profile_key=profile_key,
    )
