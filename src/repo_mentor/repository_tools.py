"""RepoMentor 的仓库证据 LangChain Tools。"""
from __future__ import  annotations

# from msilib.schema import Class

from pathlib import Path
from typing import Any
from langchain.tools import tool
from pydantic import BaseModel,ConfigDict,Field

from repo_mentor.models import TargetTask
from repo_mentor.repository_ranker import (
    rank_target_files as rank_target_files_core,
)
from repo_mentor.repository_reader import (
    read_repository_onboarding_docs,
    read_text_document,
)
from repo_mentor.repository_service import (
    RepositoryPathError,
    validate_repository_path,
)
from repo_mentor.repository_tree import (
    DEFAULT_IGNORED_NAMES,
    build_tree,
    should_ignore,
)

# ============================================================
# Tool 输入 Schema
# ============================================================

class ToolInputModel(BaseModel):
    """RepoMentor Tool 输入模型基类。"""
    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=True,
    )

class GetRepoTreeInput(ToolInputModel):
    """get_repo_tree 参数。"""
    repository_path:str = Field(
        min_length=1,
        description="需要分析的本地代码仓库路径。",
    )
    max_depth:int = Field(
        default=4,
        ge=1,
        le=10,
        description="目录树最大扫描深度",
    )
    max_files:int=Field(
        default=200,
        ge=1,
        le=1000,
        description="最多扫描的文件数量",
    )
class GetOnboardingDocsInput(ToolInputModel):
    """get_onboarding_docs 参数。"""
    repository_path:str = Field(
        min_length=1,
        description="需要读取入门资料的本地仓库路径",
    )

class ReadRepoFileInput(ToolInputModel):
    """read_repo_file 参数。"""
    repository_path: str = Field(
        min_length=1,
        description="本地仓库根目录",
    )
    relative_path:str = Field(
        min_length=1,
        description="相对于仓库根目录的真实文件路径，"
                    "例如 src/repo_mentor/models.py。",

    )

class RankTargetFilesInput(ToolInputModel):
    """rank_target_files 参数。"""
    repository_path: str = Field(
        min_length=1,
        description="需要分析的本地仓库路径。"
    )
    target_task:TargetTask = Field(
        description="用户当前希望完成的具体学习或贡献目标。",
    )
    top_n:int = Field(
        default=8,
        ge=1,
        le=20,
        description="最多返回多少个相关文件。",
    )

# ============================================================
# 公共辅助函数
# ============================================================

def build_error_result(
        error:Exception,
)->dict[str,Any]:
    """将可预期的执行异常转换为结构化结果。"""
    return {
        "ok":False,
        "error_type":type(error).__name__,
        "message":str(error),
    }

def ensure_safe_relative_path(
        relative_path:str,
)->None:
    """阻止 Tool 主动读取敏感或忽略路径。"""
    candidate = Path(relative_path)

    #.is_absolute():判断是不是绝对路径
    if candidate.is_absolute():
        raise ValueError(
            f"read_repo_file只接受仓库内部的相对路径。"
        )
    for part in candidate.parts:
        if part in {"","."}:
            continue
        if should_ignore(
            Path(part),
            DEFAULT_IGNORED_NAMES
        ):
            raise ValueError(f"禁止读取被忽略或敏感路径：{relative_path}")

# ============================================================
# Tool 1：目录树
# ============================================================

@tool(args_schema=GetRepoTreeInput)
def get_repo_tree(
        repository_path:str,
        max_depth:int = 4,
        max_files:int = 200,
)->dict[str,Any]:
    """
        获取真实本地仓库的目录树。
        当需要了解仓库结构、确认真实文件路径，
        或寻找下一步应该读取哪些文件时使用。
        此工具只返回目录结构，不读取源码内容。
        """
    try:
        result = build_tree(
            repository_path,
            max_depth=max_depth,
            max_files=max_files,
        )
        return{
            "ok": True,
            "tree": result.tree,
            "file_count": result.file_count,
            "directory_count": result.directory_count,
            "truncated": result.truncated,
            "warnings": result.warnings,
        }

    except (RepositoryPathError,ValueError,OSError) as error :
        return  build_error_result(error)

# ============================================================
# Tool 2：README / CONTRIBUTING 等
# ============================================================

