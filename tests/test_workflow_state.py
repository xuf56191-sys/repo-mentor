"""AgentState 的单元测试：默认值、reducer 语义与安全边界。"""
from tkinter.constants import CURRENT

from repo_mentor.models import LearnerProfile, TargetTask
from repo_mentor.workflow_state import (
    create_initial_state,
    validate_state_no_secrets,
)

def make_learner()->LearnerProfile:
    return LearnerProfile(
        current_level="beginner",
        known_skills=["python"],
        learning_goal ="理解目录树扫描",
        daily_hours=2.0,
        available_days=7,
    )

def make_target()->TargetTask:
    return  TargetTask(
        title="理解目录树扫描",
        description = "理解仓库目录树生成流程",
        task_type = "understand_module",
        expected_outcome = "能说明目录树生成流程",
    )

def test_create_initial_state_defaults():
    state = create_initial_state(make_learner(),make_target())

    assert state["repo_evidence"] ==[]
    assert state["messages"] == []
    assert state["errors"] == []
    assert state["step_count"] == 0

def test_errors_accumulate():
    # 模拟 LangGraph 的 operator.add 语义：追加而不是覆盖
    state = create_initial_state(make_learner(),make_target())
    state["errors"] = state["errors"] + ["first"]
    state["errors"] = state["errors"] + ["second"]

def test_step_count_overwrites():
    state = create_initial_state(make_learner(), make_target())
    state["step_count"] = 1
    state["step_count"] = 2
    assert state["step_count"] == 2

def test_validate_state_no_secrets_detects_key():
    assert validate_state_no_secrets({"api_key":"x"}) is False
    assert validate_state_no_secrets({"nested": {"token": "y"}}) is False
    assert validate_state_no_secrets({"data": {"password": "z"}}) is False

def test_validate_state_no_secrets_accepts_normal():
    state = create_initial_state(make_learner(), make_target())
    state["repo_evidence"] = [
        {"source_path": "a.py", "reason": "token 只是普通单词"}
    ]

    assert validate_state_no_secrets(state) is True