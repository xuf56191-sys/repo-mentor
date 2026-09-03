"""V0.8 限定检索的严格数据模型。"""

from typing import Annotated, Literal

from pydantic import (
    Field,
    StringConstraints,
    model_validator,
)

from repo_mentor.models import StrictModel


RetrievalSourceType = Literal[
    "readme",
    "docs",
    "python",
    "test",
    "config",
]


class ScopedDocument(StrictModel):
    """通过安全和学习相关性过滤的文档。"""

    repository_scope_id: str = Field(min_length=8)
    module_scope_id: str = Field(min_length=8)
    source_path: str = Field(min_length=1)
    source_type: RetrievalSourceType
    # 原文不能继承 StrictModel 的自动去首尾空白，
    # 否则开头空行被删除后行号会失真。
    content: Annotated[
        str,
        StringConstraints(
            min_length=1,
            strip_whitespace=False,
        ),
    ]
    size_bytes: int = Field(ge=0)
    priority: int = Field(ge=0, le=3)
    relevance_score: float = Field(ge=0.0)
    relevance_reasons: list[str] = Field(min_length=1)
    content_hash: str = Field(min_length=64, max_length=64)


class DocumentChunk(StrictModel):
    """一个可检索且可定位回原文的证据片段。"""

    chunk_id: str = Field(min_length=16)
    repository_scope_id: str = Field(min_length=8)
    module_scope_id: str = Field(min_length=8)
    source_path: str = Field(min_length=1)
    source_type: RetrievalSourceType
    content: str = Field(min_length=1)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    heading_or_symbol: str | None = None
    relevance_score: float = Field(ge=0.0)
    relevance_reasons: list[str] = Field(min_length=1)
    content_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_line_range(self) -> "DocumentChunk":
        if self.line_end < self.line_start:
            raise ValueError(
                "line_end 不能小于 line_start"
            )
        return self


class DocumentLoadResult(StrictModel):
    """当前学习模块的文档加载结果。"""

    repository_scope_id: str = Field(min_length=8)
    module_scope_id: str = Field(min_length=8)
    documents: list[ScopedDocument] = Field(
        default_factory=list
    )
    warnings: list[str] = Field(default_factory=list)
    used_files: int = Field(ge=0)
    used_chars: int = Field(ge=0)


class RetrievalHit(StrictModel):
    """一条混合检索命中及可解释分数。"""

    chunk: DocumentChunk
    score: float = Field(ge=0.0, le=1.0)
    vector_score: float = Field(ge=0.0, le=1.0)
    keyword_score: float = Field(ge=0.0, le=1.0)


class RetrievalResult(StrictModel):
    """限定在仓库和学习模块内的检索结果。"""

    query: str = Field(min_length=1)
    repository_scope_id: str = Field(min_length=8)
    module_scope_id: str = Field(min_length=8)
    hits: list[RetrievalHit] = Field(default_factory=list)
    evidence_sufficient: bool
    reason: str = Field(min_length=3)


class SourceCitation(StrictModel):
    """回答中可以定位回真实仓库文件的引用。"""

    source_path: str = Field(min_length=1)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    excerpt: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_line_range(self) -> "SourceCitation":
        if self.line_end < self.line_start:
            raise ValueError(
                "line_end 不能小于 line_start"
            )
        return self


class GroundedLearningAnswer(StrictModel):
    """只回答当前学习任务且带真实来源的结果。"""

    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    citations: list[SourceCitation] = Field(
        default_factory=list
    )
    evidence_sufficient: bool
    uncertainty: str | None = None
    scope_note: str = Field(min_length=3)

    @model_validator(mode="after")
    def validate_grounding(self) -> "GroundedLearningAnswer":
        if self.evidence_sufficient and not self.citations:
            raise ValueError(
                "证据充分的回答必须至少包含一个引用"
            )
        if not self.evidence_sufficient and self.citations:
            raise ValueError(
                "拒答结果不应携带未经确认的引用"
            )
        return self
