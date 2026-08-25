"""tests/test_adaptive_nodes.py：四个节点的独立单元测试。

设计原则：
- 每个节点只测"它自己"的输入输出，不依赖其他节点；
- generate_roadmap 用 monkeypatch 替换 LLM 依赖：
  测试不花钱、不联网、可重复。
"""

from pathlib import Path
from langgraph.types import Overwrite
from repo_mentor.repository_safeguards import EvidenceBudget
from repo_mentor.models import (
    LearnerProfile,
    RoadmapConfirmation,
    TargetTask,
    DailyPlan,
    EvidenceSource,
    LearningRoadmap,
    LearningTask,
    RepositoryEvidence,
    AssessmentPackage,
    PracticeTask,
    QuizQuestion,
)
from repo_mentor.adaptive_nodes import (
    analyze_learner,
    analyze_target,
    collect_evidence,
    generate_roadmap,
    inspect_request,
    request_clarification,
    read_more_evidence,
    conservative_evidence_stop,
    confirm_roadmap,
    apply_human_revision,
    generate_assessment,
    evaluate_answers,
)
import pytest

def make_learner() -> LearnerProfile:
    """构造一个可复用的学习者画像（测试数据）。"""
    return LearnerProfile(
        current_level="beginner",
        known_skills=["python"],
        unfamiliar_skills=["pydantic"],
        learning_goal="理解目录树扫描",
        daily_hours=2.0,
        available_days=7,
    )


def make_target() -> TargetTask:
    """构造一个可复用的目标任务（测试数据）。"""
    return TargetTask(
        title="理解目录树扫描",
        description="理解仓库目录树生成流程",
        task_type="understand_module",
        expected_outcome="能说明目录树生成流程",
    )

def make_learning_roadmap() -> LearningRoadmap:
    """构造包含两个任务的路线，用于验证节点选择首个任务。"""
    source = EvidenceSource(
        file_path="src/repo_mentor/adaptive_workflow.py",
        evidence_type="source",
        reason="该文件定义正式工作流",
        confidence=1.0,
    )

    first_task = LearningTask(
        title="理解自适应工作流",
        objective="能够解释状态图的节点和路由流程",
        evidence_sources=[source],
        reading_task="阅读自适应工作流源码",
        code_location_task="定位工作流构造函数",
        practice_task="绘制工作流执行路径",
        completion_criteria=["能解释节点顺序"],
        estimated_hours=1.0,
    )
    second_task = LearningTask(
        title="理解评估模型",
        objective="能够解释结构化评估模型",
        evidence_sources=[source],
        reading_task="阅读评估模型定义",
        code_location_task="定位 AssessmentPackage",
        practice_task="构造一个评估包",
        completion_criteria=["能解释评估包结构"],
        estimated_hours=1.0,
    )

    return LearningRoadmap(
        learner_profile=make_learner(),
        target_task=make_target(),
        learner_summary="具备 Python 基础，需要学习 LangGraph",
        skill_gaps=["langgraph"],
        daily_plans=[
            DailyPlan(
                day=1,
                theme="工作流",
                tasks=[first_task],
                daily_outcome="理解自适应工作流",
            ),
            DailyPlan(
                day=2,
                theme="评估模型",
                tasks=[second_task],
                daily_outcome="理解评估模型结构",
            ),
        ],
        total_estimated_hours=2.0,
    )

