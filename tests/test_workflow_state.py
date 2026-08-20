"""AgentState 的单元测试：默认值、reducer 语义与安全边界。"""

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

def test_create_initial_state_has_bounded_evidence_defaults():
    """初始状态应限制最多补读两个文件。"""
    state = create_initial_state(
        make_learner(),
        make_target(),
    )
    budget = state["evidence_budget"]

    assert state["step_count"] == 0
    assert state["max_steps"] == 2
    assert state["evidence_candidates"] == []
    assert state["read_evidence_files"] == []
    assert state["evidence_stop_reason"] is None

    assert budget.max_files == 2
    assert budget.used_files == 0
    assert budget.used_chars == 0
    assert budget.stopped is False
    assert budget.stop_reason is None

def test_initial_states_do_not_share_mutable_budget():
    """两个工作流不能共享预算用量。"""
    first = create_initial_state(
        make_learner(),
        make_target(),
    )
    second = create_initial_state(
        make_learner(),
        make_target(),
    )

    first_budget = first["evidence_budget"]
    second_budget = second["evidence_budget"]

    assert first_budget is not second_budget
    assert (
        first["evidence_candidates"]
        is not second["evidence_candidates"]
    )
    assert (
        first["read_evidence_files"]
        is not second["read_evidence_files"]
    )

    first_budget.consume(
        file_count=1,
        char_count=100,
    )

    assert first_budget.used_files == 1
    assert first_budget.used_chars == 100

    assert second_budget.used_files == 0
    assert second_budget.used_chars == 0

def test_initial_state_has_confirmation_defaults():
    """人工确认状态应从尚未请求确认开始。"""
    state = create_initial_state(
        make_learner(),
        make_target(),
    )

    assert (
        state["confirmation_status"]
        == "not_requested"
    )
    assert state["human_confirmation"] is None
    assert state["revision_count"] == 0

    # thread_id 属于调用配置，不属于业务 State。
    assert "thread_id" not in state