@tool(args_schema=GetOnboardingDocsInput)
def get_onboarding_docs(
        repository_path:str,
)->dict[str,Any]:
    """
        读取真实仓库的入门与贡献资料。

        当需要了解项目用途、安装方式、依赖、
        CONTRIBUTING 贡献要求或 docs 入口时使用。

        不应该用此工具读取任意源码文件。
        """
    try:
        result = read_repository_onboarding_docs(repository_path)
        documents = []
        for document in result.documents:
            documents.append(
                {
                    "document_type": (
                        document.document_type
                    ),
                    "source_path": (
                        document.relative_path
                    ),
                    "size_bytes": (
                        document.size_bytes
                    ),
                    "content": document.content,
                }
            )
        return {
            "ok": True,
            "repository_name": (
                result.repository_name
            ),
            "documents": documents,
            "warnings": result.warnings,
        }
    except (
            RepositoryPathError,
            ValueError,
            OSError,
    ) as error:
        return build_error_result(error)

# ============================================================
# Tool 3：单个真实文件读取
# ============================================================

@tool(args_schema=ReadRepoFileInput)
def read_repo_file(
        repository_path:str,
        relative_path:str,
)->dict[str,Any]:
    """
        读取仓库中的一个已知文本文件。

        只有当目录树或目标文件排序已经提供了真实文件路径，
        并且确实需要确认该文件内部内容时才使用。

        不用于批量扫描仓库，也不允许读取敏感或忽略路径。
        """
    try:
        ensure_safe_relative_path(relative_path)
        repository_info = (
            validate_repository_path(repository_path)
        )
        document = read_text_document(
            repository_root=(
                repository_info.absolute_path
            ),
            relative_path=relative_path,
            document_type="repository_file",
        )
        if document is None:
            return {
                "ok":False,
                "error_type":"FileNotFoundError",
                "message":(
                    f"没有找到可读取的仓库文件："
                    f"{relative_path}"
                ),
            }
        return {
            "ok": True,
            "source_path": (
                document.relative_path
            ),
            "size_bytes": (
                document.size_bytes
            ),
            "content": document.content,
        }

    except (
        RepositoryPathError,
        ValueError,
        OSError,
    ) as error:
        return build_error_result(error)

# ============================================================
# Tool 4：目标相关文件排序
# ============================================================


@tool(args_schema=RankTargetFilesInput)
def rank_target_files(
    repository_path: str,
    target_task: TargetTask | dict,
    top_n: int = 8,
) -> dict[str, Any]:
    """
    根据用户当前目标对真实仓库文件进行相关性排序。

    当用户已经有明确学习目标、Issue 或贡献任务，
    需要确定下一步最值得阅读哪些真实文件时使用。

    此工具返回候选文件、分数、理由和证据，
    但不会自动读取所有候选文件的源码。
    """

    try:
        if isinstance(
            target_task,
            TargetTask,
        ):
            validated_target = target_task
        else:
            validated_target = (
                TargetTask.model_validate(
                    target_task
                )
            )

        ranked_files = (
            rank_target_files_core(
                repository_path=repository_path,
                target_task=validated_target,
                top_n=top_n,
            )
        )

        return {
            "ok": True,
            "target": (
                validated_target.title
            ),
            "files": [
                item.model_dump(
                    mode="json"
                )
                for item in ranked_files
            ],
        }

    except (
        RepositoryPathError,
        ValueError,
        OSError,
    ) as error:
        return build_error_result(error)


# ============================================================
# 后续给模型绑定时统一使用
# ============================================================


REPOSITORY_TOOLS = [
    get_repo_tree,
    get_onboarding_docs,
    read_repo_file,
    rank_target_files,
]

"""
| Tool                  | 什么时候用             | 不应该做什么      |
| --------------------- | ----------------- | ----------- |
| `get_repo_tree`       | 不知道仓库有哪些真实文件      | 不读源码        |
| `get_onboarding_docs` | 了解 README、贡献方式、依赖 | 不读取任意 `.py` |
| `rank_target_files`   | 已有明确目标，要决定先看哪些文件  | 不猜源码内部实现    |
| `read_repo_file`      | 已经确定某个真实文件值得读     | 不批量读取整个仓库   |

"""
