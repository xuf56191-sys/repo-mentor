"""8 月 31 日：带来源学习问答的离线测试。"""

from repo_mentor.grounded_qa import (
    REFUSAL_TEXT,
    answer_learning_question,
)
from repo_mentor.hybrid_retriever import ScopedHybridRetriever
from repo_mentor.retrieval_models import DocumentChunk


def make_chunk() -> DocumentChunk:
    content = (
        "def route_after_evidence(state):\n"
        "    if state.get('repo_evidence'):\n"
        "        return 'enough_evidence'"
    )
    return DocumentChunk(
        chunk_id="chunk-grounded-answer-001",
        repository_scope_id="repo-grounded-001",
        module_scope_id="module-grounded-001",
        source_path="src/repo_mentor/adaptive_workflow.py",
        source_type="python",
        content=content,
        line_start=10,
        line_end=12,
        heading_or_symbol="route_after_evidence",
        relevance_score=100.0,
        relevance_reasons=["当前任务来源"],
        content_hash="a" * 64,
    )


def make_retriever() -> ScopedHybridRetriever:
    return ScopedHybridRetriever(
        [make_chunk()],
        repository_scope_id="repo-grounded-001",
        module_scope_id="module-grounded-001",
    )


def test_answer_has_real_path_and_line_range():
    answer = answer_learning_question(
        "route_after_evidence 如何判断证据充分？",
        make_retriever(),
    )

    assert answer.evidence_sufficient is True
    assert len(answer.citations) == 1
    assert answer.citations[0].source_path == (
        "src/repo_mentor/adaptive_workflow.py"
    )
    assert answer.citations[0].line_start == 10
    assert answer.citations[0].excerpt in make_chunk().content
    assert "adaptive_workflow.py:10-12" in answer.answer


def test_unrelated_question_is_refused_without_citations():
    answer = answer_learning_question(
        "怎样烤制草莓蛋糕？",
        make_retriever(),
    )

    assert answer.evidence_sufficient is False
    assert answer.citations == []
    assert answer.answer == REFUSAL_TEXT


def test_empty_question_is_rejected():
    try:
        answer_learning_question("  ", make_retriever())
    except ValueError as error:
        assert "question 不能为空" in str(error)
    else:
        raise AssertionError("空问题必须被拒绝")
