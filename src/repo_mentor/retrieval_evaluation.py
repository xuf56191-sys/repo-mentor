"""V0.8 限定检索的 20 问题真实来源与拒答评测。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from repo_mentor.document_loader import load_documents, split_documents
from repo_mentor.hybrid_retriever import ScopedHybridRetriever
from repo_mentor.models import EvidenceSource, LearningTask, TargetTask


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES_PATH = PROJECT_ROOT / "evaluation" / "retrieval_cases.json"


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    question: str
    expected_paths: tuple[str, ...]
    should_refuse: bool = False


@dataclass(frozen=True)
class RetrievalEvaluationOutcome:
    question: str
    expected_paths: tuple[str, ...]
    returned_paths: tuple[str, ...]
    should_refuse: bool
    passed: bool


@dataclass(frozen=True)
class RetrievalEvaluationReport:
    outcomes: tuple[RetrievalEvaluationOutcome, ...]

    @property
    def source_cases(self) -> tuple[RetrievalEvaluationOutcome, ...]:
        return tuple(item for item in self.outcomes if not item.should_refuse)

    @property
    def refusal_cases(self) -> tuple[RetrievalEvaluationOutcome, ...]:
        return tuple(item for item in self.outcomes if item.should_refuse)

    @property
    def passed_count(self) -> int:
        return sum(item.passed for item in self.outcomes)

    @property
    def total_count(self) -> int:
        return len(self.outcomes)

    @property
    def top3_hit_rate(self) -> float:
        cases = self.source_cases
        return sum(item.passed for item in cases) / len(cases) if cases else 0.0

    @property
    def refusal_rate(self) -> float:
        cases = self.refusal_cases
        return sum(item.passed for item in cases) / len(cases) if cases else 0.0

    @property
    def unrelated_question_rejected(self) -> bool:
        """兼容 V0.8 前十题评测使用的旧属性。"""
        return bool(self.refusal_cases) and self.refusal_rate == 1.0

    @property
    def unbounded_baseline_unsupported_answer_rate(self) -> float:
        """“所有问题都回答”基线在越界题上的不可靠回答率。"""
        return 1.0 if self.refusal_cases else 0.0

    @property
    def scoped_unsupported_answer_rate(self) -> float:
        return 1.0 - self.refusal_rate

    @property
    def all_passed(self) -> bool:
        return self.passed_count == self.total_count


EVALUATION_SOURCE_PATHS = (
    "docs/retrieval-scope.md",
    "src/repo_mentor/document_loader.py",
    "src/repo_mentor/grounded_qa.py",
    "src/repo_mentor/hybrid_retriever.py",
    "src/repo_mentor/learning_evidence.py",
    "src/repo_mentor/retrieval_models.py",
    "src/repo_mentor/repository_reader.py",
    "src/repo_mentor/repository_tree.py",
    "src/repo_mentor/repository_ranker.py",
    "src/repo_mentor/repository_tools.py",
    "src/repo_mentor/repository_safeguards.py",
)


def load_evaluation_cases(
    cases_path: str | Path = DEFAULT_CASES_PATH,
) -> tuple[RetrievalEvaluationCase, ...]:
    """从公开 JSON 载入并校验评测案例。"""
    raw_cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    if not isinstance(raw_cases, list) or len(raw_cases) != 20:
        raise ValueError("retrieval_cases.json 必须恰好包含 20 个案例")

    cases: list[RetrievalEvaluationCase] = []
    for raw in raw_cases:
        question = str(raw.get("question") or "").strip()
        expected_paths = tuple(raw.get("expected_paths") or [])
        should_refuse = bool(raw.get("should_refuse"))
        if not question:
            raise ValueError("评测问题不能为空")
        if should_refuse == bool(expected_paths):
            raise ValueError(
                "拒答案例不能配置期望来源，来源案例必须配置期望来源"
            )
        cases.append(
            RetrievalEvaluationCase(
                question=question,
                expected_paths=expected_paths,
                should_refuse=should_refuse,
            )
        )
    return tuple(cases)


EVALUATION_CASES = load_evaluation_cases()


def build_evaluation_task() -> tuple[TargetTask, LearningTask]:
    target = TargetTask(
        title="理解 RepoMentor V0.8 限定检索证据链",
        description="理解安全读取、目标排序、切分、检索和带来源问答",
        task_type="understand_module",
        expected_outcome="能定位证据加载、排名、隔离、引用和拒答实现",
    )
    task = LearningTask(
        title="验证 V0.8 目标限定检索",
        objective="统计 20 个问题的 Top-3 来源命中率和越界拒答率",
        evidence_sources=[
            EvidenceSource(
                file_path=path,
                evidence_type="source",
                reason="V0.8 检索证据链的已批准来源",
            )
            for path in EVALUATION_SOURCE_PATHS
        ],
        reading_task="阅读限定检索和 grounded answer 的设计与实现",
        code_location_task="定位读取、切分、混合排名、引用和拒答函数",
        practice_task="运行 20 问题 Top-3 来源与拒答评测",
        completion_criteria=[
            "来源问题的期望真实文件进入 Top-3",
            "越界问题无命中且明确拒答",
        ],
        estimated_hours=1.0,
    )
    return target, task


def run_retrieval_evaluation(
    repository_path: str | Path = PROJECT_ROOT,
    *,
    cases_path: str | Path = DEFAULT_CASES_PATH,
) -> RetrievalEvaluationReport:
    target, task = build_evaluation_task()
    loaded = load_documents(repository_path, target, task)
    chunks = split_documents(loaded.documents)
    retriever = ScopedHybridRetriever(
        chunks,
        repository_scope_id=loaded.repository_scope_id,
        module_scope_id=loaded.module_scope_id,
    )

    outcomes: list[RetrievalEvaluationOutcome] = []
    for case in load_evaluation_cases(cases_path):
        result = retriever.retrieve(case.question, top_k=3)
        returned_paths = tuple(hit.chunk.source_path for hit in result.hits)
        if case.should_refuse:
            passed = not result.evidence_sufficient and not result.hits
        else:
            passed = result.evidence_sufficient and bool(
                set(case.expected_paths) & set(returned_paths)
            )
        outcomes.append(
            RetrievalEvaluationOutcome(
                question=case.question,
                expected_paths=case.expected_paths,
                returned_paths=returned_paths,
                should_refuse=case.should_refuse,
                passed=passed,
            )
        )
    return RetrievalEvaluationReport(outcomes=tuple(outcomes))


def main() -> None:
    report = run_retrieval_evaluation()
    print("== V0.8 Scoped Retrieval Evaluation (20 cases) ==")
    for index, outcome in enumerate(report.outcomes, start=1):
        status = "PASS" if outcome.passed else "FAIL"
        print(f"{index:02d}. {status} | {outcome.question}")
        print("    Top-3:", ", ".join(outcome.returned_paths) or "REFUSED")
    print(f"Top-3 hit rate: {report.top3_hit_rate:.0%}")
    print(f"Scoped refusal rate: {report.refusal_rate:.0%}")
    print(
        "Unsupported-answer rate (unbounded -> scoped): "
        f"{report.unbounded_baseline_unsupported_answer_rate:.0%} -> "
        f"{report.scoped_unsupported_answer_rate:.0%}"
    )
    if not report.all_passed:
        raise RuntimeError("V0.8 检索评测未通过")
    print("V0.8 RETRIEVAL EVALUATION PASSED")


if __name__ == "__main__":
    main()
