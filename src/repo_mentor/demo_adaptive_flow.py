"""V0.6 自适应工作流演示：路线生成、中断确认与恢复。

PowerShell 运行方式（项目根目录）：
    $env:PYTHONPATH = (Resolve-Path .\src).Path
    python -m repo_mentor.demo_adaptive_flow

说明：
- 默认离线：generate_roadmap 用假生成器，不花钱不联网；
- 想用真实 LLM 生成路线：把 USE_REAL_LLM 改为 True
  （需要 .env 里有有效的 MODEL_API_KEY）。
"""
from pathlib import Path

from repo_mentor import adaptive_nodes
from repo_mentor.adaptive_workflow import (
    build_adaptive_graph,
    resume_adaptive_workflow,
    start_adaptive_workflow,
)
from repo_mentor.models import (
    DailyPlan,
    EvidenceSource,
    LearnerProfile,
    LearningRoadmap,
    LearningTask,
    TargetTask,
)

# 演示用目标仓库：项目自带的 demo_repo（小、快、离线可跑）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_REPO = PROJECT_ROOT / "data" / "demo_repo"

# False = 离线演示（推荐先跑这个）；True = 真实 LLM 生成路线
USE_REAL_LLM = False


def fake_roadmap_generator(
    user_profile,
    target_task,
    repository_readme,
    repository_tree,
) -> LearningRoadmap:
    """离线生成结构正确的路线，不调用 LLM。"""
    # 生产生成器接收 dict，离线替身保持相同输入契约，
    # 并重新校验成严格领域模型。
    learner = LearnerProfile.model_validate(user_profile)
    target = TargetTask.model_validate(target_task)

    task = LearningTask(
        title="定位并解释目录树生成流程",
        objective="能够说明仓库目录树如何被读取并用于路线生成",
        evidence_sources=[
            EvidenceSource(
                file_path="README.md",
                evidence_type="readme",
                reason="演示仓库 README 提供项目入口和目录说明",
                excerpt=(
                    repository_readme[:200]
                    if repository_readme
                    else None
                ),
                confidence=0.9,
            )
        ],
        reading_task="阅读 README 和仓库目录结构说明",
        code_location_task="定位目录树读取相关模块和调用位置",
        practice_task="用自己的语言画出目录树生成与消费流程",
        completion_criteria=[
            "能说明目录树数据从哪里产生",
            "能指出目录树被哪个路线生成步骤消费",
        ],
        estimated_hours=1.0,
    )

    return LearningRoadmap(
        learner_profile=learner,
        target_task=target,
        learner_summary="具备 Python 基础，需要补充 LangGraph 和 Pydantic 知识",
        skill_gaps=list(learner.unfamiliar_skills),
        daily_plans=[
            DailyPlan(
                day=1,
                theme="理解目录树证据流程",
                tasks=[task],
                daily_outcome="能够解释目录树证据如何进入学习路线",
            )
        ],
        risks_and_uncertainties=[
            "离线演示使用固定路线，不代表真实 LLM 的生成质量",
        ],
        total_estimated_hours=1.0,
    )


def main() -> None:
    """运行 V0.6 路线生成、人工确认和 checkpoint 恢复演示。"""
    learner = LearnerProfile(
        current_level="beginner",
        known_skills=["python"],
        unfamiliar_skills=["pydantic", "langchain"],
        learning_goal="理解目录树扫描",
        daily_hours=2.0,
        available_days=7,
    )
    target = TargetTask(
        title="理解目录树扫描",
        description="理解仓库目录树生成流程",
        task_type="understand_module",
        expected_outcome="能说明目录树生成流程",
    )

    # 离线模式只替换 LLM 依赖。
    # 图结构、节点、路由和 checkpoint 都使用正式实现。
    if not USE_REAL_LLM:
        adaptive_nodes.generate_structured_roadmap = (
            fake_roadmap_generator
        )

    # Checkpointer 绑定在编译后的 app 上。
    # 暂停和恢复必须复用同一个 app。
    app = build_adaptive_graph()
    thread_id = "v06-demo-session"

    print("== 启动 V0.6 自适应工作流 ==")

    result = start_adaptive_workflow(
        app,
        thread_id=thread_id,
        repository_path=str(TARGET_REPO),
        learner_profile=learner,
        target_task=target,
    )

    # 用户可以多次 revise。
    # 每次修改后都会重新生成路线并再次进入 interrupt。
    while "__interrupt__" in result:
        interrupt_value = result["__interrupt__"][0].value

        print("\n== 工作流已暂停 ==")
        print("问题：", interrupt_value["question"])
        print("当前目标：", interrupt_value["target"]["title"])
        print(
            "当前水平：",
            interrupt_value["learner"]["current_level"],
        )
        print(
            "路线主题：",
            interrupt_value["roadmap"]["daily_plans"][0]["theme"],
        )
        print(
            "修订次数：",
            interrupt_value["revision_count"],
        )

        action = input(
            "\n请输入 approve 批准，或 revise 修改难度"
            "（直接回车默认 approve）："
        ).strip().lower()

        if not action:
            action = "approve"

        if action == "approve":
            confirmation = {
                "action": "approve",
            }
        elif action == "revise":
            new_level = input(
                "请输入新的技术水平"
                "（例如 beginner/intermediate）："
            ).strip()

            if not new_level:
                new_level = "intermediate"

            confirmation = {
                "action": "revise",
                "learner_updates": {
                    "current_level": new_level,
                },
            }
        else:
            print("只支持 approve 或 revise，请重新输入。")
            continue

        # Command(resume=...) 通过相同 thread_id
        # 找到之前保存的 checkpoint。
        result = resume_adaptive_workflow(
            app,
            thread_id=thread_id,
            confirmation=confirmation,
        )

    roadmap = result.get("roadmap")

    if not isinstance(roadmap, LearningRoadmap):
        questions = result.get(
            "clarification_questions",
            [],
        )
        raise RuntimeError(
            "工作流没有生成路线。"
            f"需要补充的信息：{questions}"
        )

    print("\n== 最终路线已批准 ==")
    print("确认状态：", result["confirmation_status"])
    print("学习目标：", roadmap.target_task.title)
    print("学习者水平：", roadmap.learner_profile.current_level)
    print("路线主题：", roadmap.daily_plans[0].theme)
    print("任务标题：", roadmap.daily_plans[0].tasks[0].title)
    print("预计时间：", roadmap.total_estimated_hours)

    # 演示同时承担最基本的冒烟验证。
    assert result["confirmation_status"] == "approved"
    assert result["human_confirmation"].action == "approve"
    assert roadmap.target_task.title == target.title
    assert roadmap.daily_plans
    assert roadmap.daily_plans[0].tasks

    print("\nV0.6 ADAPTIVE WORKFLOW DEMO PASSED")


if __name__ == "__main__":
    main()
