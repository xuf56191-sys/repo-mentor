from __future__ import annotations

import logging
from typing import Any
from dataclasses import dataclass
import time
from pydantic import ValidationError


logger = logging.getLogger(__name__)


SENSITIVE_KEYWORDS = {
    "api_key",
    "apikey",
    "token",
    "password",
    "secret",
    "authorization",
}



def redact_for_log(
    value: Any,
) -> Any:
    """
    递归隐藏日志中的敏感字段。
    遍历字典、列表等容器，当发现字典的键（不区分大小写）出现在
    SENSITIVE_KEYWORDS 中时，将其值替换为 "***"，其他情况递归处理。

    """
    # 处理字典：遍历键值对
    if isinstance(value, dict):
        redacted = {}

        for key, item_value in value.items():

            if isinstance(key, str):
                key_lower = key.lower()

                is_sensitive = any(keyword in key_lower for keyword in SENSITIVE_KEYWORDS)
            else:
                is_sensitive = False

            if is_sensitive:
                redacted[key] = ("***REDACTED***")
            else:
                redacted[key] = (redact_for_log(item_value))

        return redacted
    # 处理列表或元组：递归处理每个元素，并保持原类型
    if isinstance(value,list):
        return [redact_for_log(item) for item in value]
    if isinstance(value,tuple):
        return tuple(redact_for_log(item) for item in value)
    # 其他基础类型（int, float, str, bool, None 等）直接返回
    return value

from dataclasses import dataclass


@dataclass
class EvidenceBudget:
    max_files: int = 4
    max_chars: int = 30_000

    used_files: int = 0
    used_chars: int = 0

    stopped: bool = False
    stop_reason: str | None = None

    def __post_init__(self) -> None:
        if self.max_files < 1:
            raise ValueError(
                "max_files必须大于等于1"
            )

        if self.max_chars < 1:
            raise ValueError(
                "max_chars必须大于等于1"
            )

    def can_consume(
        self,
        file_count: int,
        char_count: int,
    ) -> bool:
        if file_count < 0:
            raise ValueError(
                "file_count不能小于0"
            )

        if char_count < 0:
            raise ValueError(
                "char_count不能小于0"
            )

        if self.stopped:
            return False

        if (
            self.used_files + file_count
            > self.max_files
        ):
            return False

        if (
            self.used_chars + char_count
            > self.max_chars
        ):
            return False

        return True

    def consume(
        self,
        file_count: int,
        char_count: int,
    ) -> None:
        if not self.can_consume(
            file_count,
            char_count,
        ):
            if not self.stopped:
                if (
                    self.used_files
                    + file_count
                    > self.max_files
                ):
                    self.stop(
                        "文件数超限："
                        f"已用 "
                        f"{self.used_files}/"
                        f"{self.max_files}，"
                        f"本次试图读取 "
                        f"{file_count} 个文件"
                    )

                elif (
                    self.used_chars
                    + char_count
                    > self.max_chars
                ):
                    self.stop(
                        "字符数超限："
                        f"已用 "
                        f"{self.used_chars}/"
                        f"{self.max_chars}，"
                        f"本次试图读取 "
                        f"{char_count} 个字符"
                    )

            return

        self.used_files += file_count
        self.used_chars += char_count

        if self.used_files >= self.max_files:
            self.stop(
                "文件预算已耗尽 "
                f"({self.used_files}/"
                f"{self.max_files})"
            )

        elif self.used_chars >= self.max_chars:
            self.stop(
                "字符预算已耗尽 "
                f"({self.used_chars}/"
                f"{self.max_chars})"
            )

    def stop(
        self,
        reason: str,
    ) -> None:
        if not self.stopped:
            self.stopped = True
            self.stop_reason = reason

@dataclass
class ToolExecutionResult:
    result: Any
    elapsed_seconds: float
    attempts: int


def is_retryable_exception(
    error: Exception,
) -> bool:
    """判断异常是否值得再尝试一次。"""

    # 参数本身错误，重新执行没有意义
    if isinstance(
        error,
        (
            ValueError,
            ValidationError,
            FileNotFoundError,
            PermissionError,
        ),
    ):
        return False

    # 这些问题可能是暂时性的
    return isinstance(
        error,
        (
            TimeoutError,
            ConnectionError,
            OSError,
        ),
    )


RETRYABLE_ERROR_TYPES = {
    "TimeoutError",
    "ConnectionError",
    "OSError",
}


