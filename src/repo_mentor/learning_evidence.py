"""路线、测验和学习问答共用的一次性证据层。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repo_mentor.document_loader import (
    load_documents,
    split_documents,
)
from repo_mentor.grounded_qa import (
    answer_learning_question,
)
from repo_mentor.hybrid_retriever import (
    ScopedHybridRetriever,
)
from repo_mentor.models import (
    LearningTask,
    RepositoryEvidence,
    TargetTask,
)
from repo_mentor.retrieval_models import (
    DocumentChunk,
    DocumentLoadResult,
    GroundedLearningAnswer,
    RetrievalResult,
)


def retriever_from_chunks(
    chunks: list[DocumentChunk] | tuple[DocumentChunk, ...],
) -> ScopedHybridRetriever:
    """从 State 中已有片段恢复检索器，不重新索引仓库。"""
    validated = [
        DocumentChunk.model_validate(chunk)
        for chunk in chunks
    ]
    if not validated:
        raise ValueError("构造检索器至少需要一个片段")
    first = validated[0]
    return ScopedHybridRetriever(
        validated,
        repository_scope_id=first.repository_scope_id,
        module_scope_id=first.module_scope_id,
    )


def retrieval_context_from_chunks(
    chunks: list[DocumentChunk] | tuple[DocumentChunk, ...],
    query: str,
    *,
    top_k: int = 5,
) -> tuple[str, list[RepositoryEvidence]]:
    """为路线和测验生成可追溯、同源的文本上下文。"""
    result = retriever_from_chunks(chunks).retrieve(
        query,
        top_k=top_k,
    )
    evidence = [
        RepositoryEvidence(
            source_path=hit.chunk.source_path,
            snippet=hit.chunk.content,
            reason=(
                "当前学习模块混合检索命中；"
                f"行 {hit.chunk.line_start}-{hit.chunk.line_end}"
            ),
            confidence=round(hit.score, 4),
        )
        for hit in result.hits
    ]
    context = "\n\n".join(
        (
            f"[{item.source_path}]\n"
            f"{item.snippet or ''}"
        )
        for item in evidence
    )
    return context, evidence


@dataclass(frozen=True)
class LearningEvidenceLayer:
    """保存一次加载/切分结果，供三个消费者复用。"""

    load_result: DocumentLoadResult
    chunks: tuple[DocumentChunk, ...]

    @classmethod
    def build(
        cls,
        repository_path: str | Path,
        target_task: TargetTask,
        learning_task: LearningTask,
    ) -> "LearningEvidenceLayer":
        loaded = load_documents(
            repository_path,
            target_task,
            learning_task,
        )
        return cls(
            load_result=loaded,
            chunks=tuple(split_documents(loaded.documents)),
        )

    @property
    def retriever(self) -> ScopedHybridRetriever:
        """创建轻量检索视图，不再次读取或切分仓库。"""
        return retriever_from_chunks(self.chunks)

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
    ) -> RetrievalResult:
        return self.retriever.retrieve(query, top_k=top_k)

    def answer(self, question: str) -> GroundedLearningAnswer:
        return answer_learning_question(
            question,
            self.retriever,
        )

    def repository_evidence(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[RepositoryEvidence]:
        """把检索命中转换为路线/测验已有的证据协议。"""
        result = self.retrieve(query, top_k=top_k)
        return [
            RepositoryEvidence(
                source_path=hit.chunk.source_path,
                snippet=hit.chunk.content,
                reason=(
                    "当前学习模块混合检索命中；"
                    f"行 {hit.chunk.line_start}-"
                    f"{hit.chunk.line_end}"
                ),
                confidence=round(hit.score, 4),
            )
            for hit in result.hits
        ]


def merge_repository_evidence(
    existing: list[RepositoryEvidence],
    retrieved: list[RepositoryEvidence],
) -> list[RepositoryEvidence]:
    """按路径和片段去重，避免覆盖已有 State 字段。"""
    merged: list[RepositoryEvidence] = []
    seen: set[tuple[str, str]] = set()
    for raw in [*existing, *retrieved]:
        item = RepositoryEvidence.model_validate(raw)
        key = (
            item.source_path.replace("\\", "/").casefold(),
            (item.snippet or "").strip(),
        )
        if key not in seen:
            merged.append(item)
            seen.add(key)
    return merged
