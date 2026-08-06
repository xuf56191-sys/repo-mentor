"""本地代码仓库路径校验服务。"""

from __future__ import  annotations

from dataclasses import dataclass
from pathlib import Path

from src.repo_mentor.main import PROJECT_ROOT

PROJECT_ROOT = Path(__file__).resolve().parents[2]

class RepositoryPathError(ValueError):
    """本地仓库路径无效"""

@dataclass(frozen= True)
class RepositoryInfo:
    """经过校验的本地仓库基础信息。"""
    name:str
    absolute_path:Path
    has_git_metadata: bool

def normalize_path_text(path_value:str|Path) -> str:
    """
        将用户输入的路径转换成可处理的字符串。

        同时处理用户从文件管理器复制路径时可能带上的引号。
        """
    path_text = str(path_value).strip()

    if (len(path_text)>=2 and path_text[0] == path_text[-1] and path_text[0] in {"'",'"'}):
        path_text = path_text[1:-1].strip()

    if not path_text:

        raise RepositoryPathError("仓库路径不能为空，请输入一个本地文件夹路径。")
    return path_text

def validate_repository_path(path_value:str|Path)->RepositoryInfo:
    """
        校验用户输入的本地仓库路径。

        Args:
            path_value: 用户输入的文件夹路径。

        Returns:
            经过校验的RepositoryInfo对象。

        Raises:
            RepositoryPathError: 路径为空、不存在、不是目录或无法访问。
        """
    path_text = normalize_path_text(path_value)

    try:
        repository_path = (Path(path_text).expanduser().resolve())

    except OSError as error:
        raise RepositoryPathError(f"无法解析仓库路径：{path_text}") from error

    if not repository_path.exists():
        raise RepositoryPathError(f"仓库路径不存在：{repository_path}")

    if not repository_path.is_dir():
        raise RepositoryPathError(f"仓库路径不是文件夹：{repository_path}")

    try:
        # 尝试实际访问目录，避免路径存在但当前用户无法读取。
        next(repository_path.iterdir(),None)
    except OSError as error:
        raise RepositoryPathError(f"没有权限访问文件夹：{path_text}")

    except OSError as error:
        raise RepositoryPathError(f"读取文件夹失败：{path_text}")
    return  RepositoryInfo(
        name = repository_path.name,
        absolute_path = repository_path,
        has_git_metadata=(
                repository_path / ".git"
        ).exists()
    )

def print_repository_info(repository_info: RepositoryInfo,)->None:
    """打印经过校验的仓库信息。"""
    print("=" * 60)
    print("本地仓库路径校验成功")
    print("=" * 60)
    print(f"仓库名称：{repository_info.name}")
    print(f"绝对路径：{repository_info.absolute_path}")
    print(
        "Git元数据："
        f"{'已发现.git' if repository_info.has_git_metadata else '未发现.git'}"
    )

def run_validation_case(
        case_name:str,
        path_value:str|Path,
):
    """运行一个路径校验案例并打印结果。"""
    print("\n" + "=" * 60)
    print(f"测试案例：{case_name}")
    print("="*60)
    print(f"输入内容：{path_value!r}")

    try:
        repository_info = validate_repository_path(path_value)
    except RepositoryPathError as error:
        print(f"校验失败{error}")
        return
    print_repository_info(repository_info)

def main() -> None:
    """运行本地路径校验演示"""
    run_validation_case(
        case_name="正常的RepoMentor项目路径",
        path_value= PROJECT_ROOT,
    )
    run_validation_case(
        case_name="空路径",
        path_value="   ",
    )
    run_validation_case(
        case_name="不存在的路径",
        path_value=(
                PROJECT_ROOT
                / "this_repository_does_not_exist"
        ),
    )

    run_validation_case(
        case_name="路径指向文件而不是文件夹",
        path_value=PROJECT_ROOT / "README.md",
    )


if __name__ == "__main__":
    main()

