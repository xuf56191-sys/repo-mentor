"""V0.6 自适应工作流：组装核心节点和条件路由。

两个公开入口：
- build_adaptive_graph()：组装并编译图，返回可 invoke 的 app；
- run_adaptive_workflow(...)：一次调用完成整条工作流，
  返回结构化 LearningRoadmap。
"""

from typing import Literal

from langgraph.graph import START, END, StateGraph

from repo_mentor import adaptive_nodes
from repo_mentor.models import LearnerProfile, LearningRoadmap, TargetTask
from repo_mentor.workflow_state import (
    AgentState,
    create_initial_state,
)

def build_adaptive_graph():
    """组装并编译基础图，返回可 invoke 的 app。"""
    graph = StateGraph(AgentState)

    # 注册 6 个节点；执行顺序由边和路由决定
    graph.add_node("analyze_learner", adaptive_nodes.analyze_learner)
    graph.add_node("analyze_target", adaptive_nodes.analyze_target)
    graph.add_node("collect_evidence", adaptive_nodes.collect_evidence)
    graph.add_node("generate_roadmap", adaptive_nodes.generate_roadmap)
    graph.add_node("inspect_request", adaptive_nodes.inspect_request)
    graph.add_node(
        "request_clarification",
        adaptive_nodes.request_clarification,
    )

    # 连边：定义执行顺序（与流程图一致）
    graph.add_edge(START, "inspect_request")

    graph.add_conditional_edges(
        "inspect_request",
        route_after_request,
        {
            "ready": "analyze_learner",
            "needs_clarification": "request_clarification",
        },
    )

    graph.add_edge("analyze_learner", "analyze_target")
    graph.add_edge("analyze_target", "collect_evidence")
    graph.add_conditional_edges(
        "collect_evidence",
        route_after_evidence,
        {
            "enough_evidence": "generate_roadmap",
            "needs_clarification": "request_clarification",
        },
    )
    graph.add_edge("generate_roadmap", END)
    graph.add_edge(
        "request_clarification",
        END,
    )

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
        "learner_input": learner_profile.model_dump(mode="json"),
        "target_input": target_task.model_dump(mode="json"),
        "repository_path": repository_path,
    }
    result = build_adaptive_graph().invoke(initial)
    roadmap = result["roadmap"]
    if not isinstance(roadmap,LearningRoadmap):
        raise TypeError(
            f"预期LearningRoadmap,实际为{type(roadmap).__name__}"
        )
    return roadmap


# ---------------- 路由 1：判断原始输入是否完整（纯规则） ----------------

def route_after_request(
    state: AgentState,
) -> Literal["ready", "needs_clarification"]:
    """根据输入缺失项决定继续分析还是请求澄清。"""
    if state.get("missing_fields"):
        return "needs_clarification"

    return "ready"


# ---------------- 路由 2：判断仓库证据是否充分（纯规则） ----------------

def route_after_evidence(
    state: AgentState,
) -> Literal["enough_evidence", "needs_clarification"]:
    """证据为空时请求澄清，否则继续生成路线。"""
    if not state.get("repo_evidence"):
        return "needs_clarification"

    return "enough_evidence"
