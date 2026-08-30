"""当前学习模块的目标限定文档加载与轻量切分。"""

from __future__ import annotations

import ast
import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from repo_mentor.models import LearningTask, TargetTask
from repo_mentor.repository_ranker import rank_target_files
from repo_mentor.repository_reader import (
    MAX_TEXT_FILE_BYTES,
    read_text_document,
)
from repo_mentor.repository_service import (
    validate_repository_path,
)
from repo_mentor.repository_tree import (
    DEFAULT_IGNORED_NAMES,
    should_ignore,
)
from repo_mentor.retrieval_models import (
    DocumentChunk,
    DocumentLoadResult,
    RetrievalSourceType,
    ScopedDocument,
)


DEFAULT_MAX_INDEX_FILES = 20
DEFAULT_MAX_INDEX_CHARS = 200_000
DEFAULT_MAX_CHUNK_CHARS = 1_200

DOCUMENT_EXTENSIONS = {".md", ".rst", ".txt"}
CONFIG_EXTENSIONS = {".toml", ".yaml", ".yml", ".ini", ".cfg"}
CONFIG_NAMES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "pytest.ini",
    "tox.ini",
}


@dataclass
class _Candidate:
    """加载前的内部候选记录。"""

    source_path: str
    source_type: RetrievalSourceType
    priority: int
    relevance_score: float
    reasons: list[str] = field(default_factory=list)


