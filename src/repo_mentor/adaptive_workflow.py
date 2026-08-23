"""V0.6 自适应工作流：组装核心节点和条件路由。

主要公开入口：
- build_adaptive_graph()：组装并编译图，返回可 invoke 的 app；
- start_adaptive_workflow(...)：使用 thread_id 启动可中断会话；
- resume_adaptive_workflow(...)：使用同一 thread_id 恢复会话；
- run_adaptive_workflow(...)：兼容旧的一次性调用，自动批准生成的路线。
"""

from typing import Any, Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command

from repo_mentor import adaptive_nodes
from repo_mentor.models import LearnerProfile, LearningRoadmap, TargetTask
from repo_mentor.workflow_state import (
    AgentState,
    create_initial_state,
)
from langgraph.checkpoint.serde.jsonplus import (
    JsonPlusSerializer,
)
# LangGraph 整体执行的安全保险。
# 正常业务循环由 AgentState.max_steps 控制。
GRAPH_RECURSION_LIMIT = 20

# Checkpoint 只允许重建 AgentState 中实际保存的项目类型。
# 使用精确白名单，避免允许任意 Python 类型反序列化。
CHECKPOINT_ALLOWED_MSGPACK_MODULES = [
    ("repo_mentor.models", "LearnerProfile"),
    ("repo_mentor.models", "TargetTask"),
    ("repo_mentor.models", "RepositoryEvidence"),
    ("repo_mentor.models", "LearningRoadmap"),
    ("repo_mentor.models", "RoadmapConfirmation"),
    ("repo_mentor.models", "MasteryProfile"),
    (
        "repo_mentor.repository_safeguards",
        "EvidenceBudget",
    ),
]


def create_memory_checkpointer() -> InMemorySaver:
    """创建带自定义类型白名单的开发期内存 Checkpointer。"""
    serializer = JsonPlusSerializer(
        allowed_msgpack_modules=(
            CHECKPOINT_ALLOWED_MSGPACK_MODULES
        ),
    )
    return InMemorySaver(serde=serializer)


def make_thread_config(thread_id: str) -> dict[str, Any]:
    """构造 checkpoint 调用配置；thread_id 不写入业务 State。"""
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise ValueError("thread_id 必须是非空字符串。")

    return {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": GRAPH_RECURSION_LIMIT,
    }


def build_adaptive_graph(
    checkpointer=None,
):
    """组装并编译基础图，返回支持 checkpoint 的 app。"""
    if checkpointer is None:
        checkpointer = create_memory_checkpointer()

    graph = StateGraph(AgentState)

    # 注册 10 个节点；执行顺序由边和条件路由决定
    graph.add_node("analyze_learner", adaptive_nodes.analyze_learner)
    graph.add_node("analyze_target", adaptive_nodes.analyze_target)
    graph.add_node("collect_evidence", adaptive_nodes.collect_evidence)
    graph.add_node("generate_roadmap", adaptive_nodes.generate_roadmap)
    graph.add_node("inspect_request", adaptive_nodes.inspect_request)
    graph.add_node(
        "request_clarification",
        adaptive_nodes.request_clarification,
    )
    graph.add_node(
        "read_more_evidence",
        adaptive_nodes.read_more_evidence,
    )
    graph.add_node(
        "conservative_evidence_stop",
        adaptive_nodes.conservative_evidence_stop,
    )
    graph.add_node(
        "confirm_roadmap",
        adaptive_nodes.confirm_roadmap,
    )
    graph.add_node(
        "apply_human_revision",
        adaptive_nodes.apply_human_revision,
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
            "read_more": "read_more_evidence",
            "stop": "conservative_evidence_stop",
        },
    )
    graph.add_conditional_edges(
        "read_more_evidence",
        route_after_evidence,
        {
            "enough_evidence": "generate_roadmap",
            "read_more": "read_more_evidence",
            "stop": "conservative_evidence_stop",
        },
    )
    graph.add_edge(
        "generate_roadmap",
        "confirm_roadmap",
    )
    graph.add_conditional_edges(
        "confirm_roadmap",
        route_after_confirmation,
        {
            "approved": END,
            "revision_requested": "apply_human_revision",
        },
    )
    graph.add_edge(
        "apply_human_revision",
        "analyze_learner",
    )
    graph.add_edge(
        "request_clarification",
        END,
    )
    graph.add_edge(
        "conservative_evidence_stop",
        END,
    )


    # 编译：校验图合法性（无孤立节点、无非法边）
    return graph.compile(checkpointer=checkpointer)


