"""RepoMentor 自适应工作流的共享状态（LangGraph State）。

设计原则：
1. 每个字段有明确的产生节点与消费节点（见文件底部表格）；
2. State 不保存 API Key 等敏感信息（validate_state_no_secrets）；
3. 不放无用整段源码，只放结构化证据（RepositoryEvidence）。
"""

from __future__ import annotations




import operator
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages

from repo_mentor.models import (
    LearnerProfile,
    LearningRoadmap,
    RepositoryEvidence,
    TargetTask,
)
from repo_mentor.repository_safeguards import SENSITIVE_KEYWORDS


class AgentState(TypedDict, total=False):
    """所有节点共享的状态。字段均为可选，从空 dict 起步。"""

    # ---------- 输入 ----------
    learner_profile: LearnerProfile          # 产生: analyze_learner/用户; 消费: generate_roadmap 等
    target_task: TargetTask                  # 产生: analyze_target/用户; 消费: collect_evidence 等

    # ---------- 证据 ----------
    repo_evidence: Annotated[
        list[RepositoryEvidence],
        operator.add,                        # 累积: 多次 collect_evidence 追加
    ]

    # ---------- 输出 ----------
    roadmap: LearningRoadmap                 # 产生: generate_roadmap; 消费: 最终输出

    # ---------- 掌握度（V0.7 再定义正式模型，今天用 dict 占位） ----------
    mastery: dict[str, Any]                  # 产生: evaluate_answers/update_profile; 消费: replan

    # ---------- 运行时 ----------
    messages: Annotated[list, add_messages]  # 产生/消费: 所有节点, LLM 对话历史
    errors: Annotated[list[str], operator.add]  # 产生: 任意节点捕获的错误
    step_count: int                          # 产生: 每个节点自增; 消费: 终止条件

    repository_path: str  # 产生: 用户输入; 消费: collect_evidence
    learner_analysis: dict[str, Any]  # 产生: analyze_learner; 消费: generate_roadmap
    target_analysis: dict[str, Any]  # 产生: analyze_target; 消费: collect_evidence
    repo_readme: str  # 产生: collect_evidence; 消费: generate_roadmap
    repo_tree: str  # 产生: collect_evidence; 消费: generate_roadmap

def create_initial_state(
        learner_profile:LearnerProfile,
        target_task:TargetTask,
)->dict:
    """构造带默认值的初始state，避免节点读取时keyError."""
    return {
        "learner_profile":learner_profile,
        "target_task":target_task,
        "repo_evidence":[],
        "messages":[],
        "errors":[],
        "step_count":0,
    }


def validate_state_no_secrets(state:Any)->bool:
    """递归检查 State 中是否有敏感字段名。

        只检查字典键名（不扫描正文），避免把普通单词误判为密钥；
        发现敏感键名返回 False。
    """
    if isinstance(state,dict):
        for key,value in state.items():
            key_lower = str(key).lower()
            if any(k in key_lower for k in SENSITIVE_KEYWORDS):
                return False
            if not validate_state_no_secrets(value):
                return False
    elif isinstance(state,(list,tuple)):
        return all(
            validate_state_no_secrets(item)
            for item in state
        )
    return  True




# 字段来源与使用节点表（小目标 2 交付物）：
# | 字段            | 产生节点              | 消费节点                          |
# | learner_profile | analyze_learner/用户  | analyze_target、generate_roadmap   |
# | target_task     | analyze_target/用户   | collect_evidence、generate_roadmap |
# | repo_evidence   | collect_evidence      | generate_roadmap、generate_assessment |
# | roadmap         | generate_roadmap      | 最终输出、replan                   |
# | mastery         | evaluate_answers/update_profile | replan                      |
# | messages        | 所有节点              | 所有节点                          |
# | errors          | 任意节点              | 终止节点/用户提示                  |
# | step_count      | 每个节点自增          | 终止条件（max_steps）              |
# | repository_path | 用户输入            | collect_evidence                |
# | learner_analysis| analyze_learner     | generate_roadmap                |
# | target_analysis | analyze_target      | collect_evidence                |
# | repo_readme     | collect_evidence    | generate_roadmap                |
# | repo_tree       | collect_evidence    | generate_roadmap                |