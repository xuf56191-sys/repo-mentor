import pytest

from repo_mentor.assessment_generator import (
    infer_assessment_difficulty,
    normalize_repo_path,
    select_assessment_evidence,
    generate_structured_assessment,
    validate_assessment_against_context,
)
from repo_mentor.models import (
    AssessmentPackage,
    EvidenceSource,
    LearnerProfile,
    LearningTask,
    PracticeTask,
    QuizQuestion,
    RepositoryEvidence,
)
from repo_mentor import assessment_generator

def make_learner(
    current_level: str,
) -> LearnerProfile:
    return LearnerProfile(
        current_level=current_level,
        known_skills=["python"],
        unfamiliar_skills=["langgraph"],
        learning_goal="理解 LangGraph 工作流",
        daily_hours=2.0,
        available_days=7,
    )

def make_assessment_package(
    *,
    difficulty: str = "beginner",
    source_path: str = (
        "src/repo_mentor/adaptive_workflow.py"
    ),
    excerpt: str | None = (
        "def build_adaptive_graph():"
    ),
    requires_human_review: bool = True,
) -> AssessmentPackage:
    """构造结构有效、上下文可进一步校验的评估包。"""
    source = EvidenceSource(
        file_path=source_path,
        evidence_type="source",
        reason="该文件包含工作流构造函数",
        excerpt=excerpt,
        confidence=1.0,
    )

    concept = QuizQuestion(
        question_id="question-concept",
        question_type="concept",
        prompt="build_adaptive_graph 的职责是什么？",
        expected_answer="负责组装并编译自适应工作流",
        difficulty=difficulty,
        related_task_title="理解自适应工作流",
        evidence_sources=[source],
        knowledge_points=["StateGraph"],
    )
    location = QuizQuestion(
        question_id="question-location",
        question_type="code_location",
        prompt="build_adaptive_graph 定义在哪个文件？",
        expected_answer=source_path,
        difficulty=difficulty,
        related_task_title="理解自适应工作流",
        evidence_sources=[source],
        knowledge_points=["代码定位"],
    )
    practice = PracticeTask(
        practice_id="practice-workflow",
        title="补充工作流测试",
        instructions="为工作流图增加节点结构测试",
        expected_outcome="测试能够验证正式节点集合",
        deliverable="一个 pytest 测试函数",
        difficulty=difficulty,
        related_task_title="理解自适应工作流",
        evidence_sources=[source],
        knowledge_points=["StateGraph", "pytest"],
        completion_criteria=["测试能够通过"],
        estimated_hours=0.5,
        requires_human_review=requires_human_review,
    )

    return AssessmentPackage(
        assessment_id="assessment-workflow",
        related_task_title="理解自适应工作流",
        difficulty=difficulty,
        questions=[concept, location],
        practice_task=practice,
    )

def make_learning_task() -> LearningTask:
    return LearningTask(
        title="理解自适应工作流",
        objective="能够解释状态图的节点和路由流程",
        evidence_sources=[
            EvidenceSource(
                file_path=(
                    "src/repo_mentor/adaptive_workflow.py"
                ),
                evidence_type="source",
                reason="该文件定义正式工作流",
                confidence=1.0,
            ),
            EvidenceSource(
                file_path="README.md",
                evidence_type="readme",
                reason="README 描述工作流结构",
                confidence=1.0,
            ),
        ],
        reading_task="阅读自适应工作流实现",
        code_location_task="定位条件路由函数",
        practice_task="绘制工作流执行路径",
        completion_criteria=[
            "能说明节点执行顺序",
        ],
        estimated_hours=1.0,
    )


def make_repo_evidence(
    source_path: str,
    snippet: str | None,
) -> RepositoryEvidence:
    return RepositoryEvidence(
        source_path=source_path,
        snippet=snippet,
        reason="与当前路线任务相关",
        confidence=0.9,
    )

class FakeStructuredLLM:
    """模拟 with_structured_output() 返回的模型。"""

    def __init__(self, parsed):
        self.parsed = parsed
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return {
            "parsed": self.parsed,
            "parsing_error": None,
            "raw": None,
        }


class FakeLLM:
    """记录结构化输出参数，不进行网络请求。"""

    def __init__(self, parsed):
        self.structured = FakeStructuredLLM(parsed)
        self.schema = None

    def with_structured_output(
        self,
        schema,
        **kwargs,
    ):
        self.schema = schema
        assert kwargs["method"] == "function_calling"
        assert kwargs["include_raw"] is True
        return self.structured

def test_normalize_repo_path():
    assert normalize_repo_path(
        r"SRC\Repo_Mentor\Adaptive_Workflow.py"
    ) == "src/repo_mentor/adaptive_workflow.py"


@pytest.mark.parametrize(
    ("current_level", "expected"),
    [
        ("beginner", "beginner"),
        ("Python 初学者", "beginner"),
        ("intermediate", "intermediate"),
        ("正在进阶学习", "intermediate"),
        ("advanced", "advanced"),
        ("高级 Python 开发者", "advanced"),
        ("无法识别的描述", "beginner"),
    ],
)
def test_infer_assessment_difficulty(
    current_level,
    expected,
):
    learner = make_learner(current_level)

    assert (
        infer_assessment_difficulty(learner)
        == expected
    )