def make_node_assessment() -> AssessmentPackage:
    """构造 evaluate_answers 节点测试使用的评估包。"""
    source = EvidenceSource(
        file_path="src/repo_mentor/adaptive_workflow.py",
        evidence_type="source",
        reason="该文件定义正式工作流",
        confidence=1.0,
    )

    concept = QuizQuestion(
        question_id="question-concept",
        question_type="concept",
        prompt="为什么恢复需要相同 thread_id？",
        expected_answer="用于定位对应 checkpoint",
        difficulty="beginner",
        related_task_title="理解自适应工作流",
        evidence_sources=[source],
        knowledge_points=["thread_id"],
    )
    location = QuizQuestion(
        question_id="question-location",
        question_type="code_location",
        prompt="工作流构造函数位于哪个文件？",
        expected_answer=(
            "src/repo_mentor/adaptive_workflow.py"
        ),
        difficulty="beginner",
        related_task_title="理解自适应工作流",
        evidence_sources=[source],
        knowledge_points=["代码定位"],
    )
    practice = PracticeTask(
        practice_id="practice-workflow",
        title="补充工作流测试",
        instructions="为工作流增加节点结构测试",
        expected_outcome="测试能够验证正式节点集合",
        deliverable="一个 pytest 测试函数",
        difficulty="beginner",
        related_task_title="理解自适应工作流",
        evidence_sources=[source],
        knowledge_points=["pytest"],
        completion_criteria=["测试能够通过"],
        estimated_hours=0.5,
    )

    return AssessmentPackage(
        assessment_id="assessment-node",
        related_task_title="理解自适应工作流",
        difficulty="beginner",
        questions=[concept, location],
        practice_task=practice,
    )

class FakeRoadmap:
    """只提供确认节点需要的 model_dump 接口。"""

    def model_dump(
        self,
        mode: str,
    ) -> dict:
        assert mode == "json"

        return {
            "learner_summary": "离线测试路线",
            "total_estimated_hours": 2.0,
        }

def make_mini_repo(tmp_path: Path) -> Path:
    """在 pytest 临时目录里造一个最小仓库，供 collect_evidence 测试。"""
    src = tmp_path / "src"
    src.mkdir()
    (src / "repository_tree.py").write_text(
        "def build_tree():\n    return 'tree'\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "# Mini Repo\n\n目录树功能见 `src/repository_tree.py`。",
        encoding="utf-8",
    )
    return tmp_path


# ---------------- 节点 1：analyze_learner ----------------

def test_analyze_learner():
    """输入只有 learner_profile，输出应包含 learner_analysis。"""
    state = {"learner_profile": make_learner()}
    update = analyze_learner(state)

    assert "learner_analysis" in update
    analysis = update["learner_analysis"]
    assert analysis["skill_gaps"] == ["pydantic"]
    assert analysis["current_level"] == "beginner"
    assert analysis["daily_capacity_hours"] == 14.0  # 2.0h × 7 天


# ---------------- 节点 2：analyze_target ----------------

def test_analyze_target():
    """输入只有 target_task，输出应包含目标关键词。"""
    state = {"target_task": make_target()}
    update = analyze_target(state)

    assert "target_analysis" in update
    keywords = update["target_analysis"]["keywords"]
    assert "tree" in keywords
    assert update["target_analysis"]["task_type"] == "understand_module"


# ---------------- 节点 3：collect_evidence ----------------

def test_collect_evidence(tmp_path: Path):
    """对真实小仓库收集证据：证据非空、README/目录树都已取回。"""
    repo = make_mini_repo(tmp_path)
    state = {
        "repository_path": str(repo),
        "target_task": make_target(),
    }
    update = collect_evidence(state)

    assert len(update["repo_evidence"]) > 0
    assert update["repo_readme"]  # 非空
    assert "README.md" in update["repo_tree"]
    assert update["evidence_candidates"]
    assert (
            "src/repository_tree.py"
            in update["evidence_candidates"]
    )
    assert len(update["evidence_candidates"]) == len(
        set(update["evidence_candidates"])
    )


# ---------------- 节点 4：generate_roadmap（monkeypatch 打桩） ----------------

def test_generate_roadmap(monkeypatch):
    """用假生成器替换 LLM 依赖，验证节点正确组装参数并产出 roadmap。"""
    from repo_mentor import adaptive_nodes

    # 记录调用参数，顺便验证节点把 state 的值正确传给了下游
    captured = {}

    def fake_generator(
        user_profile,
        target_task,
        repository_readme,
        repository_tree,
    ):
        captured["readme"] = repository_readme
        captured["tree"] = repository_tree
        return "fake roadmap"

    # monkeypatch：临时替换模块里的真实函数，测试结束后自动还原
    monkeypatch.setattr(
        adaptive_nodes, "generate_structured_roadmap", fake_generator
    )

    # 构造完整输入：generate_roadmap 需要画像、目标、README、目录树
    state = {
        "learner_profile": make_learner(),
        "target_task": make_target(),
        "repo_readme": "这是 README 正文",
        "repo_tree": "demo_repo/  README.md",
    }
    update = adaptive_nodes.generate_roadmap(state)

    assert update["roadmap"] == "fake roadmap"
    assert captured["readme"] == "这是 README 正文"  # 参数正确透传
    assert captured["tree"] == "demo_repo/  README.md"


