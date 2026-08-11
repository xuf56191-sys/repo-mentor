"""RepoMentor目标驱动的最小Tool Calling流程。"""

from __future__ import annotations

import json
from typing import Any
from pathlib import Path

from langchain.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from repo_mentor.llm_service import create_llm
from repo_mentor.models import TargetTask
from repo_mentor.repository_ranker import PROJECT_ROOT
from repo_mentor.repository_tools import (
    REPOSITORY_TOOLS,
)


# 第4题
TOOLS_BY_NAME = {}
for repo_tool in REPOSITORY_TOOLS:
    TOOLS_BY_NAME[repo_tool.name] = repo_tool


def build_messages(
    repository_path: str,
    target_task: TargetTask,
):
    """构造目标驱动的初始消息。"""

    system_message = SystemMessage(
        content=(
            "你是 RepoMentor 的仓库证据收集模块。\n"
            "\n"
            "你的任务是围绕用户当前的具体学习或贡献目标，"
            "只收集真正需要的仓库证据。\n"
            "\n"
            "请遵守以下规则：\n"
            "1. 不知道仓库有哪些真实文件时，可以使用 get_repo_tree。\n"
            "2. 需要了解 README、依赖、贡献说明时，"
            "可以使用 get_onboarding_docs。\n"
            "3. 已经有明确目标，需要确定最值得阅读哪些文件时，"
            "优先考虑 rank_target_files。\n"
            "4. 只有已经确认真实存在的文件，"
            "才可以使用 read_repo_file 读取内容。\n"
            "5. 不要为了通用了解一次读取大量源码。\n"
            "6. 当现有证据已经足够回答目标时，应停止调用工具。\n"
            "7. 不要猜测不存在的文件或尚未读取的源码内容。"
        )
    )

    human_message = HumanMessage(
        content=(
            f"本地仓库路径：{repository_path}\n"
            "\n"
            f"目标标题：{target_task.title}\n"
            f"目标描述：{target_task.description}\n"
            f"期望结果：{target_task.expected_outcome}\n"
            f"任务类型：{target_task.task_type}\n"
            "\n"
            "请根据这个具体目标判断目前是否需要调用仓库工具。"
            "如果需要，请只请求必要的工具。"
        )
    )

    return [
        system_message,
        human_message,
    ]

def request_tool_decision(
    messages,
):
    """让模型根据当前目标决定是否调用仓库工具。"""

    llm = create_llm(thinking_enabled=False)
    llm_with_tools = llm.bind_tools(REPOSITORY_TOOLS)
    ai_message = llm_with_tools.invoke(messages)

    return ai_message

