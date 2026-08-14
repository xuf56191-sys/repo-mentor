from repo_mentor.repository_service import (
    RepositoryPathError,
    validate_repository_path,
)
import json

from langchain.messages import ToolMessage
from repo_mentor.models import TargetTask

from repo_mentor.target_tool_calling import (
    configure_logging,
    run_target_tool_calling,
)

from repo_mentor.repository_ranker import (
    rank_target_files,
)


REPOSITORIES = {
    "R1-RepoMentor": (
        r"D:\PPT文档\agent初学代码\repo-mentor"
    ),
    "R2-ItsDangerous": (
        r"D:\PPT文档\agent初学代码"
        r"\repo-validation\itsdangerous"
    ),
    "R3-Pipfile": (
        r"D:\PPT文档\agent初学代码"
        r"\repo-validation\pipfile"
    ),
}


def validate_repositories() -> None:
    print("=" * 70)
    print("V0.4 Repository Validation")
    print("=" * 70)

    for repository_name, repository_path in (
        REPOSITORIES.items()
    ):
        print(f"\n[{repository_name}]")
        print(f"input_path: {repository_path}")

        try:
            repository_info = (
                validate_repository_path(
                    repository_path
                )
            )

            print("status: PASS")
            print(
                "name:",
                repository_info.name,
            )
            print(
                "absolute_path:",
                repository_info.absolute_path,
            )
            print(
                "has_git_metadata:",
                repository_info.has_git_metadata,
            )

        except RepositoryPathError as error:
            print("status: FAIL")
            print("error:", error)

CASE_R1_A = TargetTask(
    title=(
        "理解RepoMentor的目录树扫描流程"
    ),
    description=(
        "理解本地仓库路径校验、目录遍历、"
        "忽略规则和目录树生成之间的关系"
    ),
    task_type="understand_module",
    expected_outcome=(
        "能够说明从仓库路径输入"
        "到目录树生成的完整流程"
    ),
    reference=None
)

CASE_R1_B = TargetTask(
    title=(
        "理解 RepoMentor 的仓库工具"
        "如何被测试"
    ),
    description=(
        "找到仓库证据工具相关的核心实现文件"
        "和测试文件，理解测试如何验证 "
        "Repository Tools 的主要行为。"
    ),
    task_type="understand_module",
    expected_outcome=(
        "能够指出关键 Tool 实现文件"
        "和对应测试文件，并说明测试"
        "主要验证了哪些行为。"
    ),
    reference=None,
)

CASE_R2_A = TargetTask(
    title=(
        "理解 ItsDangerous 的数据签名"
        "与恢复流程"
    ),
    description=(
        "理解数据从序列化、签名到验证和恢复"
        "之间的核心实现关系，"
        "找到最值得阅读的源码文件。"
    ),
    task_type="understand_module",
    expected_outcome=(
        "能够指出数据签名与反序列化验证"
        "相关的核心文件，并说明"
        "主要实现之间的关系。"
    ),
    reference=None,
)

CASE_R2_B = TargetTask(
    title=(
        "理解 ItsDangerous 的序列化功能"
        "如何被测试"
    ),
    description=(
        "找到序列化和签名相关的核心实现文件"
        "及测试文件，理解测试如何验证"
        "正常序列化、篡改检测和异常行为。"
    ),
    task_type="understand_module",
    expected_outcome=(
        "能够指出核心实现与对应测试，"
        "并说明测试覆盖的主要行为。"
    ),
    reference=None,
)

CASE_R3_A = TargetTask(
    title=(
        "理解 Pipfile 的配置解析核心流程"
    ),
    description=(
        "理解 Pipfile 配置内容如何被读取和解析，"
        "找到最值得阅读的核心实现文件。"
    ),
    task_type="understand_module",
    expected_outcome=(
        "能够指出 Pipfile 解析相关的核心源码文件，"
        "并说明主要解析职责。"
    ),
    reference=None,
)

CASE_R3_B = TargetTask(
    title=(
        "理解 Pipfile 解析功能如何被测试"
    ),
    description=(
        "找到 Pipfile 解析功能相关的实现文件"
        "和测试文件，理解测试"
        "如何验证配置解析行为。"
    ),
    task_type="understand_module",
    expected_outcome=(
        "能够指出关键解析实现及对应测试，"
        "并说明测试主要覆盖哪些解析行为。"
    ),
    reference=None,
)