def is_retryable_result(
    result: Any,
) -> bool:
    """判断 Tool 返回的结构化失败是否值得重试。"""

    if not isinstance(result, dict):
        return False

    if result.get("ok") is not False:
        return False

    return (
        result.get("error_type")
        in RETRYABLE_ERROR_TYPES
    )

def invoke_with_retry(
    repository_tool,
    tool_args: dict[str, Any],
    *,
    max_retries: int = 1,
) -> ToolExecutionResult:
    """
    执行 Repository Tool。

    对暂时性失败最多重试 max_retries 次。
    """

    if max_retries < 0:
        raise ValueError(
            "max_retries不能小于0"
        )

    tool_name = getattr(
        repository_tool,
        "name",
        type(repository_tool).__name__,
    )

    attempts = 0

    overall_start = (
        time.perf_counter()
    )

    while attempts <= max_retries:
        attempts += 1

        try:
            result = (
                repository_tool.invoke(
                    tool_args
                )
            )

            # Tool自己返回了“可重试失败”
            if (
                is_retryable_result(result)
                and attempts <= max_retries
            ):
                logger.warning(
                    "tool_retry "
                    "name=%s attempt=%d",
                    tool_name,
                    attempts,
                )
                continue

            elapsed = (
                time.perf_counter()
                - overall_start
            )

            return ToolExecutionResult(
                result=result,
                elapsed_seconds=elapsed,
                attempts=attempts,
            )

        except Exception as error:
            retryable = (
                is_retryable_exception(
                    error
                )
            )

            if (
                retryable
                and attempts <= max_retries
            ):
                logger.warning(
                    "tool_retry "
                    "name=%s attempt=%d "
                    "error_type=%s",
                    tool_name,
                    attempts,
                    type(error).__name__,
                )
                continue

            # 最终失败也不再向外抛，
            # 转成结构化结果
            elapsed = (
                time.perf_counter()
                - overall_start
            )

            logger.error(
                "tool_failed "
                "name=%s attempts=%d "
                "error_type=%s",
                tool_name,
                attempts,
                type(error).__name__,
            )

            return ToolExecutionResult(
                result={
                    "ok": False,
                    "error_type": (
                        type(error).__name__
                    ),
                    "message": str(error),
                },
                elapsed_seconds=elapsed,
                attempts=attempts,
            )

def summarize_tool_result(
    tool_name: str,
    result: Any,
) -> dict[str, Any]:
    """生成安全、简短的 Tool 结果摘要。"""

    if not isinstance(result, dict):
        return {
            "result_type": (
                type(result).__name__
            )
        }

    if result.get("ok") is False:
        return {
            "ok": False,
            "error_type": (
                result.get("error_type")
            ),
        }

    if tool_name == "read_repo_file":
        content = result.get(
            "content",
            "",
        )

        return {
            "ok": True,
            "source_path": (
                result.get("source_path")
            ),
            "chars": len(content),
        }

    if tool_name == "get_onboarding_docs":
        documents = result.get(
            "documents",
            [],
        )

        return {
            "ok": True,
            "document_count": (
                len(documents)
            ),
            "source_paths": [
                document.get(
                    "source_path"
                )
                for document
                in documents
            ],
            "chars": sum(
                len(
                    document.get(
                        "content",
                        "",
                    )
                )
                for document
                in documents
            ),
        }

    if tool_name == "get_repo_tree":
        return {
            "ok": True,
            "file_count": (
                result.get("file_count")
            ),
            "directory_count": (
                result.get(
                    "directory_count"
                )
            ),
            "truncated": (
                result.get("truncated")
            ),
        }

    if tool_name == "rank_target_files":
        files = result.get(
            "files",
            [],
        )

        return {
            "ok": True,
            "candidate_count": len(files),
            "top_files": [
                item.get("file_path")
                for item in files[:5]
            ],
        }

    return {
        "ok": result.get(
            "ok",
            True,
        )
    }

def calculate_evidence_cost(
    tool_name: str,
    result: Any,
) -> tuple[int, int]:
    """
    计算 Tool 结果进入模型上下文时
    消耗的文件数和字符数。
    """

    if not isinstance(result, dict):
        return 0, 0

    if result.get("ok") is False:
        return 0, 0

    if tool_name == "read_repo_file":
        content = result.get(
            "content",
            "",
        )

        return (
            1,
            len(content),
        )

    if tool_name == "get_onboarding_docs":
        documents = result.get(
            "documents",
            [],
        )

        file_count = len(documents)

        char_count = sum(
            len(
                document.get(
                    "content",
                    "",
                )
            )
            for document
            in documents
        )

        return (
            file_count,
            char_count,
        )

    return 0, 0
