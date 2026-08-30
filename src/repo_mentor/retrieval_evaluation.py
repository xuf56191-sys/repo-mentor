"""V0.8 限定混合检索的 10 问题真实来源评测。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repo_mentor.document_loader import (
    load_documents,
    split_documents,
)
from repo_mentor.hybrid_retriever import (
    ScopedHybridRetriever,
)
from repo_mentor.models import (
    EvidenceSource,
    LearningTask,
    TargetTask,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    question: str
    expected_paths: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalEvaluationOutcome:
    question: str
    expected_paths: tuple[str, ...]
    returned_paths: tuple[str, ...]
    passed: bool


@dataclass(frozen=True)
class RetrievalEvaluationReport:
    outcomes: tuple[RetrievalEvaluationOutcome, ...]
    unrelated_question_rejected: bool

    @property
    def passed_count(self) -> int:
        return sum(
            outcome.passed
            for outcome in self.outcomes
        )

    @property
    def total_count(self) -> int:
        return len(self.outcomes)

    @property
    def all_passed(self) -> bool:
        return (
            self.passed_count == self.total_count
            and self.unrelated_question_rejected
        )


EVALUATION_SOURCE_PATHS = (
    "docs/retrieval-scope.md",
    "src/repo_mentor/document_loader.py",
    "src/repo_mentor/hybrid_retriever.py",
    "src/repo_mentor/retrieval_models.py",
    "src/repo_mentor/repository_reader.py",
    "src/repo_mentor/repository_tree.py",
    "src/repo_mentor/repository_ranker.py",
    "src/repo_mentor/repository_tools.py",
    "src/repo_mentor/repository_safeguards.py",
)


EVALUATION_CASES = (
    RetrievalEvaluationCase(
        question="MAX_TEXT_FILE_BYTES 单文件字节上限在哪里定义？",
        expected_paths=(
            "src/repo_mentor/repository_reader.py",
        ),
    ),
    RetrievalEvaluationCase(
        question="目录树如何限制 max_depth 和 max_files？",
        expected_paths=(
            "src/repo_mentor/repository_tree.py",
        ),
    ),
    RetrievalEvaluationCase(
        question="rank_target_files 如何根据 TargetTask 排序候选文件？",
        expected_paths=(
            "src/repo_mentor/repository_ranker.py",
        ),
    ),
    RetrievalEvaluationCase(
        question="ensure_safe_relative_path 如何拒绝 .env 敏感路径？",
        expected_paths=(
            "src/repo_mentor/repository_tools.py",
            "src/repo_mentor/repository_tree.py",
        ),
    ),
    RetrievalEvaluationCase(
        question="EvidenceBudget 如何限制文件数和字符数？",
        expected_paths=(
            "src/repo_mentor/repository_safeguards.py",
        ),
    ),
    RetrievalEvaluationCase(
        question="DocumentChunk 如何保留 source_path 和 line_start？",
        expected_paths=(
            "src/repo_mentor/retrieval_models.py",
            "src/repo_mentor/document_loader.py",
        ),
    ),
    RetrievalEvaluationCase(
        question="_segment_starts 如何用 ast 按 Python 类和函数边界切分？",
        expected_paths=(
            "src/repo_mentor/document_loader.py",
        ),
    ),
    RetrievalEvaluationCase(
        question="混合检索如何合并 vector_score 和 keyword_score？",
        expected_paths=(
            "src/repo_mentor/hybrid_retriever.py",
        ),
    ),
    RetrievalEvaluationCase(
        question="为什么 RepoMentor 不做全仓 RAG 和安全分析？",
        expected_paths=(
            "docs/retrieval-scope.md",
        ),
    ),
    RetrievalEvaluationCase(
        question="repository_scope_id 和 module_scope_id 如何防止检索串数据？",
        expected_paths=(
            "src/repo_mentor/retrieval_models.py",
            "src/repo_mentor/hybrid_retriever.py",
            "docs/retrieval-scope.md",
        ),
    ),
)


def build_evaluation_task() -> tuple[TargetTask, LearningTask]:
    target = TargetTask(
        title="理解 RepoMentor V0.8 限定检索证据链",
        description=(
            "理解仓库安全读取、目标排序、"
            "文档切分和混合检索之间的关系"
        ),
        task_type="understand_module",
        expected_outcome=(
            "能定位限定检索的安全、加载、"
            "排名和范围隔离实现"
        ),
    )
    task = LearningTask(
        title="验证 V0.8 目标限定检索",
        objective="使 10 个学习问题的真实来源进入 Top-3",
        evidence_sources=[
            EvidenceSource(
                file_path=path,
                evidence_type="source",
                reason="V0.8 检索证据链的已批准来源",
            )
            for path in EVALUATION_SOURCE_PATHS
        ],
        reading_task="阅读限定检索设计和实现",
        code_location_task="定位读取、切分、向量和关键词排名函数",
        practice_task="运行 10 问题 Top-3 来源评测",
        completion_criteria=[
            "10 个学习问题的预期真实来源进入 Top-3",
            "无关问题返回证据不足",
        ],
        estimated_hours=1.0,
    )
    return target, task


def run_retrieval_evaluation(
    repository_path: str | Path = PROJECT_ROOT,
) -> RetrievalEvaluationReport:
    target, task = build_evaluation_task()
    loaded = load_documents(
        repository_path,
        target,
        task,
    )
    chunks = split_documents(loaded.documents)
    retriever = ScopedHybridRetriever(
        chunks,
        repository_scope_id=loaded.repository_scope_id,
        module_scope_id=loaded.module_scope_id,
    )

    outcomes: list[RetrievalEvaluationOutcome] = []
    for case in EVALUATION_CASES:
        result = retriever.retrieve(
            case.question,
            top_k=3,
        )
        returned_paths = tuple(
            hit.chunk.source_path
            for hit in result.hits
        )
        outcomes.append(
            RetrievalEvaluationOutcome(
                question=case.question,
                expected_paths=case.expected_paths,
                returned_paths=returned_paths,
                passed=(
                    result.evidence_sufficient
                    and bool(
                        set(case.expected_paths)
                        & set(returned_paths)
                    )
                ),
            )
        )

    unrelated = retriever.retrieve(
        "如何为巧克力蛋糕制作草莓奶油装饰？",
        top_k=3,
    )

    return RetrievalEvaluationReport(
        outcomes=tuple(outcomes),
        unrelated_question_rejected=(
            not unrelated.evidence_sufficient
            and not unrelated.hits
        ),
    )


def main() -> None:
    report = run_retrieval_evaluation()

    print("== V0.8 Scoped Hybrid Retrieval Evaluation ==")
    for index, outcome in enumerate(
        report.outcomes,
        start=1,
    ):
        status = "PASS" if outcome.passed else "FAIL"
        print(f"{index:02d}. {status} | {outcome.question}")
        print("    Top-3:", ", ".join(outcome.returned_paths))

    print(
        "Unrelated question:",
        "PASS" if report.unrelated_question_rejected else "FAIL",
    )
    print(
        f"Result: {report.passed_count}/{report.total_count}"
    )

    if not report.all_passed:
        raise RuntimeError("V0.8 检索评测未通过")

    print("V0.8 RETRIEVAL EVALUATION PASSED")


if __name__ == "__main__":
    main()
