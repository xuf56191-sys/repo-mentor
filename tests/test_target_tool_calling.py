from repo_mentor.target_tool_calling import (
    TOOLS_BY_NAME,
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
        fake_tool_call
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