"""最小 checkpoint + interrupt 演示。"""

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command, interrupt


class DemoState(TypedDict, total=False):
    """最小图的共享状态。"""

    topic: str
    status: str
    human_decision: dict[str, str]


def prepare_topic(state: DemoState) -> dict:
    """模拟准备一个等待确认的学习主题。"""
    return {
        "status": f"已准备主题：{state['topic']}",
    }


def human_review(state: DemoState) -> dict:
    """暂停图，等待用户确认。"""
    decision = interrupt({
        "question": "是否确认这个学习主题？",
        "topic": state["topic"],
        "allowed_actions": ["approve", "revise"],
    })

    return {
        "human_decision": decision,
        "status": "已收到人工决定",
    }


def finish(state: DemoState) -> dict:
    """人工确认完成后的最终节点。"""
    action = state["human_decision"]["action"]

    return {
        "status": f"流程完成，用户决定：{action}",
    }


graph = StateGraph(DemoState)

graph.add_node("prepare_topic", prepare_topic)
graph.add_node("human_review", human_review)
graph.add_node("finish", finish)

graph.add_edge(START, "prepare_topic")
graph.add_edge("prepare_topic", "human_review")
graph.add_edge("human_review", "finish")
graph.add_edge("finish", END)

# TODO 1：创建内存 checkpointer
checkpointer = InMemorySaver()

# TODO 2：编译时传入 checkpointer
app = graph.compile(checkpointer=checkpointer)

# TODO 3：为第一个会话设置 thread_id
config_a = {
    "configurable": {
        "thread_id":"learner_a"
    }
}

# 第一次执行会停在 human_review
first_result = app.invoke(
    {
        "topic": "学习 LangGraph checkpoint",
        "status": "",
    },
    config=config_a,
)

print("第一次执行返回：")
print(first_result)

print("中断问题：")
print(first_result["__interrupt__"][0].value)

# 使用相同 thread_id 恢复
resumed_result = app.invoke(
    Command(
        resume={
            "action": "approve",
        }
    ),
    config=config_a,
)

print("恢复后的结果：")
print(resumed_result)

# 第二个独立会话
config_b = {
    "configurable": {
        "thread_id": "learner-b",
    }
}

app.invoke(
    {
        "topic": "学习人工确认节点",
        "status": "",
    },
    config=config_b,
)

snapshot_a = app.get_state(config_a)
snapshot_b = app.get_state(config_b)

print("会话 A 的主题：")
print(snapshot_a.values["topic"])

print("会话 B 的主题：")
print(snapshot_b.values["topic"])

assert snapshot_a.values["topic"] == (
    "学习 LangGraph checkpoint"
)
assert snapshot_b.values["topic"] == (
    "学习人工确认节点"
)
assert resumed_result["status"] == (
    "流程完成，用户决定：approve"
)

print("CHECKPOINT DEMO PASSED")