def test_inspect_request_reports_missing_daily_hours():
    """缺少时间时返回具体问题，不创建严格模型。"""
    learner_input = make_learner().model_dump(mode="json")
    learner_input.pop("daily_hours")

    result = inspect_request({
        "learner_input": learner_input,
        "target_input": make_target().model_dump(mode="json"),
    })

    assert result["missing_fields"] == [
        "learner_input.daily_hours"
    ]
    assert result["clarification_questions"] == [
        "请提供每天可投入的学习时间（小时数）。"
    ]
    assert "learner_profile" not in result
    assert "target_task" not in result


def test_inspect_request_builds_validated_models():
    """信息完整时清空缺失项，并创建严格领域模型。"""
    result = inspect_request({
        "learner_input": make_learner().model_dump(mode="json"),
        "target_input": make_target().model_dump(mode="json"),
    })

    assert result["missing_fields"] == []
    assert result["clarification_questions"] == []
    assert isinstance(result["learner_profile"], LearnerProfile)
    assert isinstance(result["target_task"], TargetTask)


def test_request_clarification_handles_missing_evidence():
    """证据为空时返回可执行的具体澄清问题。"""
    result = request_clarification({
        "missing_fields": [],
        "clarification_questions": [],
    })

    assert result["missing_fields"] == ["repo_evidence"]
    assert result["clarification_questions"] == [
        "当前仓库证据不足，请提供更具体的目标文件、"
        "模块名称或 Issue 信息。"
    ]


# ---------------- 节点 6：read_more_evidence ----------------

def test_read_more_evidence_adds_one_evidence_without_mutating_old_budget(
    tmp_path: Path,
):
    """每次只补读一个文件，并且不原地修改旧预算。"""
    repo = make_mini_repo(tmp_path)
    original_budget = EvidenceBudget(
        max_files=2,
        max_chars=30_000,
    )

    state = {
        "repository_path": str(repo),
        "evidence_candidates": [
            "src/repository_tree.py",
            "README.md",
        ],
        "read_evidence_files": [],
        "step_count": 0,
        "evidence_budget": original_budget,
    }

    update = read_more_evidence(state)

    assert update["step_count"] == 1
    assert update["read_evidence_files"] == [
        "src/repository_tree.py"
    ]
    assert len(update["repo_evidence"]) == 1
    assert (
        update["repo_evidence"][0].source_path
        == "src/repository_tree.py"
    )

    # 旧预算不能被节点原地修改
    assert original_budget.used_files == 0
    assert update["evidence_budget"] is not original_budget
    assert update["evidence_budget"].used_files == 1


def test_read_more_evidence_skips_attempted_file(
    tmp_path: Path,
):
    """已经尝试过的文件必须跳过，不能重复读取。"""
    repo = make_mini_repo(tmp_path)
    budget = EvidenceBudget(
        max_files=2,
        max_chars=30_000,
        used_files=1,
        used_chars=20,
    )

    state = {
        "repository_path": str(repo),
        "evidence_candidates": [
            "src/repository_tree.py",
            "README.md",
        ],
        "read_evidence_files": [
            "src/repository_tree.py"
        ],
        "step_count": 1,
        "evidence_budget": budget,
    }

    update = read_more_evidence(state)

    assert update["step_count"] == 2
    assert update["read_evidence_files"] == [
        "src/repository_tree.py",
        "README.md",
    ]
    assert update["repo_evidence"][0].source_path == "README.md"
    assert update["evidence_budget"].used_files == 2

# ---------------- 节点 7：conservative_evidence_stop ----------------

