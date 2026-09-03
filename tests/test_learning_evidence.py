"""9 月 1 日：路线、测验和问答复用证据层。"""

from repo_mentor.learning_evidence import (
    LearningEvidenceLayer,
    merge_repository_evidence,
)
from repo_mentor.models import RepositoryEvidence
from repo_mentor.retrieval_models import (
    DocumentChunk,
    DocumentLoadResult,
)


def make_layer() -> LearningEvidenceLayer:
    chunk = DocumentChunk(
        chunk_id="chunk-shared-evidence-001",
        repository_scope_id="repo-shared-001",
        module_scope_id="module-shared-001",
        source_path="src/repo_mentor/models.py",
        source_type="python",
        content="class TargetTask(StrictModel):\n    pass",
        line_start=170,
        line_end=171,
        heading_or_symbol="TargetTask",
        relevance_score=100.0,
        relevance_reasons=["当前任务来源"],
        content_hash="b" * 64,
    )
    loaded = DocumentLoadResult(
        repository_scope_id="repo-shared-001",
        module_scope_id="module-shared-001",
        documents=[],
        warnings=[],
        used_files=1,
        used_chars=len(chunk.content),
    )
    return LearningEvidenceLayer(
        load_result=loaded,
        chunks=(chunk,),
    )


def test_same_chunks_support_retrieval_answer_and_evidence():
    layer = make_layer()

    retrieval = layer.retrieve("TargetTask 在哪里定义？")
    answer = layer.answer("TargetTask 在哪里定义？")
    evidence = layer.repository_evidence(
        "TargetTask 在哪里定义？"
    )

    assert retrieval.hits[0].chunk is layer.chunks[0]
    assert answer.citations[0].source_path == (
        "src/repo_mentor/models.py"
    )
    assert evidence[0].source_path == (
        "src/repo_mentor/models.py"
    )


def test_merge_adds_without_overwriting_or_duplicating():
    first = RepositoryEvidence(
        source_path="README.md",
        snippet="scope",
        reason="原有证据",
        confidence=1.0,
    )
    duplicate = first.model_copy(
        update={"reason": "检索再次命中"}
    )
    second = RepositoryEvidence(
        source_path="src/repo_mentor/models.py",
        snippet="class TargetTask",
        reason="新增证据",
        confidence=0.8,
    )

    merged = merge_repository_evidence(
        [first],
        [duplicate, second],
    )

    assert merged == [first, second]
