"""V0.6 自适应工作流：把四个核心节点组装成基础图。

两个公开入口：
- build_adaptive_graph()：组装并编译图，返回可 invoke 的 app；
- run_adaptive_workflow(...)：一次调用完成整条工作流，
  返回结构化 LearningRoadmap。
"""

from langgraph.graph import START, END, StateGraph

from repo_mentor import adaptive_nodes
from repo_mentor.adaptive_nodes import analyze_learner
from repo_mentor.models import LearnerProfile, LearningRoadmap, TargetTask
from repo_mentor.workflow_state import (
    AgentState,
    create_initial_state,
)

def build_adaptive_graph():
    """组装并编译基础图，返回可 invoke 的 app。"""
    graph = StateGraph(AgentState)

    # 注册 4 个节点（执行顺序由 add_edge 决定，与注册顺序无关）
    graph.add_node("analyze_learner", adaptive_nodes.analyze_learner)
    graph.add_node("analyze_target", adaptive_nodes.analyze_target)
    graph.add_node("collect_evidence", adaptive_nodes.collect_evidence)
    graph.add_node("generate_roadmap", adaptive_nodes.generate_roadmap)

    # 连边：定义执行顺序（与流程图一致）
    graph.add_edge(START, "analyze_learner")
    graph.add_edge("analyze_learner", "analyze_target")
    graph.add_edge("analyze_target", "collect_evidence")
    graph.add_edge("collect_evidence", "generate_roadmap")
    graph.add_edge("generate_roadmap", END)

    # 编译：校验图合法性（无孤立节点、无非法边）
    return graph.compile()

def run_adaptive_workflow(
    repository_path: str,
    learner_profile: LearnerProfile,
    target_task: TargetTask,
) -> LearningRoadmap:
    """构造初始 State -> 执行整条图 -> 返回结构化路线。"""
    initial = {
        **create_initial_state(learner_profile, target_task),
        "repository_path": repository_path,
    }
    result = build_adaptive_graph().invoke(initial)
    roadmap = result["roadmap"]
    if not isinstance(roadmap,LearningRoadmap):
        raise TypeError(
            f"预期LearningRoadmap,实际为{type(roadmap).__name__}"
        )
    return roadmap