def test_conservative_evidence_stop_reports_step_limit():
    """达到补读次数上限时，明确说明停止原因和缺少内容。"""
    result = conservative_evidence_stop({
        "step_count": 2,
        "max_steps": 2,
        "evidence_budget": EvidenceBudget(max_files=2),
        "evidence_stop_reason": None,
    })

    assert result["evidence_stop_reason"] == (
        "已达到最多 2 次证据补读上限。"
    )
    assert result["missing_fields"] == ["repo_evidence"]
    assert "源码内容" in result["clarification_questions"][0]


def test_conservative_evidence_stop_preserves_specific_reason():
    """补读节点产生的具体停止原因应优先保留。"""
    result = conservative_evidence_stop({
        "step_count": 1,
        "max_steps": 2,
        "evidence_stop_reason": "文件内容超过剩余字符预算。",
    })

    assert result["evidence_stop_reason"] == (
        "文件内容超过剩余字符预算。"
    )
    assert (
        "文件内容超过剩余字符预算"
        in result["clarification_questions"][0]
    )

# ---------------- 节点 9：confirm_roadmap ----------------

def test_confirm_roadmap_accepts_approval(
    monkeypatch,
):
    """批准恢复值应转换成严格模型和 approved 状态。"""
    from repo_mentor import adaptive_nodes

    captured = {}

    def fake_interrupt(payload):
        captured["payload"] = payload

        return {
            "action": "approve",
        }

    monkeypatch.setattr(
        adaptive_nodes,
        "interrupt",
        fake_interrupt,
    )

    result = confirm_roadmap({
        "learner_profile": make_learner(),
        "target_task": make_target(),
        "roadmap": FakeRoadmap(),
        "revision_count": 0,
    })

    assert result["confirmation_status"] == "approved"
    assert isinstance(
        result["human_confirmation"],
        RoadmapConfirmation,
    )
    assert (
        result["human_confirmation"].action
        == "approve"
    )

    payload = captured["payload"]

    assert payload["kind"] == "roadmap_confirmation"
    assert payload["target"]["title"] == "理解目录树扫描"
    assert payload["learner"]["current_level"] == "beginner"
    assert payload["allowed_actions"] == [
        "approve",
        "revise",
    ]
    assert payload["revision_count"] == 0

def test_confirm_roadmap_accepts_revision(
    monkeypatch,
):
    """修改恢复值应保存更新并进入 revision_requested 状态。"""
    from repo_mentor import adaptive_nodes

    def fake_interrupt(payload):
        return {
            "action": "revise",
            "target_updates": {
                "title": "理解 checkpoint 持久化",
                "description": (
                    "理解 checkpoint 保存和恢复状态的过程"
                ),
                "expected_outcome": (
                    "能够实现可暂停和恢复的工作流"
                ),
            },
        }

    monkeypatch.setattr(
        adaptive_nodes,
        "interrupt",
        fake_interrupt,
    )

    result = confirm_roadmap({
        "learner_profile": make_learner(),
        "target_task": make_target(),
        "roadmap": FakeRoadmap(),
        "revision_count": 1,
    })

    confirmation = result["human_confirmation"]

    assert (
        result["confirmation_status"]
        == "revision_requested"
    )
    assert isinstance(
        confirmation,
        RoadmapConfirmation,
    )
    assert confirmation.action == "revise"
    assert confirmation.target_updates["title"] == (
        "理解 checkpoint 持久化"
    )

