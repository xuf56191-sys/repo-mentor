from pathlib import Path

import pytest
from pydantic import ValidationError

from repo_mentor.models import TargetTask
from repo_mentor.repository_tools import (
    get_onboarding_docs,
    get_repo_tree,
    rank_target_files,
    read_repo_file,
)


def create_test_repository(
    tmp_path: Path,
) -> Path:
    """创建一个最小测试仓库。"""

    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (
        tmp_path / "README.md"
    ).write_text(
        "# Test Repository\n\n"
        "目录树功能见 "
        "`src/repository_tree.py`。",
        encoding="utf-8",
    )

    (
        tmp_path / "requirements.txt"
    ).write_text(
        "pydantic\n",
        encoding="utf-8",
    )

    (
        src_dir / "repository_tree.py"
    ).write_text(
        "def build_tree():\n"
        "    return 'tree'\n",
        encoding="utf-8",
    )

    return tmp_path


def test_get_repo_tree_can_invoke(
    tmp_path: Path,
) -> None:
    repository = create_test_repository(
        tmp_path
    )

    result = get_repo_tree.invoke(
        {
            "repository_path": str(repository),
            "max_depth": 4,
            "max_files": 100,
        }
    )

    assert result["ok"] is True
    assert "README.md" in result["tree"]


def test_get_onboarding_docs_can_invoke(
    tmp_path: Path,
) -> None:
    repository = create_test_repository(
        tmp_path
    )

    result = get_onboarding_docs.invoke(
        {
            "repository_path": str(repository),
        }
    )

    assert result["ok"] is True

    source_paths = {
        document["source_path"]
        for document
        in result["documents"]
    }

    assert "README.md" in source_paths


def test_read_repo_file_can_invoke(
    tmp_path: Path,
) -> None:
    repository = create_test_repository(
        tmp_path
    )

    result = read_repo_file.invoke(
        {
            "repository_path": str(repository),
            "relative_path": (
                "src/repository_tree.py"
            ),
        }
    )

    assert result["ok"] is True
    assert (
        "build_tree"
        in result["content"]
    )


def test_rank_target_files_can_invoke(
    tmp_path: Path,
) -> None:
    repository = create_test_repository(
        tmp_path
    )

    target = TargetTask(
        title="理解目录树扫描",
        description=(
            "理解repository tree"
            "目录树扫描流程"
        ),
        task_type="understand_module",
        expected_outcome=(
            "能够说明目录树模块作用"
        ),
        reference=None,
    )

    result = rank_target_files.invoke(
        {
            "repository_path": str(repository),
            "target_task": (
                target.model_dump(
                    mode="json"
                )
            ),
            "top_n": 3,
        }
    )

    assert result["ok"] is True
    assert result["files"]

    file_paths = {
        item["file_path"]
        for item in result["files"]
    }

    assert (
        "src/repository_tree.py"
        in file_paths
    )


def test_invalid_tool_argument_is_rejected(
    tmp_path: Path,
) -> None:
    repository = create_test_repository(
        tmp_path
    )

    with pytest.raises(
        ValidationError
    ):
        get_repo_tree.invoke(
            {
                "repository_path": (
                    str(repository)
                ),
                "max_depth": 0,
            }
        )


def test_read_repo_file_rejects_env(
    tmp_path: Path,
) -> None:
    repository = create_test_repository(
        tmp_path
    )

    (
        repository / ".env"
    ).write_text(
        "API_KEY=secret",
        encoding="utf-8",
    )

    result = read_repo_file.invoke(
        {
            "repository_path": (
                str(repository)
            ),
            "relative_path": ".env",
        }
    )

    assert result["ok"] is False