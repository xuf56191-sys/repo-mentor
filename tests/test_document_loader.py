"""目标限定文档加载与切分测试。"""

from pathlib import Path

from repo_mentor.document_loader import (
    classify_scoped_file,
    load_documents,
    split_documents,
)
from repo_mentor.models import (
    EvidenceSource,
    LearningTask,
    TargetTask,
)


def make_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "demo-repository"
    (repository / "src").mkdir(parents=True)
    (repository / "tests").mkdir()
    (repository / "docs").mkdir()
    (repository / ".venv").mkdir()

    (repository / "README.md").write_text(
        "# Scoped Retrieval\n\n"
        "The index flow is implemented in `src/target_module.py`.\n",
        encoding="utf-8",
    )
    (repository / "docs" / "guide.md").write_text(
        "# Loading documents\n\n"
        "Load only files related to the current learning task.\n\n"
        "## Source metadata\n\n"
        "Every chunk keeps its path and line range.\n",
        encoding="utf-8",
    )
    (repository / "src" / "target_module.py").write_text(
        '\n\n"""Target-scoped indexing helpers."""\n\n'
        "from pathlib import Path\n\n"
        "def load_documents(path: Path):\n"
        "    \"\"\"Load approved text documents.\"\"\"\n"
        "    return [path]\n\n"
        "def build_index(documents):\n"
        "    \"\"\"Build chunks with source metadata.\"\"\"\n"
        "    return list(documents)\n",
        encoding="utf-8",
    )
    (repository / "tests" / "test_target_module.py").write_text(
        "def test_loader_keeps_sources():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    (repository / "pyproject.toml").write_text(
        "[project]\nname = 'demo'\n",
        encoding="utf-8",
    )
    (repository / "src" / "binary.py").write_bytes(
        b"print('before')\x00print('after')"
    )
    (repository / "src" / "large.py").write_text(
        "x = '" + "a" * 201_000 + "'\n",
        encoding="utf-8",
    )
    (repository / ".env").write_text(
        "SECRET=do-not-index\n",
        encoding="utf-8",
    )
    (repository / ".venv" / "secret.py").write_text(
        "TOKEN = 'do-not-index'\n",
        encoding="utf-8",
    )
    (repository / "logo.png").write_bytes(b"\x89PNG")
    return repository


def make_target() -> TargetTask:
    return TargetTask(
        title="理解目标限定文档加载",
        description="理解 load_documents 如何保留路径和行号",
        task_type="understand_module",
        expected_outcome="能解释文档准入和切分边界",
    )


def make_learning_task() -> LearningTask:
    paths = [
        "README.md",
        "docs/guide.md",
        "src/target_module.py",
        "tests/test_target_module.py",
        "pyproject.toml",
        "src/binary.py",
        "src/large.py",
        ".env",
        ".venv/secret.py",
        "logo.png",
    ]
    return LearningTask(
        title="实现限定文档加载",
        objective="只加载当前目标相关的安全文本",
        evidence_sources=[
            EvidenceSource(
                file_path=path,
                evidence_type="source",
                reason="验证当前文档加载范围",
            )
            for path in paths
        ],
        reading_task="阅读文档加载和切分逻辑",
        code_location_task="定位 load_documents 和 build_index",
        practice_task="对小型仓库生成带行号的片段",
        completion_criteria=["二进制和忽略路径不会进入"],
        estimated_hours=1.0,
    )


def test_classify_scoped_file_types():
    assert classify_scoped_file("README.md") == "readme"
    assert classify_scoped_file("docs/guide.rst") == "docs"
    assert classify_scoped_file("src/app.py") == "python"
    assert classify_scoped_file("tests/test_app.py") == "test"
    assert classify_scoped_file("pyproject.toml") == "config"
    assert classify_scoped_file("assets/logo.png") is None


def test_load_documents_excludes_unsafe_and_binary_files(
    tmp_path: Path,
):
    repository = make_repository(tmp_path)
    result = load_documents(
        repository,
        make_target(),
        make_learning_task(),
    )
    loaded_paths = {
        document.source_path
        for document in result.documents
    }

    assert {
        "README.md",
        "docs/guide.md",
        "src/target_module.py",
        "tests/test_target_module.py",
        "pyproject.toml",
    } <= loaded_paths
    assert "src/binary.py" not in loaded_paths
    assert "src/large.py" not in loaded_paths
    assert ".env" not in loaded_paths
    assert ".venv/secret.py" not in loaded_paths
    assert "logo.png" not in loaded_paths
    assert any(
        "二进制" in warning
        for warning in result.warnings
    )
    assert any(
        "文件过大" in warning
        for warning in result.warnings
    )


def test_load_documents_respects_file_budget(
    tmp_path: Path,
):
    result = load_documents(
        make_repository(tmp_path),
        make_target(),
        make_learning_task(),
        max_files=2,
    )

    assert result.used_files == 2
    assert len(result.documents) == 2
    assert any(
        "索引文件上限" in warning
        for warning in result.warnings
    )


def test_split_documents_keeps_readable_source_lines(
    tmp_path: Path,
):
    repository = make_repository(tmp_path)
    loaded = load_documents(
        repository,
        make_target(),
        make_learning_task(),
    )
    chunks = split_documents(
        loaded.documents,
        max_chunk_chars=300,
    )

    assert chunks
    assert all(chunk.source_path for chunk in chunks)
    assert all(chunk.line_start >= 1 for chunk in chunks)
    assert all(
        chunk.line_end >= chunk.line_start
        for chunk in chunks
    )
    assert all(chunk.content.strip() for chunk in chunks)
    assert {
        chunk.repository_scope_id
        for chunk in chunks
    } == {loaded.repository_scope_id}
    assert {
        chunk.module_scope_id
        for chunk in chunks
    } == {loaded.module_scope_id}

    build_index_chunk = next(
        chunk
        for chunk in chunks
        if chunk.heading_or_symbol == "build_index"
    )
    source_lines = (
        repository
        / "src"
        / "target_module.py"
    ).read_text(encoding="utf-8").splitlines()
    restored_text = "\n".join(
        source_lines[
            build_index_chunk.line_start - 1:
            build_index_chunk.line_end
        ]
    ).strip()

    assert build_index_chunk.content == restored_text
    assert "def build_index" in build_index_chunk.content


def test_scope_ids_are_stable_for_same_inputs(
    tmp_path: Path,
):
    repository = make_repository(tmp_path)
    first = load_documents(
        repository,
        make_target(),
        make_learning_task(),
    )
    second = load_documents(
        repository,
        make_target(),
        make_learning_task(),
    )

    assert first.repository_scope_id == (
        second.repository_scope_id
    )
    assert first.module_scope_id == second.module_scope_id


def test_module_scope_changes_when_approved_sources_change(
    tmp_path: Path,
):
    repository = make_repository(tmp_path)
    first_task = make_learning_task()
    second_task = make_learning_task().model_copy(
        update={
            "evidence_sources": [
                *make_learning_task().evidence_sources,
                EvidenceSource(
                    file_path="src/another_module.py",
                    evidence_type="source",
                    reason="切换后的新模块证据",
                ),
            ],
        }
    )

    first = load_documents(
        repository,
        make_target(),
        first_task,
    )
    second = load_documents(
        repository,
        make_target(),
        second_task,
    )

    assert first.module_scope_id != second.module_scope_id
