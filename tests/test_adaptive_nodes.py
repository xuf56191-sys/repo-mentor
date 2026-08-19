"""tests/test_adaptive_nodes.py：四个节点的独立单元测试。

设计原则：
- 每个节点只测"它自己"的输入输出，不依赖其他节点；
- generate_roadmap 用 monkeypatch 替换 LLM 依赖：
  测试不花钱、不联网、可重复。
"""

from pathlib import Path
from repo_mentor.repository_safeguards import EvidenceBudget
from repo_mentor.models import LearnerProfile, TargetTask
from repo_mentor.adaptive_nodes import (
    analyze_learner,
    analyze_target,
    collect_evidence,
    generate_roadmap,
    inspect_request,
    request_clarification,
    read_more_evidence,
    conservative_evidence_stop,
)


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