def execute_tool_call(
    tool_call: dict[str, Any],
) -> ToolMessage:
    """执行一个模型请求的 Repository Tool。"""

    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    tool_id = tool_call["id"]

    repository_tool = TOOLS_BY_NAME.get(
        tool_name
    )

    if repository_tool is None:
        raise ValueError(
            f"未发现工具：{tool_name}"
        )

    tool_result = repository_tool.invoke(
        tool_args
    )

    tool_content = json.dumps(
        tool_result,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    return ToolMessage(
        content=tool_content,
        tool_call_id=tool_id,
        name=tool_name,
    )




def run_target_tool_calling(
    repository_path: str,
    target_task: TargetTask,
    *,
    max_rounds: int = 2,
):
    """运行有限轮次的目标驱动 Tool Calling。"""

    if max_rounds < 1:
        raise ValueError(
            "max_rounds 必须大于等于 1"
        )

    # 1. 构造最初的 SystemMessage + HumanMessage
    messages = build_messages(
        repository_path=repository_path,
        target_task=target_task,
    )

    # 2. 创建普通模型
    llm = create_llm(
        thinking_enabled=False
    )

    # 3. 给模型绑定 Repository Tools
    llm_with_tools = llm.bind_tools(
        REPOSITORY_TOOLS
    )

    total_tool_calls = 0

    # 4. 最多允许 max_rounds 轮工具调用
    for round_index in range(
        1,
        max_rounds + 1,
    ):
        print(
            "\n"
            + "=" * 60
        )
        print(
            f"第 {round_index} 轮模型决策"
        )
        print(
            "=" * 60
        )

        # 5. 模型根据当前 messages 决定：
        #    继续调用 Tool，还是直接回答
        ai_message = llm_with_tools.invoke(
            messages
        )

        # 非常重要：
        # 模型发出的 Tool Call 本身
        # 也必须进入消息历史
        messages.append(
            ai_message
        )

        tool_calls = (
            ai_message.tool_calls
        )

        # 6. 如果模型没有请求任何Tool
        #    说明它认为已有证据足够
        if not tool_calls:
            print(
                "模型没有继续请求 Tool。"
            )

            print(
                "\n"
                + "=" * 60
            )
            print(
                "最终回答"
            )
            print(
                "=" * 60
            )
            print(
                ai_message.content
            )

            print(
                f"\n总 Tool 调用次数："
                f"{total_tool_calls}"
            )

            return {
                "final_message": ai_message,
                "messages": messages,
                "tool_call_count": (
                    total_tool_calls
                ),
                "rounds": round_index,
            }

        # 7. 模型要求调用一个或多个Tool
        for index, tool_call in enumerate(
            tool_calls,
            start=1,
        ):
            total_tool_calls += 1

            print(
                f"\nTool Call {index}"
            )
            print(
                f"name: "
                f"{tool_call['name']}"
            )
            print(
                f"args: "
                f"{tool_call['args']}"
            )
            print(
                f"id: "
                f"{tool_call['id']}"
            )

            # 8. 真正执行模型请求的Tool
            tool_message = (
                execute_tool_call(
                    tool_call
                )
            )

            # 9. 把Tool执行结果放回消息历史
            messages.append(
                tool_message
            )

            print(
                "\nTool 执行完成"
            )
            print(
                f"name: "
                f"{tool_message.name}"
            )
            print(
                f"tool_call_id: "
                f"{tool_message.tool_call_id}"
            )

    # 10. 如果已经达到最大工具调用轮次，
    #     不再允许继续请求新Tool。
    print(
        "\n"
        + "=" * 60
    )
    print(
        "已达到最大 Tool Calling 轮次"
    )
    print(
        "=" * 60
    )

    # 使用没有绑定Tools的普通LLM，
    # 强制模型只根据当前已经获得的证据总结回答。
    final_instruction = HumanMessage(
        content=(
            "工具调用轮次已经结束。"
            "现在禁止继续请求或模拟任何工具调用，"
            "也不要输出 tool_calls、XML、DSML 或其他工具调用语法。"
            "请只根据当前 messages 中已经获得的真实工具结果"
            "给出最终总结。"
            "如果现有证据不足以完全回答目标，"
            "请明确说明还缺少哪些证据，"
            "但不要继续调用工具。"
        )
    )

    messages.append(
        final_instruction
    )

    final_message = llm.invoke(
        messages
    )

    messages.append(
        final_message
    )

    print(
        final_message.content
    )

    print(
        f"\n总 Tool 调用次数："
        f"{total_tool_calls}"
    )

    return {
        "final_message": final_message,
        "messages": messages,
        "tool_call_count": (
            total_tool_calls
        ),
        "rounds": max_rounds,
    }




PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


def main() -> None:
    # target_task = TargetTask(
    #     title=(
    #         "理解 RepoMentor 的目录树扫描流程"
    #     ),
    #     description=(
    #         "理解本地仓库路径校验、"
    #         "目录遍历、忽略规则和"
    #         "目录树生成之间的关系"
    #     ),
    #     task_type="understand_module",
    #     expected_outcome=(
    #         "能够说明从仓库路径输入"
    #         "到目录树生成的完整流程"
    #     ),
    #     reference=None,
    # )

    #A
    # target_task = TargetTask(
    #     title="查看 RepoMentor 的仓库结构",
    #     description=(
    #         "我现在只想知道这个仓库有哪些真实目录和文件，"
    #         "了解项目的大致目录结构。"
    #         "暂时不要读取任何源码文件内容。"
    #     ),
    #     task_type="understand_module",
    #     expected_outcome=(
    #         "能够看到仓库真实目录树，"
    #         "知道主要目录和文件分别位于哪里。"
    #     ),
    #     reference=None,
    # )

    #B
    # target_task = TargetTask(
    #     title="了解 RepoMentor 的项目介绍和贡献资料",
    #     description=(
    #         "我想先了解这个项目是做什么的、"
    #         "使用哪些主要依赖，以及是否存在贡献说明。"
    #         "当前不需要分析源码实现。"
    #     ),
    #     task_type="understand_module",
    #     expected_outcome=(
    #         "能够说明项目用途、主要依赖"
    #         "以及是否存在贡献相关文档。"
    #     ),
    #     reference=None,
    # )

    #D
    target_task = TargetTask(
        title="读取已经确认存在的 README.md",
        description=(
            "README.md 已经确认真实存在于仓库根目录。"
            "现在只需要读取 README.md 的真实内容，"
            "不要扫描目录树，也不要读取其他源码文件。"
        ),
        task_type="understand_module",
        expected_outcome=(
            "获得 README.md 的真实文本内容，"
            "并根据该内容进行简要说明。"
        ),
        reference="README.md",
    )

    result = run_target_tool_calling(
        repository_path=str(
            PROJECT_ROOT
        ),
        target_task=target_task,
        max_rounds=2,
    )

    print(
        "\n"
        + "=" * 60
    )
    print(
        "运行统计"
    )
    print(
        "=" * 60
    )

    print(
        "Tool调用次数：",
        result["tool_call_count"],
    )

    print(
        "Tool Calling轮次：",
        result["rounds"],
    )

if __name__ == "__main__":
    main()