def start_adaptive_workflow(
    app,
    *,
    thread_id: str,
    repository_path: str,
    learner_profile: LearnerProfile,
    target_task: TargetTask,
) -> dict[str, Any]:
    """启动一个会话，通常在路线确认节点返回 interrupt。"""
    initial = {
        **create_initial_state(learner_profile, target_task),
        "learner_input": learner_profile.model_dump(mode="json"),
        "target_input": target_task.model_dump(mode="json"),
        "repository_path": repository_path,
    }
    return app.invoke(
        initial,
        config=make_thread_config(thread_id),
    )


def resume_adaptive_workflow(
    app,
    *,
    thread_id: str,
    confirmation: dict[str, Any],
) -> dict[str, Any]:
    """用人工决定恢复已中断的同一会话。"""
    return app.invoke(
        Command(resume=confirmation),
        config=make_thread_config(thread_id),
    )

def run_adaptive_workflow(
    repository_path: str,
    learner_profile: LearnerProfile,
    target_task: TargetTask,
) -> LearningRoadmap:
    """兼容旧入口：启动会话，并自动批准生成的路线。"""
    app = build_adaptive_graph()
    thread_id = "run-adaptive-workflow"
    result = start_adaptive_workflow(
        app,
        thread_id=thread_id,
        repository_path=repository_path,
        learner_profile=learner_profile,
        target_task=target_task,
    )

    if result.get("__interrupt__"):
        result = resume_adaptive_workflow(
            app,
            thread_id=thread_id,
            confirmation={"action": "approve"},
        )

    roadmap = result["roadmap"]
    if not isinstance(roadmap, LearningRoadmap):
        raise TypeError(
            f"预期 LearningRoadmap，实际为 {type(roadmap).__name__}"
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


# ---------------- 路由 2：决定生成、补读或保守停止 ----------------

def route_after_evidence(
    state: AgentState,
) -> Literal["enough_evidence", "read_more", "stop"]:
    """根据内容证据和读取限制决定下一步。"""
    evidence_items = state.get("repo_evidence") or []

    # 路径匹配证据不等于内容证据。
    has_content_evidence = any(
        bool((item.snippet or "").strip())
        for item in evidence_items
    )

    # 有内容证据时返回 enough_evidence。
    # 必须首先判断成功，避免第 2 次读取成功后被上限截断。
    if has_content_evidence:
        return "enough_evidence"

    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 2)

    # step_count 达到 max_steps 时返回 stop。
    if step_count >= max_steps:
        return "stop"

    budget = state.get("evidence_budget")

    # budget 存在并且 budget.stopped 为 True 时返回 stop。
    if budget is not None and budget.stopped:
        return "stop"

    candidates = state.get("evidence_candidates") or []
    attempted_files = set(
        state.get("read_evidence_files") or []
    )

    has_unread_candidate = any(
        path not in attempted_files
        for path in candidates
    )

    # 没有未读取的候选文件时返回 stop。
    if not has_unread_candidate:
        return "stop"

    # 以上条件都不满足时返回 read_more。
    return "read_more"

# ---------------- 路由 3：根据人工确认决定结束或重生成 ----------------

def route_after_confirmation(
    state: AgentState,
) -> Literal["approved", "revision_requested"]:
    """根据经过校验的人工确认状态选择下一步。"""
    status = state.get("confirmation_status")

    if status == "approved":
        return "approved"

    if status == "revision_requested":
        return "revision_requested"

    raise ValueError(
        "人工确认路由收到非法状态："
        f"{status!r}"
    )
