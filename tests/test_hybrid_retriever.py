"""限定范围混合检索的单元测试。"""

from repo_mentor.hybrid_retriever import (
    ScopedHybridRetriever,
)
from repo_mentor.retrieval_models import DocumentChunk


REPOSITORY_SCOPE = "repo-test-scope"
MODULE_SCOPE = "module-test-scope"


def make_chunk(
    *,
    chunk_id: str,
    source_path: str,
    content: str,
    heading: str,
    repository_scope_id: str = REPOSITORY_SCOPE,
    module_scope_id: str = MODULE_SCOPE,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        repository_scope_id=repository_scope_id,
        module_scope_id=module_scope_id,
        source_path=source_path,
        source_type="python",
        content=content,
        line_start=10,
        line_end=20,
        heading_or_symbol=heading,
        relevance_score=100.0,
        relevance_reasons=["当前学习任务直接引用"],
        content_hash="a" * 64,
    )


def make_chunks() -> list[DocumentChunk]:
    return [
        make_chunk(
            chunk_id="chunk-checkpoint-0001",
            source_path="src/repo_mentor/adaptive_workflow.py",
            heading="resume_mastery_workflow",
            content=(
                "Command(resume=answers) 使用相同 thread_id "
                "从 checkpoint 恢复 interrupt 中断的会话位置。"
            ),
        ),
        make_chunk(
            chunk_id="chunk-graph-000000002",
            source_path="src/repo_mentor/adaptive_workflow.py",
            heading="build_adaptive_graph",
            content=(
                "def build_adaptive_graph():\n"
                "    graph = StateGraph(AgentState)\n"
                "    return graph.compile()"
            ),
        ),
        make_chunk(
            chunk_id="chunk-sensitive-00003",
            source_path="src/repo_mentor/repository_tools.py",
            heading="ensure_safe_relative_path",
            content=(
                "ensure_safe_relative_path 会拒绝 .env、"
                "敏感凭据、密钥和被忽略的路径。"
            ),
        ),
    ]


def make_retriever(
    chunks: list[DocumentChunk] | None = None,
) -> ScopedHybridRetriever:
    return ScopedHybridRetriever(
        chunks or make_chunks(),
        repository_scope_id=REPOSITORY_SCOPE,
        module_scope_id=MODULE_SCOPE,
    )


def test_semantic_vector_finds_resume_evidence():
    result = make_retriever().retrieve(
        "程序暂停以后，怎样从上次位置继续会话？"
    )

    assert result.evidence_sufficient is True
    assert result.hits[0].chunk.heading_or_symbol == (
        "resume_mastery_workflow"
    )
    assert result.hits[0].vector_score > 0


def test_keyword_fallback_prioritizes_exact_identifier():
    result = make_retriever().retrieve(
        "build_adaptive_graph 在哪里定义？"
    )

    assert result.evidence_sufficient is True
    assert result.hits[0].chunk.heading_or_symbol == (
        "build_adaptive_graph"
    )
    assert result.hits[0].keyword_score > 0


def test_concept_expansion_finds_sensitive_path_rule():
    result = make_retriever().retrieve(
        "如何避免读取仓库中的凭据和密钥文件？"
    )

    assert result.evidence_sufficient is True
    assert result.hits[0].chunk.heading_or_symbol == (
        "ensure_safe_relative_path"
    )


def test_retriever_filters_other_repository_and_module():
    foreign_chunk = make_chunk(
        chunk_id="chunk-foreign-0000001",
        source_path="foreign.py",
        heading="build_adaptive_graph",
        content="build_adaptive_graph exact exact exact",
        repository_scope_id="repo-foreign-scope",
    )
    retriever = make_retriever(
        [*make_chunks(), foreign_chunk]
    )

    result = retriever.retrieve(
        "build_adaptive_graph"
    )

    assert all(
        hit.chunk.repository_scope_id
        == REPOSITORY_SCOPE
        for hit in result.hits
    )
    assert all(
        hit.chunk.source_path != "foreign.py"
        for hit in result.hits
    )


def test_unrelated_question_returns_insufficient_evidence():
    result = make_retriever().retrieve(
        "如何烘焙巧克力蛋糕？"
    )

    assert result.evidence_sufficient is False
    assert result.hits == []
    assert "证据" in result.reason


def test_top_k_limits_returned_chunks():
    result = make_retriever().retrieve(
        "工作流节点如何恢复？",
        top_k=2,
    )

    assert result.evidence_sufficient is True
    assert len(result.hits) == 2
    assert all(
        0.0 <= hit.score <= 1.0
        for hit in result.hits
    )