def test_select_assessment_evidence_uses_only_verified_task_files():
    task = make_learning_task()

    selected = select_assessment_evidence(
        task,
        [
            # 路径分隔符和大小写不同，但应该匹配。
            make_repo_evidence(
                r"SRC\REPO_MENTOR\ADAPTIVE_WORKFLOW.PY",
                "def build_adaptive_graph():\n    ...",
            ),

            # 相同文件的重复证据应该被去重。
            make_repo_evidence(
                "src/repo_mentor/adaptive_workflow.py",
                "duplicate content",
            ),

            # 路线任务引用了 README，但没有内容证据。
            make_repo_evidence(
                "README.md",
                None,
            ),

            # 有内容，但不属于当前路线任务引用的文件。
            make_repo_evidence(
                "src/repo_mentor/config.py",
                "def load_settings(): ...",
            ),
        ],
    )

    assert len(selected) == 1
    assert selected[0].source_path == (
        r"SRC\REPO_MENTOR\ADAPTIVE_WORKFLOW.PY"
    )
    assert "build_adaptive_graph" in selected[0].snippet


def test_select_assessment_evidence_rejects_path_only_evidence():
    task = make_learning_task()

    with pytest.raises(
        ValueError,
        match="没有可用于生成测验的真实内容证据",
    ):
        select_assessment_evidence(
            task,
            [
                make_repo_evidence(
                    "src/repo_mentor/adaptive_workflow.py",
                    None,
                ),
                make_repo_evidence(
                    "README.md",
                    "   ",
                ),
            ],
        )

def test_generate_structured_assessment_uses_filtered_context(
    monkeypatch,
):
    learner = make_learner("beginner")
    task = make_learning_task()
    package = make_assessment_package()
    fake_llm = FakeLLM(package)

    monkeypatch.setattr(
        assessment_generator,
        "create_llm",
        lambda **kwargs: fake_llm,
    )

    result = generate_structured_assessment(
        learner_profile=learner,
        learning_task=task,
        repo_evidence=[
            make_repo_evidence(
                "src/repo_mentor/adaptive_workflow.py",
                (
                    "def build_adaptive_graph():\n"
                    "    return graph.compile()"
                ),
            ),
            # 不属于当前路线任务，不能进入 Prompt。
            make_repo_evidence(
                "src/repo_mentor/config.py",
                "SECRET_UNRELATED_CONTENT",
            ),
        ],
    )

    assert result == package
    assert fake_llm.schema is AssessmentPackage

    rendered_messages = str(
        fake_llm.structured.messages
    )
    assert "build_adaptive_graph" in rendered_messages
    assert "SECRET_UNRELATED_CONTENT" not in rendered_messages


def test_validation_rejects_unauthorized_file():
    learner = make_learner("beginner")
    task = make_learning_task()
    package = make_assessment_package(
        source_path="src/repo_mentor/nonexistent.py",
        excerpt=None,
    )
    evidence = [
        make_repo_evidence(
            "src/repo_mentor/adaptive_workflow.py",
            "def build_adaptive_graph(): ...",
        )
    ]

    with pytest.raises(
        ValueError,
        match="引用了未授权仓库文件",
    ):
        validate_assessment_against_context(
            package,
            task,
            infer_assessment_difficulty(learner),
            evidence,
        )


def test_validation_rejects_fabricated_excerpt():
    learner = make_learner("beginner")
    task = make_learning_task()
    package = make_assessment_package(
        excerpt="def nonexistent_function():",
    )
    evidence = [
        make_repo_evidence(
            "src/repo_mentor/adaptive_workflow.py",
            "def build_adaptive_graph(): ...",
        )
    ]

    with pytest.raises(
        ValueError,
        match="证据中不存在的 excerpt",
    ):
        validate_assessment_against_context(
            package,
            task,
            infer_assessment_difficulty(learner),
            evidence,
        )


def test_validation_rejects_wrong_difficulty():
    learner = make_learner("beginner")
    task = make_learning_task()
    package = make_assessment_package(
        difficulty="advanced",
        excerpt=None,
    )
    evidence = [
        make_repo_evidence(
            "src/repo_mentor/adaptive_workflow.py",
            "def build_adaptive_graph(): ...",
        )
    ]

    with pytest.raises(
        ValueError,
        match="难度与学习者当前水平不一致",
    ):
        validate_assessment_against_context(
            package,
            task,
            infer_assessment_difficulty(learner),
            evidence,
        )


def test_validation_requires_human_review_for_practice():
    learner = make_learner("beginner")
    task = make_learning_task()
    package = make_assessment_package(
        excerpt=None,
        requires_human_review=False,
    )
    evidence = [
        make_repo_evidence(
            "src/repo_mentor/adaptive_workflow.py",
            "def build_adaptive_graph(): ...",
        )
    ]

    with pytest.raises(
        ValueError,
        match="必须标记为需要人工复核",
    ):
        validate_assessment_against_context(
            package,
            task,
            infer_assessment_difficulty(learner),
            evidence,
        )