def _stable_hash(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def _normalize_relative_path(value: str) -> str:
    return PurePosixPath(
        value.replace("\\", "/")
    ).as_posix()


def _repository_scope_id(repository_root: Path) -> str:
    normalized = repository_root.resolve(
        strict=False
    ).as_posix()
    if os.name == "nt":
        normalized = normalized.casefold()
    return f"repo-{_stable_hash(normalized)[:16]}"


def _module_scope_id(
    target_task: TargetTask,
    learning_task: LearningTask,
) -> str:
    scope_text = "\n".join(
        [
            target_task.title,
            target_task.description,
            target_task.expected_outcome,
            learning_task.title,
            learning_task.objective,
            learning_task.reading_task,
            learning_task.code_location_task,
            learning_task.practice_task,
            *(
                source.file_path
                for source in learning_task.evidence_sources
            ),
        ]
    )
    return f"module-{_stable_hash(scope_text)[:16]}"


def classify_scoped_file(
    relative_path: str,
) -> RetrievalSourceType | None:
    """判断文件是否属于 V0.8 允许类型。"""
    normalized = _normalize_relative_path(
        relative_path
    )
    path = PurePosixPath(normalized)
    filename = path.name.lower()
    suffix = path.suffix.lower()
    lower_parts = {
        part.lower()
        for part in path.parts
    }

    if filename.startswith("readme") or (
        filename.startswith("contributing")
        and suffix in DOCUMENT_EXTENSIONS
    ):
        return "readme"

    if "docs" in lower_parts and (
        suffix in DOCUMENT_EXTENSIONS
    ):
        return "docs"

    if suffix == ".py":
        if (
            "tests" in lower_parts
            or filename.startswith("test_")
            or filename.endswith("_test.py")
        ):
            return "test"
        return "python"

    if (
        filename in CONFIG_NAMES
        or filename.startswith("requirements")
        and suffix == ".txt"
        or suffix in CONFIG_EXTENSIONS
    ):
        return "config"

    return None


def _is_safe_candidate_path(
    relative_path: str,
) -> bool:
    path = PurePosixPath(
        _normalize_relative_path(relative_path)
    )

    if path.is_absolute() or ".." in path.parts:
        return False

    return not any(
        should_ignore(
            Path(part),
            DEFAULT_IGNORED_NAMES,
        )
        for part in path.parts
        if part not in {"", "."}
    )


def _add_candidate(
    candidates: dict[str, _Candidate],
    *,
    source_path: str,
    priority: int,
    relevance_score: float,
    reasons: list[str],
) -> None:
    normalized_path = _normalize_relative_path(
        source_path
    )
    source_type = classify_scoped_file(
        normalized_path
    )

    if source_type is None or not _is_safe_candidate_path(
        normalized_path
    ):
        return

    lookup_key = normalized_path.casefold()
    existing = candidates.get(lookup_key)

    if existing is None:
        candidates[lookup_key] = _Candidate(
            source_path=normalized_path,
            source_type=source_type,
            priority=priority,
            relevance_score=max(
                relevance_score,
                0.0,
            ),
            reasons=list(dict.fromkeys(reasons)),
        )
        return

    existing.priority = min(existing.priority, priority)
    existing.relevance_score = max(
        existing.relevance_score,
        relevance_score,
    )
    for reason in reasons:
        if reason not in existing.reasons:
            existing.reasons.append(reason)


def load_documents(
    repository_path: str | Path,
    target_task: TargetTask,
    learning_task: LearningTask,
    *,
    max_files: int = DEFAULT_MAX_INDEX_FILES,
    max_total_chars: int = DEFAULT_MAX_INDEX_CHARS,
    max_file_bytes: int = MAX_TEXT_FILE_BYTES,
) -> DocumentLoadResult:
    """加载当前学习模块允许的目标相关文档。"""
    if max_files < 1:
        raise ValueError("max_files 必须大于等于 1")
    if max_total_chars < 1:
        raise ValueError(
            "max_total_chars 必须大于等于 1"
        )
    if max_file_bytes < 1:
        raise ValueError(
            "max_file_bytes 必须大于等于 1"
        )

    target = TargetTask.model_validate(target_task)
    task = LearningTask.model_validate(learning_task)
    repository_info = validate_repository_path(
        repository_path
    )
    repository_root = repository_info.absolute_path
    repository_scope_id = _repository_scope_id(
        repository_root
    )
    module_scope_id = _module_scope_id(target, task)

    candidates: dict[str, _Candidate] = {}
    warnings: list[str] = []

    # P0：路线任务已经批准的证据路径。
    for source in task.evidence_sources:
        _add_candidate(
            candidates,
            source_path=source.file_path,
            priority=0,
            relevance_score=100.0,
            reasons=[
                "当前 LearningTask.evidence_sources "
                "直接引用",
                source.reason,
            ],
        )

    # P1–P3：复用已有目标排序，但不读取未准入类型。
    ranked_files = rank_target_files(
        repository_root,
        target,
        top_n=max(max_files * 3, 24),
    )
    for ranked in ranked_files:
        source_type = classify_scoped_file(
            ranked.file_path
        )
        if source_type in {"readme", "docs"}:
            priority = 1
        elif source_type == "test":
            priority = 3
        else:
            priority = 2

        _add_candidate(
            candidates,
            source_path=ranked.file_path,
            priority=priority,
            relevance_score=ranked.score,
            reasons=list(ranked.reasons),
        )

    ordered_candidates = sorted(
        candidates.values(),
        key=lambda item: (
            item.priority,
            -item.relevance_score,
            item.source_path.casefold(),
        ),
    )

    documents: list[ScopedDocument] = []
    used_chars = 0

    for candidate in ordered_candidates:
        if len(documents) >= max_files:
            warnings.append(
                f"已达当前模块索引文件上限：{max_files}"
            )
            break

        try:
            document = read_text_document(
                repository_root=repository_root,
                relative_path=candidate.source_path,
                document_type=candidate.source_type,
                max_bytes=max_file_bytes,
            )
        except ValueError as error:
            warnings.append(str(error))
            continue

        if document is None:
            warnings.append(
                "候选文件不存在或不是普通文件："
                f"{candidate.source_path}"
            )
            continue

        # 只删除末尾空白，保留开头空行，
        # 否则切分后的源文件行号会偏移。
        content = document.content.rstrip()
        if not content.strip():
            warnings.append(
                f"文件内容为空，已跳过：{candidate.source_path}"
            )
            continue

        if used_chars + len(content) > max_total_chars:
            warnings.append(
                "文件会超过当前模块字符预算，"
                f"已跳过：{candidate.source_path}"
            )
            continue

        documents.append(
            ScopedDocument(
                repository_scope_id=(
                    repository_scope_id
                ),
                module_scope_id=module_scope_id,
                source_path=document.relative_path,
                source_type=candidate.source_type,
                content=content,
                size_bytes=document.size_bytes,
                priority=candidate.priority,
                relevance_score=(
                    candidate.relevance_score
                ),
                relevance_reasons=(
                    candidate.reasons
                    or ["通过当前目标相关性过滤"]
                ),
                content_hash=_stable_hash(content),
            )
        )
        used_chars += len(content)

    return DocumentLoadResult(
        repository_scope_id=repository_scope_id,
        module_scope_id=module_scope_id,
        documents=documents,
        warnings=warnings,
        used_files=len(documents),
        used_chars=used_chars,
    )


def _segment_starts(
    document: ScopedDocument,
    lines: list[str],
) -> list[tuple[int, str | None]]:
    """返回语义片段起始行及标题或符号。"""
    starts: list[tuple[int, str | None]] = []

    if document.source_type in {"python", "test"}:
        try:
            tree = ast.parse("\n".join(lines))
        except SyntaxError:
            return [(1, None)]

        for node in tree.body:
            if isinstance(
                node,
                (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                starts.append((node.lineno, node.name))

    elif document.source_type in {"readme", "docs"}:
        for line_number, line in enumerate(
            lines,
            start=1,
        ):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
                if heading:
                    starts.append((line_number, heading))

    elif document.source_type == "config":
        for line_number, line in enumerate(
            lines,
            start=1,
        ):
            stripped = line.strip()
            if (
                stripped.startswith("[")
                and stripped.endswith("]")
            ):
                starts.append((line_number, stripped))

    if not starts:
        return [(1, None)]

    if starts[0][0] > 1:
        starts.insert(0, (1, "module"))

    return starts


def _split_line_range(
    lines: list[str],
    *,
    line_start: int,
    line_end: int,
    label: str | None,
    max_chunk_chars: int,
) -> list[tuple[str, int, int, str | None]]:
    chunks: list[tuple[str, int, int, str | None]] = []
    buffer: list[str] = []
    buffer_start = line_start
    buffer_chars = 0

    def flush(end_line: int) -> None:
        nonlocal buffer, buffer_chars, buffer_start
        content = "\n".join(buffer).strip()
        if content:
            chunks.append(
                (content, buffer_start, end_line, label)
            )
        buffer = []
        buffer_chars = 0

    for line_number in range(line_start, line_end + 1):
        line = lines[line_number - 1]

        if len(line) > max_chunk_chars:
            if buffer:
                flush(line_number - 1)
            for offset in range(
                0,
                len(line),
                max_chunk_chars,
            ):
                piece = line[
                    offset: offset + max_chunk_chars
                ].strip()
                if piece:
                    chunks.append(
                        (piece, line_number, line_number, label)
                    )
            buffer_start = line_number + 1
            continue

        added_chars = len(line) + (1 if buffer else 0)
        if (
            buffer
            and buffer_chars + added_chars > max_chunk_chars
        ):
            flush(line_number - 1)
            buffer_start = line_number

        if not buffer:
            buffer_start = line_number
        buffer.append(line)
        buffer_chars += added_chars

    if buffer:
        flush(line_end)

    return chunks


def split_documents(
    documents: list[ScopedDocument],
    *,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
) -> list[DocumentChunk]:
    """按文档结构和行窗口生成可追溯片段。"""
    if max_chunk_chars < 100:
        raise ValueError(
            "max_chunk_chars 必须大于等于 100"
        )

    chunks: list[DocumentChunk] = []

    for raw_document in documents:
        document = ScopedDocument.model_validate(
            raw_document
        )
        lines = document.content.splitlines()
        if not lines:
            continue

        starts = _segment_starts(document, lines)

        for index, (line_start, label) in enumerate(starts):
            line_end = (
                starts[index + 1][0] - 1
                if index + 1 < len(starts)
                else len(lines)
            )

            for (
                content,
                chunk_line_start,
                chunk_line_end,
                chunk_label,
            ) in _split_line_range(
                lines,
                line_start=line_start,
                line_end=line_end,
                label=label,
                max_chunk_chars=max_chunk_chars,
            ):
                content_hash = _stable_hash(content)
                chunk_identity = "|".join(
                    [
                        document.repository_scope_id,
                        document.module_scope_id,
                        document.source_path,
                        str(chunk_line_start),
                        str(chunk_line_end),
                        content_hash,
                    ]
                )
                chunks.append(
                    DocumentChunk(
                        chunk_id=(
                            "chunk-"
                            + _stable_hash(
                                chunk_identity
                            )[:24]
                        ),
                        repository_scope_id=(
                            document.repository_scope_id
                        ),
                        module_scope_id=(
                            document.module_scope_id
                        ),
                        source_path=document.source_path,
                        source_type=document.source_type,
                        content=content,
                        line_start=chunk_line_start,
                        line_end=chunk_line_end,
                        heading_or_symbol=chunk_label,
                        relevance_score=(
                            document.relevance_score
                        ),
                        relevance_reasons=(
                            document.relevance_reasons
                        ),
                        content_hash=content_hash,
                    )
                )

    return chunks