CASES = [
    ("R1-A", REPOSITORIES["R1-RepoMentor"], CASE_R1_A),
    ("R1-B", REPOSITORIES["R1-RepoMentor"], CASE_R1_B),
    ("R2-A", REPOSITORIES["R2-ItsDangerous"], CASE_R2_A),
    ("R2-B", REPOSITORIES["R2-ItsDangerous"], CASE_R2_B),
    ("R3-A", REPOSITORIES["R3-Pipfile"], CASE_R3_A),
    ("R3-B", REPOSITORIES["R3-Pipfile"], CASE_R3_B),
]

def run_case(
        case_id:str,
        repository_path:str,
        target_task:TargetTask,
)->dict:
    print("\n")
    print("="*50)
    print(f"case_id:{case_id}")
    print("=" * 50)
    print(f"repository_path:{repository_path}")
    print(f"Target:{target_task.title}")

    result = run_target_tool_calling(
        repository_path = repository_path,
        target_task = target_task,
        max_rounds=3,
        max_evidence_chars=40_000,
        max_evidence_files = 4
    )
    return result


def run_three_repo_ranking_demo() -> None:
    """三个仓库 × 六个目标，只跑文件排序（不调用 LLM）。"""
    print("=" * 70)
    print("V0.4 Three-Repository Ranking Demo")
    print("=" * 70)

    for case_id, repository_path, target_task in CASES:
        print(f"\n[{case_id}] {target_task.title}")

        ranked = rank_target_files(
            repository_path=repository_path,
            target_task=target_task,
            top_n=8,
        )

        for index, item in enumerate(
            ranked,
            start=1,
        ):
            print(
                f"  {index}. {item.file_path} "
                f" score={item.score}"
            )


def run_all_cases() -> None:
    """按顺序运行六个 Case 的完整 Tool Calling（需要 LLM）。"""
    for case_id, repository_path, target_task in CASES:
        print(f"\n{'#' * 70}")
        print(f"Case {case_id}")
        print(f"{'#' * 70}")

        result = run_case(
            case_id,
            repository_path,
            target_task,
        )

        print_case_summary(result)


def print_case_summary(
    result: dict,
) -> None:
    print("\n")
    print("-" * 70)
    print("CASE SUMMARY")
    print("-" * 70)

    messages = result["messages"]

    print("\n[Tool Results]")

    for message in messages:
        if not isinstance(
            message,
            ToolMessage,
        ):
            continue

        print(
            f"\nTool: {message.name}"
        )
        print(
            f"tool_call_id: "
            f"{message.tool_call_id}"
        )

        try:
            data = json.loads(
                message.content
            )
        except json.JSONDecodeError:
            print(
                "result: 非JSON结果"
            )
            continue

        if message.name == (
            "rank_target_files"
        ):
            print("Ranked Files:")

            ranked_files = (
                data.get("files", [])
            )

            for index, item in enumerate(
                ranked_files,
                start=1,
            ):
                print(
                    f"{index}. "
                    f"{item.get('file_path')} "
                    f"score="
                    f"{item.get('score')}"
                )

        elif message.name == (
            "read_repo_file"
        ):
            content = data.get(
                "content",
                "",
            )

            print(
                "source_path:",
                data.get("source_path"),
            )
            print(
                "chars:",
                len(content),
            )

        elif message.name == (
            "get_onboarding_docs"
        ):
            documents = data.get(
                "documents",
                [],
            )

            print(
                "documents:",
                [
                    document.get(
                        "source_path"
                    )
                    for document
                    in documents
                ],
            )

        elif message.name == (
            "get_repo_tree"
        ):
            print(
                "file_count:",
                data.get("file_count"),
            )
            print(
                "directory_count:",
                data.get(
                    "directory_count"
                ),
            )

    budget = result["budget"]

    print("\n[Budget]")
    print(
        "used_files:",
        f"{budget.used_files}"
        f"/{budget.max_files}",
    )
    print(
        "used_chars:",
        f"{budget.used_chars}"
        f"/{budget.max_chars}",
    )
    print(
        "stopped:",
        budget.stopped,
    )
    print(
        "stop_reason:",
        budget.stop_reason,
    )

    print("\n[Statistics]")
    print(
        "tool_call_count:",
        result["tool_call_count"],
    )
    print(
        "rounds:",
        result["rounds"],
    )

    print("\n[Final Answer]")
    print(
        result[
            "final_message"
        ].content
    )

def main() -> None:
    configure_logging()
    validate_repositories()
    run_three_repo_ranking_demo()
    # 完整六 Case 的 Tool Calling 验证（需要 LLM，耗时/费用更高）：
    run_all_cases()


if __name__ == "__main__":
    main()