# ---------------- 节点 10：apply_human_revision ----------------

    def test_apply_human_revision_rebuilds_target_and_resets_state():
        """目标修改后应重建模型并使旧派生状态失效。"""
        learner = make_learner()
        target = make_target()

        old_budget = EvidenceBudget(
            max_files=3,
            max_chars=12_000,
            used_files=1,
            used_chars=500,
        )

        confirmation = RoadmapConfirmation(
            action="revise",
            target_updates={
                "title": "理解 checkpoint 持久化",
                "description": (
                    "理解 checkpoint 保存和恢复工作流状态的过程"
                ),
                "expected_outcome": (
                    "能够实现可暂停和恢复的 LangGraph 工作流"
                ),
            },
        )

        update = apply_human_revision({
            "learner_profile": learner,
            "target_task": target,
            "learner_input": learner.model_dump(mode="json"),
            "target_input": target.model_dump(mode="json"),
            "human_confirmation": confirmation,
            "confirmation_status": "revision_requested",
            "revision_count": 1,
            "evidence_budget": old_budget,
            "step_count": 2,
            "evidence_candidates": ["src/old.py"],
            "read_evidence_files": ["src/old.py"],
            "evidence_stop_reason": "旧目标证据不足。",
            "roadmap": FakeRoadmap(),
            "errors": ["旧读取错误"],
            "repo_readme": "需要保留的 README",
            "repo_tree": "需要保留的目录树",
        })

        # 修改字段已经更新。
        assert update["target_task"].title == (
            "理解 checkpoint 持久化"
        )
        assert update["target_input"]["title"] == (
            "理解 checkpoint 持久化"
        )

        # 未修改字段继续保留。
        assert (
                update["target_task"].task_type
                == target.task_type
        )
        assert (
                update["target_task"].reference
                == target.reference
        )

        # 学习者没有修改，应保持原值。
        assert (
                update["learner_profile"].current_level
                == learner.current_level
        )
        assert (
                update["learner_profile"].daily_hours
                == learner.daily_hours
        )

        # reducer 字段必须使用 Overwrite 真正清空。
        assert isinstance(
            update["repo_evidence"],
            Overwrite,
        )
        assert update["repo_evidence"].value == []

        assert isinstance(
            update["errors"],
            Overwrite,
        )
        assert update["errors"].value == []

        # 新目标获得全新的读取预算。
        new_budget = update["evidence_budget"]

        assert new_budget is not old_budget
        assert new_budget.max_files == 3
        assert new_budget.max_chars == 12_000
        assert new_budget.used_files == 0
        assert new_budget.used_chars == 0
        assert new_budget.stopped is False

        assert update["step_count"] == 0
        assert update["evidence_candidates"] == []
        assert update["read_evidence_files"] == []
        assert update["evidence_stop_reason"] is None

        assert update["roadmap"] is None
        assert (
                update["confirmation_status"]
                == "not_requested"
        )
        assert update["human_confirmation"] is None
        assert update["revision_count"] == 2

        # 节点不返回这些仓库级字段，
        # LangGraph 合并局部更新时会保留原值。
        assert "repo_readme" not in update
        assert "repo_tree" not in update


def test_apply_human_revision_rebuilds_learner_profile():
    """学习者修改应重新建立 LearnerProfile。"""
    learner = make_learner()
    target = make_target()

    confirmation = RoadmapConfirmation(
        action="revise",
        learner_updates={
            "current_level": "intermediate",
            "daily_hours": 3.0,
        },
    )

    update = apply_human_revision({
        "learner_profile": learner,
        "target_task": target,
        "learner_input": learner.model_dump(mode="json"),
        "target_input": target.model_dump(mode="json"),
        "human_confirmation": confirmation,
        "revision_count": 0,
        "evidence_budget": EvidenceBudget(
            max_files=2,
        ),
    })

    assert (
        update["learner_profile"].current_level
        == "intermediate"
    )
    assert (
        update["learner_profile"].daily_hours
        == 3.0
    )

    # 未修改的学习者字段保留。
    assert (
        update["learner_profile"].available_days
        == learner.available_days
    )
    assert (
        update["learner_profile"].learning_goal
        == learner.learning_goal
    )

    # 目标没有修改。
    assert update["target_task"] == target
    assert update["revision_count"] == 1
    assert update["assessment"] is None
    assert update["learner_answers"] == {}
    assert update["evaluation_results"] == []
    assert update["mastery"] is None

