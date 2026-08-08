"""安全生成本地代码仓库目录树。"""

from __future__ import annotations

from  dataclasses import dataclass,field
from  pathlib import Path
from repository_service import (
    RepositoryInfo,
    RepositoryPathError,
    validate_repository_path,
)
PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


#定义默认忽略目录：
DEFAULT_IGNORES_NAMES = {
    ".git",
    ".idea",
    ".venv",
    "venv",
    ".env",
    "__pycache__",
    ".pytest_cache",
    "outputs",
}

@dataclass
class TreeBuildResult():
    """仓库目录树生成结果"""
    tree:str
    file_count:int
    directory_count: int
    truncated:bool
    warnings:list[str] = field(
        default_factory=list
    )

@dataclass
class TreeBuildState:
    """目录树扫描过程中的内部状态。"""
    file_count: int = 0
    directory_count: int = 0
    truncated: bool = False
    warnings: list[str] = field(
        default_factory=list
    )

#用set集合，in查询速度比列表list快很多。
def should_ignore(path:Path,ignored_names:set[str],)->bool:
    """判断目录文件是否应该被忽略"""
    name = path.name
    res = path.name in ignored_names
    print(f"check {name}, ignore={res}")
    return res

def build_tree(
        repository_path:str|Path,
        *,
        max_deepth:int = 4,
        max_file:int = 200,
        ignored_names:set[str] | None = None
)->TreeBuildResult:
    """
        安全生成本地仓库目录树。

        Args:
            repository_path:
                已存在的本地仓库路径。
            max_depth:
                最大递归深度。
            max_files:
                最多扫描的文件数量。
            ignored_names:
                需要忽略的文件或目录名称。

        Returns:
            TreeBuildResult。
        """
    if max_deepth < 1:
        raise ValueError(f"max_deepth必须大于等于1")

    if max_file < 1:
        raise ValueError(f"max_file必须大于等于1")

    repository_info = validate_repository_path(repository_path)

    if ignored_names is None:
        ignored_names = set(DEFAULT_IGNORES_NAMES)
    else :
        ignored_names = set(ignored_names)

    state = TreeBuildState()

    lines = [f"{repository_info.name}/"]


    """
    directory：要扫描的文件夹绝对路径
    prefix：树形前缀字符串，比如 │ 、 、├── ，用来排版树的缩进，递归的时候不断拼接
    current_depth：当前递归到第几层；current_depth=0 最开始根目录
    """
    _walk_directory(
        directory = repository_info.absolute_path,
        prefix = " ",
        current_deepth = 0,
        max_deepth = max_deepth,
        max_file = max_file,
        ignored_names=ignored_names,
        state=state,
        lines=lines,
    )
    return TreeBuildResult(
        tree="\n".join(lines),
        file_count=state.file_count,
        directory_count = state.directory_count,
        truncated = state.truncated,
        warnings = state.warnings,
    )

def _walk_directory(
    *,
    directory: Path,
    prefix: str,
    current_deepth: int,
    max_deepth: int,
    max_file: int,
    ignored_names: set[str],
    state: TreeBuildState,
    lines: list[str],
) -> None:
    """递归遍历目录并生成树形结构。"""

    if current_deepth >= max_deepth:
        return

    try:
        children = list(directory.iterdir())
    except PermissionError:
        state.warnings.append(
            f"没有权限读取目录：{directory}"
        )
        return
    except OSError as error:
        state.warnings.append(
            f"读取目录失败：{directory}，"
            f"原因：{error}"
        )
        return

    visible_children = [
        child
        for child in children
        if not should_ignore(
            child,
            ignored_names,
        )
    ]

    # 目录排在前面，同类型按名称排序。
    visible_children.sort(
        key=lambda path: (
            not path.is_dir(),
            path.name.lower(),
        )
    )

    for index, child in enumerate(
        visible_children
    ):
        if state.truncated:
            return

        is_last = (
            index == len(visible_children) - 1
        )

        branch = (
            "└── "
            if is_last
            else "├── "
        )

        child_prefix = (
            prefix
            + (
                "    "
                if is_last
                else "│   "
            )
        )

        # 不跟随符号链接。
        if child.is_symlink():
            lines.append(
                f"{prefix}{branch}"
                f"{child.name} [symlink]"
            )
            state.warnings.append(
                f"跳过符号链接：{child}"
            )
            continue

        try:
            if child.is_dir():
                state.directory_count += 1

                lines.append(
                    f"{prefix}{branch}"
                    f"{child.name}/"
                )

                if (
                    current_deepth + 1
                    < max_deepth
                ):
                    _walk_directory(
                        directory=child,
                        prefix=child_prefix,
                        current_deepth=(
                            current_deepth + 1
                        ),
                        max_deepth=max_deepth,
                        max_file=max_file,
                        ignored_names=ignored_names,
                        state=state,
                        lines=lines,
                    )
                else:
                    lines.append(
                        f"{child_prefix}"
                        "└── ... [达到最大深度]"
                    )

            elif child.is_file():
                if (
                    state.file_count
                    >= max_file
                ):
                    lines.append(
                        f"{prefix}"
                        "... [达到最大文件数量]"
                    )

                    state.truncated = True

                    state.warnings.append(
                        "目录树已截断："
                        f"文件数量达到{max_file}。"
                    )
                    return

                state.file_count += 1

                lines.append(
                    f"{prefix}{branch}"
                    f"{child.name}"
                )

        except OSError as error:
            state.warnings.append(
                f"无法读取路径：{child}，"
                f"原因：{error}"
            )

def print_tree_result(
    result: TreeBuildResult,
) -> None:
    """打印目录树生成结果。"""

    print("=" * 60)
    print("仓库目录树")
    print("=" * 60)
    print(result.tree)

    print("\n" + "=" * 60)
    print("扫描统计")
    print("=" * 60)

    print(
        f"文件数量：{result.file_count}"
    )
    print(
        f"目录数量：{result.directory_count}"
    )
    print(
        "是否截断："
        f"{'是' if result.truncated else '否'}"
    )

    if result.warnings:
        print("\n警告：")

        for warning in result.warnings:
            print(f"- {warning}")

def main() -> None:
    """运行目录树生成测试。"""

    try:
        result = build_tree(
            PROJECT_ROOT,
            max_deepth=4,
            max_file=200,
        )

        print_tree_result(result)

    except RepositoryPathError as error:
        print(
            f"仓库路径错误：{error}"
        )

    except ValueError as error:
        print(
            f"参数错误：{error}"
        )

    except Exception as error:
        print(
            "目录树生成失败："
            f"{type(error).__name__}: "
            f"{error}"
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()