"""当前学习模块内的离线混合检索。"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

from repo_mentor.retrieval_models import (
    DocumentChunk,
    RetrievalHit,
    RetrievalResult,
)


DEFAULT_VECTOR_DIMENSIONS = 384
DEFAULT_MIN_SCORE = 0.12

STOP_TOKENS = {
    "a",
    "an",
    "and",
    "for",
    "how",
    "in",
    "is",
    "of",
    "or",
    "the",
    "to",
    "what",
    "why",
    "一个",
    "为什么",
    "什么",
    "如何",
    "怎么",
    "当前",
    "可以",
}

# 离线基线使用受控概念扩展，不假装是通用神经语义模型。
CONCEPT_GROUPS = (
    (
        "工作流",
        "workflow",
        "graph",
        "stategraph",
        "节点",
        "node",
        "路由",
        "route",
    ),
    (
        "恢复",
        "resume",
        "checkpoint",
        "thread_id",
        "interrupt",
        "中断",
        "暂停",
        "继续",
        "重启",
        "会话",
    ),
    (
        "证据",
        "evidence",
        "source",
        "snippet",
        "来源",
        "片段",
        "chunk",
    ),
    (
        "加载",
        "load",
        "loader",
        "read",
        "reader",
        "读取",
    ),
    (
        "切分",
        "切块",
        "split",
        "chunk",
        "line_start",
        "行号",
    ),
    (
        "检索",
        "retrieval",
        "retriever",
        "search",
        "top_k",
        "top-k",
    ),
    (
        "向量",
        "vector",
        "embedding",
        "semantic",
        "cosine",
        "语义",
        "余弦",
    ),
    (
        "关键词",
        "keyword",
        "identifier",
        "token",
        "函数名",
        "符号",
    ),
    (
        "敏感",
        "sensitive",
        ".env",
        "ignore",
        "ignored",
        "忽略",
        "secret",
        "凭据",
        "密钥",
    ),
    (
        "大小",
        "size",
        "bytes",
        "max_bytes",
        "过大",
        "限制",
        "budget",
        "预算",
    ),
    (
        "目录树",
        "tree",
        "repository_tree",
        "scan",
        "扫描",
        "max_depth",
    ),
    (
        "掌握度",
        "mastery",
        "profile",
        "画像",
        "weak_points",
        "薄弱点",
    ),
    (
        "评估",
        "assessment",
        "evaluation",
        "quiz",
        "score",
        "测验",
        "评分",
    ),
    (
        "持久化",
        "persistence",
        "sqlite",
        "database",
        "进度",
        "save_progress",
        "load_latest_progress",
    ),
)


def _split_identifier(value: str) -> list[str]:
    snake_parts = re.split(r"[_\-]+", value)
    parts: list[str] = []
    for snake_part in snake_parts:
        camel_parts = re.sub(
            r"([a-z0-9])([A-Z])",
            r"\1 \2",
            snake_part,
        ).split()
        parts.extend(
            part.casefold()
            for part in camel_parts
            if part
        )
    return parts


def _basic_tokens(text: str) -> list[str]:
    tokens: list[str] = []

    for identifier in re.findall(
        r"[A-Za-z][A-Za-z0-9_\-]*",
        text,
    ):
        lowered = identifier.casefold()
        tokens.append(lowered)
        tokens.extend(_split_identifier(identifier))

    for sequence in re.findall(
        r"[\u4e00-\u9fff]+",
        text,
    ):
        if len(sequence) <= 4:
            tokens.append(sequence)
        for width in (2, 3):
            if len(sequence) >= width:
                tokens.extend(
                    sequence[index: index + width]
                    for index in range(
                        len(sequence) - width + 1
                    )
                )

    return [
        token
        for token in tokens
        if len(token) >= 2 and token not in STOP_TOKENS
    ]


def tokenize(text: str, *, expand_concepts: bool) -> list[str]:
    """对中文、英文和代码标识符生成稳定特征。"""
    tokens = _basic_tokens(text)

    if expand_concepts:
        lowered = text.casefold()
        for group in CONCEPT_GROUPS:
            if any(
                concept.casefold() in lowered
                for concept in group
            ):
                for concept in group:
                    tokens.extend(_basic_tokens(concept))

    return tokens


def _hashed_vector(
    text: str,
    *,
    dimensions: int,
) -> list[float]:
    counts = Counter(
        tokenize(text, expand_concepts=True)
    )
    vector = [0.0] * dimensions

    for token, count in counts.items():
        digest = hashlib.sha256(
            token.encode("utf-8")
        ).digest()
        index = int.from_bytes(
            digest[:4],
            "big",
        ) % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign * (
            1.0 + math.log(count)
        )

    norm = math.sqrt(
        sum(value * value for value in vector)
    )
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _cosine_score(
    first: list[float],
    second: list[float],
) -> float:
    score = sum(
        left * right
        for left, right in zip(first, second)
    )
    return max(0.0, min(1.0, score))


def _keyword_score(query: str, chunk: DocumentChunk) -> float:
    query_tokens = set(
        tokenize(query, expand_concepts=False)
    )
    if not query_tokens:
        return 0.0

    content_text = "\n".join(
        [
            chunk.source_path,
            chunk.heading_or_symbol or "",
            chunk.content,
        ]
    )
    content_tokens = set(
        tokenize(content_text, expand_concepts=False)
    )
    overlap = len(query_tokens & content_tokens)
    overlap_ratio = overlap / len(query_tokens)

    normalized_query = " ".join(query.casefold().split())
    normalized_content = " ".join(
        content_text.casefold().split()
    )
    exact_phrase = (
        1.0
        if len(normalized_query) >= 3
        and normalized_query in normalized_content
        else 0.0
    )

    path_tokens = set(
        tokenize(
            chunk.source_path
            + " "
            + (chunk.heading_or_symbol or ""),
            expand_concepts=False,
        )
    )
    path_overlap = len(
        query_tokens & path_tokens
    ) / len(query_tokens)
    precise_identifiers = [
        identifier
        for identifier in re.findall(
            r"[A-Za-z_][A-Za-z0-9_\-]*",
            query,
        )
        if "_" in identifier
        or re.search(r"[a-z][A-Z]", identifier)
    ]
    content_identifier_match = (
        1.0
        if any(
            identifier.casefold()
            in normalized_content
            for identifier in precise_identifiers
            if len(identifier) >= 3
        )
        else 0.0
    )
    normalized_heading = (
        chunk.heading_or_symbol or ""
    ).casefold()
    symbol_match = (
        1.0
        if any(
            identifier.casefold() == normalized_heading
            for identifier in precise_identifiers
        )
        else 0.0
    )

    return min(
        1.0,
        0.45 * overlap_ratio
        + 0.10 * path_overlap
        + 0.05 * exact_phrase
        + 0.15 * content_identifier_match
        + 0.25 * symbol_match,
    )


def _has_precise_identifier(query: str) -> bool:
    return bool(
        re.search(
            r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+",
            query,
        )
        or re.search(
            r"[a-z][A-Z]",
            query,
        )
    )


class ScopedHybridRetriever:
    """只在指定仓库和学习模块中检索。"""

    def __init__(
        self,
        chunks: list[DocumentChunk],
        *,
        repository_scope_id: str,
        module_scope_id: str,
        dimensions: int = DEFAULT_VECTOR_DIMENSIONS,
    ) -> None:
        if dimensions < 64:
            raise ValueError(
                "dimensions 必须大于等于 64"
            )

        self.repository_scope_id = repository_scope_id
        self.module_scope_id = module_scope_id
        self.dimensions = dimensions
        self.chunks = [
            DocumentChunk.model_validate(chunk)
            for chunk in chunks
            if chunk.repository_scope_id
            == repository_scope_id
            and chunk.module_scope_id
            == module_scope_id
        ]
        self._vectors = [
            _hashed_vector(
                "\n".join(
                    [
                        chunk.source_path,
                        chunk.heading_or_symbol or "",
                        chunk.content,
                    ]
                ),
                dimensions=dimensions,
            )
            for chunk in self.chunks
        ]

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
        min_score: float = DEFAULT_MIN_SCORE,
    ) -> RetrievalResult:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("query 不能为空")
        if top_k < 1:
            raise ValueError("top_k 必须大于等于 1")
        if not 0.0 <= min_score <= 1.0:
            raise ValueError(
                "min_score 必须在 0 到 1 之间"
            )

        if not self.chunks:
            return RetrievalResult(
                query=clean_query,
                repository_scope_id=(
                    self.repository_scope_id
                ),
                module_scope_id=self.module_scope_id,
                hits=[],
                evidence_sufficient=False,
                reason="当前仓库和学习模块没有可检索片段。",
            )

        query_vector = _hashed_vector(
            clean_query,
            dimensions=self.dimensions,
        )
        precise_identifier = _has_precise_identifier(
            clean_query
        )
        ranked_hits: list[RetrievalHit] = []

        for chunk, chunk_vector in zip(
            self.chunks,
            self._vectors,
        ):
            vector_score = _cosine_score(
                query_vector,
                chunk_vector,
            )
            keyword_score = _keyword_score(
                clean_query,
                chunk,
            )
            prior = min(
                1.0,
                math.log1p(chunk.relevance_score)
                / math.log1p(100.0),
            )

            if precise_identifier:
                score = (
                    0.35 * vector_score
                    + 0.60 * keyword_score
                    + 0.05 * prior
                )
            else:
                score = (
                    0.60 * vector_score
                    + 0.35 * keyword_score
                    + 0.05 * prior
                )

            ranked_hits.append(
                RetrievalHit(
                    chunk=chunk,
                    score=round(
                        max(0.0, min(1.0, score)),
                        6,
                    ),
                    vector_score=round(
                        vector_score,
                        6,
                    ),
                    keyword_score=round(
                        keyword_score,
                        6,
                    ),
                )
            )

        ranked_hits.sort(
            key=lambda hit: (
                -hit.score,
                -hit.keyword_score,
                hit.chunk.source_path.casefold(),
                hit.chunk.line_start,
            )
        )
        best = ranked_hits[0]
        evidence_sufficient = (
            best.score >= min_score
            and (
                best.keyword_score > 0
                # 纯向量命中需要更高门槛，
                # 防止特征哈希碰撞产生假相关。
                or best.vector_score
                >= max(0.22, min_score + 0.08)
            )
        )

        if not evidence_sufficient:
            return RetrievalResult(
                query=clean_query,
                repository_scope_id=(
                    self.repository_scope_id
                ),
                module_scope_id=self.module_scope_id,
                hits=[],
                evidence_sufficient=False,
                reason=(
                    "当前学习模块内没有足够相关的证据，"
                    "请提供更具体的文件、符号或 Issue。"
                ),
            )

        eligible_hits = [
            hit
            for hit in ranked_hits
            if hit.score >= min_score
            and (
                hit.keyword_score > 0
                or hit.vector_score
                >= max(0.22, min_score + 0.08)
            )
        ]
        selected_hits = eligible_hits[:top_k]

        return RetrievalResult(
            query=clean_query,
            repository_scope_id=self.repository_scope_id,
            module_scope_id=self.module_scope_id,
            hits=selected_hits,
            evidence_sufficient=True,
            reason=(
                "已在当前仓库和学习模块范围内"
                f"返回 {len(selected_hits)} 个候选片段。"
            ),
        )