def test_generate_assessment_uses_first_roadmap_task(
    monkeypatch,
):
    """节点应选择路线首个任务并写回 assessment。"""
    from repo_mentor import adaptive_nodes

    roadmap = make_learning_roadmap()
    evidence = [
        RepositoryEvidence(
            source_path=(
                "src/repo_mentor/adaptive_workflow.py"
            ),
            snippet="def build_adaptive_graph(): ...",
            reason="与首个路线任务相关",
            confidence=1.0,
        )
    ]
    fake_assessment = object()
    captured = {}

    def fake_generator(
        *,
        learner_profile,
        learning_task,
        repo_evidence,
    ):
        captured["learner_profile"] = learner_profile
        captured["learning_task"] = learning_task
        captured["repo_evidence"] = repo_evidence
        return fake_assessment

    monkeypatch.setattr(
        adaptive_nodes,
        "generate_structured_assessment",
        fake_generator,
    )

    update = generate_assessment({
        "roadmap": roadmap,
        "learner_profile": roadmap.learner_profile,
        "repo_evidence": evidence,
    })

    assert update["assessment"] is fake_assessment
    assert (
        captured["learning_task"].title
        == "理解自适应工作流"
    )
    assert (
        captured["learner_profile"]
        == roadmap.learner_profile
    )
    assert captured["repo_evidence"] is evidence


def test_generate_assessment_requires_roadmap():
    """没有已生成路线时，不得调用评估生成器。"""
    with pytest.raises(
        ValueError,
        match="必须先存在 LearningRoadmap",
    ):
        generate_assessment({
            "roadmap": None,
        })

def test_evaluate_answers_dispatches_three_item_types(
    monkeypatch,
):
    """三类项目必须进入各自的评估器。"""
    from repo_mentor import adaptive_nodes

    assessment = make_node_assessment()
    concept_result = object()
    location_result = object()
    practice_result = object()
    calls = []

    def fake_concept(question, answer):
        calls.append((
            "concept",
            question.question_id,
            answer,
        ))
        return concept_result

    def fake_location(question, answer):
        calls.append((
            "code_location",
            question.question_id,
            answer,
        ))
        return location_result

    def fake_practice(practice, submission):
        calls.append((
            "practice",
            practice.practice_id,
            submission,
        ))
        return practice_result

    monkeypatch.setattr(
        adaptive_nodes,
        "evaluate_concept_answer",
        fake_concept,
    )
    monkeypatch.setattr(
        adaptive_nodes,
        "evaluate_code_location_answer",
        fake_location,
    )
    monkeypatch.setattr(
        adaptive_nodes,
        "mark_practice_for_human_review",
        fake_practice,
    )

    update = evaluate_answers({
        "assessment": assessment,
        "learner_answers": {
            "question-concept": "用于恢复状态",
            "question-location": (
                "src/repo_mentor/adaptive_workflow.py"
            ),
            "practice-workflow": "已提交测试代码",
        },
    })

    assert calls == [
        (
            "concept",
            "question-concept",
            "用于恢复状态",
        ),
        (
            "code_location",
            "question-location",
            "src/repo_mentor/adaptive_workflow.py",
        ),
        (
            "practice",
            "practice-workflow",
            "已提交测试代码",
        ),
    ]
    assert update["evaluation_results"] == [
        concept_result,
        location_result,
        practice_result,
    ]


def test_evaluate_answers_rejects_unknown_item_id():
    """旧测验或拼错的题目 ID 不能被静默忽略。"""
    assessment = make_node_assessment()

    with pytest.raises(
        ValueError,
        match="未知评估项目.*old-question",
    ):
        evaluate_answers({
            "assessment": assessment,
            "learner_answers": {
                "old-question": "旧题答案",
            },
        })


def test_evaluate_answers_treats_missing_answers_as_empty(
    monkeypatch,
):
    """缺失答案应交给各评估器保守处理。"""
    from repo_mentor import adaptive_nodes

    assessment = make_node_assessment()
    received = []

    def record_concept(question, answer):
        received.append(("concept", answer))
        return object()

    def record_location(question, answer):
        received.append(("location", answer))
        return object()

    def record_practice(practice, submission):
        received.append(("practice", submission))
        return object()

    monkeypatch.setattr(
        adaptive_nodes,
        "evaluate_concept_answer",
        record_concept,
    )
    monkeypatch.setattr(
        adaptive_nodes,
        "evaluate_code_location_answer",
        record_location,
    )
    monkeypatch.setattr(
        adaptive_nodes,
        "mark_practice_for_human_review",
        record_practice,
    )

    evaluate_answers({
        "assessment": assessment,
        "learner_answers": {},
    })

    assert received == [
        ("concept", ""),
        ("location", ""),
        ("practice", ""),
    ]