"""安全读取本地仓库的入门与贡献相关资料。"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from repo_mentor.repository_service import (
    RepositoryPathError,
    validate_repository_path,
)
# from  repository_service import (validate_repository_path,RepositoryPathError)

MAX_TEXT_FILE_BYTES = 200_200

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

README_CANDIDATES = (
    "README.md",
    "README.rst",
    "README.txt",
    "README",
)

CONTRIBUTING_CANDIDATES = (
    "CONTRIBUTING.md",
    "CONTRIBUTING.rst",
    "CONTRIBUTING.txt",
    "CONTRIBUTING",
)

PROJECT_METADATA_CANDIDATES = (
    "pyproject.toml",
    "requirements.txt",
)

DOCS_ENTRY_CANDIDATES = (
    "docs/README.md",
    "docs/index.md",
    "docs/index.rst",
)

@dataclass(frozen=True)
class RepositoryDocument:
    """从真实仓库读取的一份文本资料。"""
    document_type : str
    relative_path : str
    content : str
    size_bytes :int

@dataclass
class RepositoryReadResult:
    """仓库入门资料读取结果。"""
    repository_name:str
    documents:list[RepositoryDocument] = field(default_factory = list)
    warnings: list[str] = field(default_factory=list)

def look_binary(data:bytes)->bool:
    """使用简单规则判断文件是否像二进制文件。"""
    sample = data[:4096]

    return b"\x00" in sample

def read_text_document(
        repository_root:Path,
        relative_path:str,
        document_type:str,
        *,
        max_bytes:int = MAX_TEXT_FILE_BYTES,
)-> RepositoryDocument|None:
    """
        安全读取仓库中的一个文本文件。

        文件不存在时返回None。
        文件过大、二进制或编码错误时抛出ValueError。
        """
    file_path = (
        repository_root / relative_path
    ).resolve()

    try:
        file_path.relative_to(repository_root)
    except ValueError as error:
        raise ValueError(f"文件路径超出仓库范围：{relative_path}") from error

    if not file_path.exists():
        return  None

    if not file_path.is_file():
        return  None

    if file_path.is_symlink():
        raise ValueError(f"跳过符号链接文件：{relative_path}")

    try:
        size_bytes = file_path.stat().st_size
    except OSError as error:
        raise ValueError(f"无法读取文件信息：{relative_path}") from error

    if size_bytes>max_bytes:
        raise ValueError(
            f"文件过大，已跳过：{relative_path}，"
            f"大小为{size_bytes}字节，"
            f"限制为{max_bytes}字节。"
        )

    try:
        raw_data = file_path.read_bytes()
    except PermissionError as error:
        raise ValueError(f"没有权限读取文件：{file_path}") from error
    except OSError as error:
        raise ValueError(f"读取文件失败：{file_path}") from error

    if look_binary(raw_data):
        raise ValueError(f"检测到可能的二进制文件，已跳过："
                         f"{relative_path}"
                         )
    try:
        content = raw_data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError(f"文件不是正常可读取的UTF-8文件："
                         f"{relative_path}") from error

    return RepositoryDocument(
        document_type = document_type,
        relative_path=relative_path,
        content= content,
        size_bytes = size_bytes
    )

def read_first_available(
    repository_root: Path,
    candidates: tuple[str, ...],
    document_type: str,
    warnings: list[str],
) -> RepositoryDocument | None:
    """从候选路径中读取第一个可以正常读取的文件。"""

    for relative_path in candidates:
        try:
            document = read_text_document(
                repository_root=repository_root,
                relative_path=relative_path,
                document_type=document_type,
            )
        except ValueError as error:
            warnings.append(str(error))
            continue

        if document is not None:
            return document

    return None

def read_all_available(
    repository_root: Path,
    candidates: tuple[str, ...],
    document_type: str,
    warnings: list[str],
) -> list[RepositoryDocument]:
    """读取候选列表中所有存在且可安全读取的文件。"""

    documents: list[RepositoryDocument] = []

    for relative_path in candidates:
        try:
            document = read_text_document(
                repository_root=repository_root,
                relative_path=relative_path,
                document_type=document_type,
            )
        except ValueError as error:
            warnings.append(str(error))
            continue

        if document is not None:
            documents.append(document)

    return documents

def read_repository_onboarding_docs(
    repository_path: str | Path,
) -> RepositoryReadResult:
    """读取仓库中的主要入门和贡献资料。"""

    repository_info = validate_repository_path(
        repository_path
    )

    repository_root = (
        repository_info.absolute_path
    )

    result = RepositoryReadResult(
        repository_name=repository_info.name
    )

    readme = read_first_available(
        repository_root=repository_root,
        candidates=README_CANDIDATES,
        document_type="readme",
        warnings=result.warnings,
    )

    if readme is not None:
        result.documents.append(readme)
    else:
        result.warnings.append(
            "未找到README文件。"
        )

    contributing = read_first_available(
        repository_root=repository_root,
        candidates=CONTRIBUTING_CANDIDATES,
        document_type="contributing",
        warnings=result.warnings,
    )

    if contributing is not None:
        result.documents.append(contributing)
    else:
        result.warnings.append(
            "未找到CONTRIBUTING文件。"
        )

    metadata_documents = read_all_available(
        repository_root=repository_root,
        candidates=PROJECT_METADATA_CANDIDATES,
        document_type="project_metadata",
        warnings=result.warnings,
    )

    result.documents.extend(
        metadata_documents
    )

    docs_entry = read_first_available(
        repository_root=repository_root,
        candidates=DOCS_ENTRY_CANDIDATES,
        document_type="docs_entry",
        warnings=result.warnings,
    )

    if docs_entry is not None:
        result.documents.append(docs_entry)

    return result

def print_repository_documents(
    result: RepositoryReadResult,
) -> None:
    """打印仓库入门资料读取结果。"""

    print("=" * 60)
    print(
        f"仓库入门资料：{result.repository_name}"
    )
    print("=" * 60)

    if not result.documents:
        print("没有读取到可用资料。")

    for document in result.documents:
        print("\n" + "-" * 60)
        print(
            f"资料类型：{document.document_type}"
        )
        print(
            f"来源路径：{document.relative_path}"
        )
        print(
            f"文件大小：{document.size_bytes} bytes"
        )
        print("-" * 60)
        print(document.content)

    if result.warnings:
        print("\n" + "=" * 60)
        print("读取警告")
        print("=" * 60)

        for warning in result.warnings:
            print(f"- {warning}")

def main() -> None:
    """运行仓库资料读取测试。"""

    try:
        result = read_repository_onboarding_docs(
            PROJECT_ROOT
        )

        print_repository_documents(result)

    except RepositoryPathError as error:
        print(
            f"仓库路径错误：{error}"
        )

    except Exception as error:
        print(
            "仓库资料读取失败："
            f"{type(error).__name__}: {error}"
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()



