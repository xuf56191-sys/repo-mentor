from repo_mentor.target_tool_calling import (
    TOOLS_BY_NAME,
)
from repo_mentor.repository_safeguards import (
    EvidenceBudget,
    invoke_with_retry,
    redact_for_log,
)

import json
from pathlib import Path

from langchain.messages import ToolMessage

from repo_mentor.target_tool_calling import (
    TOOLS_BY_NAME,
    execute_tool_call,
)

def test_tools_by_name_contains_repository_tools():
    """Repository Tool注册表应该包含四个核心工具。"""

    expected_tools = {
        "get_repo_tree",
        "get_onboarding_docs",
        "read_repo_file",
        "rank_target_files",
    }

    assert set(
        TOOLS_BY_NAME.keys()
    ) == expected_tools

    for tool_name, tool in (
        TOOLS_BY_NAME.items()
    ):
        assert tool.name == tool_name

def test_execute_tool_call_returns_matching_tool_message(
    tmp_path: Path,
):
    """Tool执行结果必须和原始tool call id对应。"""
    budget = EvidenceBudget(
        max_files=2,
        max_chars=10_000,
    )
    readme_path = (
        tmp_path / "README.md"
    )

    readme_path.write_text(
        "# Test Repository\n"
        "This is a test README.",
        encoding="utf-8",
    )

    fake_tool_call = {
        "name": "read_repo_file",
        "args": {
            "repository_path": str(
                tmp_path
            ),
            "relative_path": "README.md",
        },
        "id": "call_test_001",
        "type": "tool_call",
    }

    tool_message = execute_tool_call(
        fake_tool_call,
        budget
    )

    assert isinstance(
        tool_message,
        ToolMessage,
    )

    assert (
        tool_message.tool_call_id
        == "call_test_001"
    )

    assert (
        tool_message.name
        == "read_repo_file"
    )

    result = json.loads(
        tool_message.content
    )

    assert result["ok"] is True

    assert (
        result["source_path"]
        == "README.md"
    )

    assert (
        "Test Repository"
        in result["content"]
    )

    def test_budget_stops_when_char_limit_exceeded():
        budget = EvidenceBudget(
            max_files=4,
            max_chars=100,
        )

        budget.consume(
            file_count=1,
            char_count=80,
        )

        assert budget.stopped is False
        assert budget.used_chars == 80

        budget.consume(
            file_count=1,
            char_count=30,
        )

        assert budget.stopped is True

        # 第二次消费应该被拒绝
        assert budget.used_files == 1
        assert budget.used_chars == 80

        assert budget.stop_reason is not None
        assert "字符" in budget.stop_reason

def test_budget_stops_when_char_limit_exceeded():
    budget = EvidenceBudget(
        max_files=4,
        max_chars=100,
    )

    budget.consume(
        file_count=1,
        char_count=80,
    )

    assert budget.stopped is False
    assert budget.used_chars == 80

    budget.consume(
        file_count=1,
        char_count=30,
    )

    assert budget.stopped is True

    # 第二次消费应该被拒绝
    assert budget.used_files == 1
    assert budget.used_chars == 80

    assert budget.stop_reason is not None
    assert "字符" in budget.stop_reason