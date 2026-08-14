from pathlib import Path

from repo_mentor.models import TargetTask
from repo_mentor.repository_ranker import (
    rank_target_files,
)


def create_target(
    title: str,
    description: str,
) -> TargetTask:
    return TargetTask(
        title=title,
        description=description,
        task_type="understand_module",
        expected_outcome="能够说明相关模块作用",
        reference=None,
    )

def test_different_targets_get_different_files(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    src.mkdir()

    (src / "repository_tree.py").write_text(
        "# tree",
        encoding="utf-8",
    )

    (src / "roadmap_generator.py").write_text(
        "# roadmap",
        encoding="utf-8",
    )

    (tmp_path / "README.md").write_text(
        "# Test Repo",
        encoding="utf-8",
    )

    tree_target = create_target(
        "理解目录树扫描",
        "理解仓库目录树扫描流程",
    )

    roadmap_target = create_target(
        "理解学习路线生成",
        "理解结构化学习路线生成流程",
    )

    tree_results = rank_target_files(
        tmp_path,
        tree_target,
        top_n=1,
    )

    roadmap_results = rank_target_files(
        tmp_path,
        roadmap_target,
        top_n=1,
    )

    assert tree_results
    assert roadmap_results

    assert (
        tree_results[0].file_path
        != roadmap_results[0].file_path
    )

def test_top_n_limit(
    tmp_path: Path,
) -> None:
    for index in range(10):
        (
            tmp_path
            / f"config_{index}.py"
        ).write_text(
            "# config",
            encoding="utf-8",
        )

    target = create_target(
        "理解配置",
        "理解config配置文件",
    )

    results = rank_target_files(
        tmp_path,
        target,
        top_n=3,
    )

    assert len(results) <= 3

def test_ranked_files_really_exist(
    tmp_path: Path,
) -> None:
    """排序结果中的文件必须真实存在。"""

    (tmp_path / "README.md").write_text(
        "# Test Repository",
        encoding="utf-8",
    )

    (tmp_path / "config.py").write_text(
        "DEBUG = False",
        encoding="utf-8",
    )

    (tmp_path / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    target = create_target(
        "理解项目配置",
        "理解项目中的config配置方式",
    )

    results = rank_target_files(
        repository_path=tmp_path,
        target_task=target,
    )

    assert results

    for result in results:
        assert (
            tmp_path / result.file_path
        ).exists()

def test_readme_reference_creates_real_snippet(
    tmp_path: Path,
) -> None:
    """README真实引用应成为可追溯文本证据。"""

    src_dir = tmp_path / "src"
    src_dir.mkdir()

    target_file = (
        src_dir / "repository_tree.py"
    )

    target_file.write_text(
        "# repository tree",
        encoding="utf-8",
    )

    readme_text = (
        "# Test Repository\n\n"
        "目录扫描功能见 "
        "`src/repository_tree.py`。"
    )

    (tmp_path / "README.md").write_text(
        readme_text,
        encoding="utf-8",
    )

    target = create_target(
        "理解目录树扫描",
        "理解repository tree目录扫描流程",
    )

    results = rank_target_files(
        repository_path=tmp_path,
        target_task=target,
        top_n=5,
    )

    assert results

    ranked_file = next(
        item
        for item in results
        if item.file_path
        == "src/repository_tree.py"
    )

    readme_evidence = [
        evidence
        for evidence in ranked_file.evidence
        if evidence.source_path
        == "README.md"
    ]

    assert readme_evidence

    assert (
        readme_evidence[0].snippet
        is not None
    )

    assert (
        "repository_tree.py"
        in readme_evidence[0].snippet
    )

def test_source_file_ranks_above_test_file(
    tmp_path: Path,
) -> None:
    """核心源码文件应排在对应测试文件之前。"""

    src = tmp_path / "src"
    tests_dir = tmp_path / "tests"
    src.mkdir()
    tests_dir.mkdir()

    (src / "signer.py").write_text(
        "# signer",
        encoding="utf-8",
    )

    (tests_dir / "test_signer.py").write_text(
        "# test",
        encoding="utf-8",
    )

    (tmp_path / "README.md").write_text(
        "# Test Repo",
        encoding="utf-8",
    )

    target = create_target(
        "理解数据签名",
        "理解数据签名与恢复流程",
    )

    results = rank_target_files(
        tmp_path,
        target,
        top_n=5,
    )

    paths = [
        item.file_path
        for item in results
    ]

    assert "src/signer.py" in paths
    assert paths.index(
        "src/signer.py"
    ) < paths.index(
        "tests/test_signer.py"
    )

def test_asset_files_are_filtered_out(
    tmp_path: Path,
) -> None:
    """svg 等资源文件不应出现在排序结果中。"""

    src = tmp_path / "src"
    src.mkdir()

    (src / "signer.py").write_text(
        "# signer",
        encoding="utf-8",
    )

    static_dir = (
        tmp_path / "docs" / "_static"
    )
    static_dir.mkdir(parents=True)

    (static_dir / "logo.svg").write_text(
        "<svg/>",
        encoding="utf-8",
    )

    (tmp_path / "README.md").write_text(
        "签名见 `src/signer.py`。",
        encoding="utf-8",
    )

    target = create_target(
        "理解数据签名",
        "理解数据签名与恢复流程",
    )

    results = rank_target_files(
        tmp_path,
        target,
        top_n=10,
    )

    paths = [
        item.file_path
        for item in results
    ]

    assert "src/signer.py" in paths
    assert all(
        not path.endswith(".svg")
        for path in paths
    )