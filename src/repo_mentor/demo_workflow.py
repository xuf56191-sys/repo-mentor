"""最小 LangGraph 演示：State 如何在节点间流动。

运行方式（项目根目录）：
    set PYTHONPATH=src
    python -m repo_mentor.demo_workflow

期望输出：
    step_count: 2
    errors: ['node_a done']
"""

from langgraph.graph import START, END, StateGraph
from repo_mentor.models import LearnerProfile, TargetTask
from repo_mentor.workflow_state import AgentState ,create_initial_state

def node_a(state:AgentState)->dict:
    # 节点只返回"局部更新"，LangGraph 负责 merge 进全局 state
    return {
        "step_count":state.get("step_count",0)+1,
        "errors":["node_a done"],    # operator.add → 追加
    }

def node_b(state: AgentState) -> dict:
    # 注意：这里读到的 step_count 已经是 node_a 更新后的值
    return {"step_count": state.get("step_count", 0) + 1}

def main()->None:
    learner = LearnerProfile(
        current_level="beginner",
        known_skills=["python"],
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
    graph = StateGraph(AgentState)
    graph.add_node("a", node_a)
    graph.add_node("b", node_b)
    graph.add_edge(START, "a")
    graph.add_edge("a", "b")
    graph.add_edge("b", END)
    app = graph.compile()

    result = app.invoke(create_initial_state(
        learner_profile=..., target_task=...,
    ))
    print(result["step_count"])  # 期望 2（a 和 b 各 +1）
    print(result["errors"])      # 期望 ["node_a done"]（累积）
    # 演示即验证
    assert result["step_count"] == 2
    assert result["errors"] == ["node_a done"]
    print("演示通过 ✅")


if __name__ == "__main__":
    main()