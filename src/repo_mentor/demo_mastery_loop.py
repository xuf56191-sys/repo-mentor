r"""V0.7 掌握度学习闭环的离线端到端演示。

PowerShell 运行方式（项目根目录）：
    $env:PYTHONPATH = (Resolve-Path .\src).Path
    python -m repo_mentor.demo_mastery_loop

演示不访问网络：路线生成、评估生成和概念评分使用固定替身，
图、checkpoint、规则评分、画像更新、重规划和 SQLite 均使用正式实现。
"""

from pathlib import Path
from unittest.mock import patch

from repo_mentor import adaptive_nodes
from repo_mentor.adaptive_workflow import (
    build_adaptive_graph,
    resume_adaptive_workflow,
    resume_mastery_workflow,
    start_adaptive_workflow,
)
from repo_mentor.demo_adaptive_flow import (
    fake_roadmap_generator,
)
from repo_mentor.models import (
    AssessmentPackage,
    EvaluationResult,
    LearnerProfile,
    PracticeTask,
    QuizQuestion,
    TargetTask,
)
from repo_mentor.progress_store import (
    SQLiteProgressStore,
    StoredLearningProgress,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_REPOSITORY = PROJECT_ROOT / "data" / "demo_repo"
DEFAULT_DATABASE_PATH = (
    PROJECT_ROOT / "data" / "repo_mentor_progress.db"
)


def fake_assessment_generator(
    learner_profile,
    learning_task,
    repo_evidence,
) -> AssessmentPackage:
    """生成与当前路线任务绑定的离线评估包。"""
    source = learning_task.evidence_sources[0]
    task_title = learning_task.title

    return AssessmentPackage(
        assessment_id="assessment-v07-demo",
        related_task_title=task_title,
        difficulty="beginner",
        questions=[
            QuizQuestion(
                question_id="question-evidence-flow",
                question_type="concept",
                prompt="目录树证据如何进入路线生成？",
                expected_answer=(
                    "先读取真实仓库内容，"
                    "再将结构化证据交给路线生成节点"
                ),
                difficulty="beginner",
                related_task_title=task_title,
                evidence_sources=[source],
                knowledge_points=["证据流程"],
            ),
            QuizQuestion(
                question_id="question-source-location",
                question_type="code_location",
                prompt="当前路线任务依据的仓库文件是什么？",
                expected_answer=source.file_path,
                difficulty="beginner",
                related_task_title=task_title,
                evidence_sources=[source],
                knowledge_points=["代码定位"],
            ),
        ],
        practice_task=PracticeTask(
            practice_id="practice-evidence-flow",
            title="绘制证据到路线的流程",
            instructions="绘制证据收集和路线生成的节点关系",
            expected_outcome="流程图能够说明证据的来源和去向",
            deliverable="Mermaid 流程图",
            difficulty="beginner",
            related_task_title=task_title,
            evidence_sources=[source],
            knowledge_points=["证据流程"],
            completion_criteria=["包含证据节点和路线节点"],
            estimated_hours=0.5,
        ),
    )


def fake_concept_evaluator(
    question,
    learner_answer,
) -> EvaluationResult:
    """返回可预测的低分，便于展示自适应复习。"""
    return EvaluationResult(
        item_id=question.question_id,
        item_type="quiz_question",
        learner_response=learner_answer,
        status="evaluated",
        evaluation_method="model",
        score=4,
        max_score=question.max_score,
        feedback="回答只提到证据，未说明节点之间的传递。",
        knowledge_points=list(question.knowledge_points),
        source_files=[
            source.file_path
            for source in question.evidence_sources
        ],
    )


def run_demo(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> StoredLearningProgress:
    """执行一次低分后增加复习任务的完整闭环。"""
    learner = LearnerProfile(
        current_level="beginner",
        known_skills=["python"],
        unfamiliar_skills=["langgraph", "pydantic"],
        learning_goal="理解目录树证据流程",
        daily_hours=2.0,
        available_days=7,
    )
    target = TargetTask(
        title="理解目录树证据流程",
        description="理解目录树如何被收集并用于生成路线",
        task_type="understand_module",
        expected_outcome="能说明证据收集到路线生成的流程",
    )

    with (
        patch.object(
            adaptive_nodes,
            "generate_structured_roadmap",
            fake_roadmap_generator,
        ),
        patch.object(
            adaptive_nodes,
            "generate_structured_assessment",
            fake_assessment_generator,
        ),
        patch.object(
            adaptive_nodes,
            "evaluate_concept_answer",
            fake_concept_evaluator,
        ),
    ):
        app = build_adaptive_graph(
            enable_mastery_loop=True
        )
        thread_id = "v07-mastery-demo"

        confirmation_pause = start_adaptive_workflow(
            app,
            thread_id=thread_id,
            repository_path=str(TARGET_REPOSITORY),
            learner_profile=learner,
            target_task=target,
        )
        confirmation_payload = confirmation_pause[
            "__interrupt__"
        ][0].value
        initial_roadmap = confirmation_pause["roadmap"]

        assessment_pause = resume_adaptive_workflow(
            app,
            thread_id=thread_id,
            confirmation={"action": "approve"},
        )
        assessment_payload = assessment_pause[
            "__interrupt__"
        ][0].value

        final_result = resume_mastery_workflow(
            app,
            thread_id=thread_id,
            answers={
                "question-evidence-flow": "目录树会作为证据。",
                "question-source-location": "unknown.py",
                "practice-evidence-flow": "已提交初版流程图。",
            },
        )

    store = SQLiteProgressStore(database_path)
    plan_id = store.save_progress(
        repository_path=TARGET_REPOSITORY,
        learner_profile=final_result["learner_profile"],
        roadmap=final_result["roadmap"],
        mastery=final_result["mastery"],
        replan_decision=final_result[
            "replan_decision"
        ],
        supplemental_tasks=final_result[
            "supplemental_tasks"
        ],
        assessment_results=final_result[
            "evaluation_results"
        ],
    )

    # 新对象模拟进程重启后重新打开数据库。
    reopened_store = SQLiteProgressStore(database_path)
    restored = reopened_store.load_latest_progress(
        TARGET_REPOSITORY
    )

    if restored is None:
        raise RuntimeError("无法从 SQLite 恢复 V0.7 进度")

    print("== V0.7 学习闭环演示 ==")
    print("路线确认中断：", confirmation_payload["kind"])
    print("初始路线任务：", initial_roadmap.daily_plans[0].tasks[0].title)
    print("答案提交中断：", assessment_payload["kind"])
    print("评估后掌握度：", restored.mastery.overall_score)
    print("薄弱点：", "、".join(restored.mastery.weak_points))
    print("重规划动作：", restored.replan_decision.action)
    print("新增任务：", restored.supplemental_tasks[0].title)
    print("SQLite plan_id：", plan_id)

    assert restored.plan_id == plan_id
    assert restored.mastery is not None
    assert restored.mastery.overall_score == 0.2
    assert restored.replan_decision is not None
    assert restored.replan_decision.action == "add_review"
    assert len(restored.supplemental_tasks) == 1

    print("V0.7 MASTERY LOOP DEMO PASSED")
    return restored


def main() -> None:
    run_demo()


if __name__ == "__main__":
    main()
