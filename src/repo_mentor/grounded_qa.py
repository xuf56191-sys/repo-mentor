"""当前学习任务内、可追溯且会保守拒答的问答。"""

from __future__ import annotations

import re

from repo_mentor.hybrid_retriever import (
    ScopedHybridRetriever,
)
from repo_mentor.retrieval_models import (
    GroundedLearningAnswer,
    RetrievalHit,
    SourceCitation,
)


REFUSAL_TEXT = (
    "当前学习任务的仓库证据不足，我不能可靠回答。"
    "请提供更具体的文件、函数名或 Issue 信息。"
)


def _compact_excerpt(
    hit: RetrievalHit,
    *,
    max_chars: int = 360,
) -> str:
    """保留原文而非改写，便于验证引用真实性。"""
    content = hit.chunk.content.strip()
    if len(content) <= max_chars:
        return content
    return content[: max_chars - 1].rstrip() + "…"


def _first_meaningful_line(excerpt: str) -> str:
    """从证据中选择一句短结论，不生成证据之外的事实。"""
    for line in excerpt.splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        if clean and not clean.startswith(("#", '"""', "'''")):
            return clean[:180]
    return re.sub(r"\s+", " ", excerpt).strip()[:180]


def answer_learning_question(
    question: str,
    retriever: ScopedHybridRetriever,
    *,
    top_k: int = 3,
) -> GroundedLearningAnswer:
    """用检索片段回答；无可靠证据时拒绝猜测。"""
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("question 不能为空")

    result = retriever.retrieve(
        clean_question,
        top_k=top_k,
    )

    if not result.evidence_sufficient or not result.hits:
        return GroundedLearningAnswer(
            question=clean_question,
            answer=REFUSAL_TEXT,
            citations=[],
            evidence_sufficient=False,
            uncertainty=result.reason,
            scope_note=(
                "问答范围仅限当前仓库、当前学习模块的已索引证据。"
            ),
        )

    citations = [
        SourceCitation(
            source_path=hit.chunk.source_path,
            line_start=hit.chunk.line_start,
            line_end=hit.chunk.line_end,
            excerpt=_compact_excerpt(hit),
        )
        for hit in result.hits
    ]
    statements = [
        (
            f"{_first_meaningful_line(citation.excerpt)} "
            f"[{citation.source_path}:"
            f"{citation.line_start}-{citation.line_end}]"
        )
        for citation in citations
    ]

    return GroundedLearningAnswer(
        question=clean_question,
        answer="根据当前任务证据：\n- " + "\n- ".join(statements),
        citations=citations,
        evidence_sufficient=True,
        uncertainty=(
            "回答只概括命中的局部片段；未命中的仓库内容不在结论范围内。"
        ),
        scope_note=(
            "问答范围仅限当前仓库、当前学习模块，"
            "不是任意全仓聊天。"
        ),
    )
