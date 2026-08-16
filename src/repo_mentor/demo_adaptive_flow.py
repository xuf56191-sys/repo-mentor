"""4 节点最小图演示：验证 State 从输入到 roadmap 的完整流转。

运行方式（项目根目录）：
    set PYTHONPATH=src
    python -m repo_mentor.demo_adaptive_flow

说明：
- 默认离线：generate_roadmap 用假生成器，不花钱不联网；
- 想用真实 LLM 生成路线：把 USE_REAL_LLM 改为 True
  （需要 .env 里有有效的 MODEL_API_KEY）。
"""

from langgraph.graph import START, END, StateGraph

from repo_mentor import adaptive_nodes
from repo_mentor.models import LearnerProfile, TargetTask
from repo_mentor.workflow_state import (
    AgentState,
    create_initial_state,
)

# 演示用目标仓库：项目自带的 demo_repo（小、快、离线可跑）
TARGET_REPO = r"D:\PPT文档\agent初学代码\repo-mentor\data\demo_repo"

# False = 离线演示（推荐先跑这个）；True = 真实 LLM 生成路线
USE_REAL_LLM = False


def fake_roadmap_generator(
    user_profile,
    target_task,
    repository_readme,
    repository_tree,
):
    """离线假生成器：不调 LLM，只返回一行说明，验证 State 流转。"""
    return (
        f"离线路线：{target_task['title']}（真实生成需开启 USE_REAL_LLM）"
    )


def main() -> None:
    # 1. 构造初始 State（repository_path 由调用方提供）
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
    initial = {
        **create_initial_state(learner, target),
        "repository_path": TARGET_REPO,
    }

    # 2. 离线模式：临时替换真实生成器（等价于测试里的 monkeypatch）
    if not USE_REAL_LLM:
        adaptive_nodes.generate_structured_roadmap = fake_roadmap_generator

    # 3. 组装 4 节点图（节点只负责一件事，LangGraph 管流转）
    graph = StateGraph(AgentState)
    graph.add_node("analyze_learner", adaptive_nodes.analyze_learner)
    graph.add_node("analyze_target", adaptive_nodes.analyze_target)
    graph.add_node("collect_evidence", adaptive_nodes.collect_evidence)
    graph.add_node("generate_roadmap", adaptive_nodes.generate_roadmap)
    graph.add_edge(START, "analyze_learner")
    graph.add_edge("analyze_learner", "analyze_target")
    graph.add_edge("analyze_target", "collect_evidence")
    graph.add_edge("collect_evidence", "generate_roadmap")
    graph.add_edge("generate_roadmap", END)
    app = graph.compile()

    # 4. 跑一遍整条链
    result = app.invoke(initial)

    # 5. 展示每个阶段的产物（验证接力正确）
    print("== learner_analysis ==")
    print(result["learner_analysis"])
    print("== target_analysis ==")
    print(result["target_analysis"])
    print("== repo_evidence 条数 ==")
    print(len(result["repo_evidence"]))
    print("== repo_readme 前 40 字符 ==")
    print(result["repo_readme"][:40].replace("\n", " "))
    print("== repo_tree 前 60 字符 ==")
    print(result["repo_tree"][:60].replace("\n", " "))
    print("== roadmap ==")
    print(result["roadmap"])

    # 6. 演示即验证
    assert result["learner_analysis"]["skill_gaps"] == [
        "pydantic", "langchain"
    ]
    assert "tree" in result["target_analysis"]["keywords"]
    assert len(result["repo_evidence"]) > 0
    assert result["repo_readme"]
    assert result["repo_tree"]
    assert result["roadmap"]
    print("\n4-NODE FLOW PASSED")


if __name__ == "__main__":
    main()
