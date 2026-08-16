"""tests/test_adaptive_nodes.py：四个节点的独立单元测试。

设计原则：
- 每个节点只测"它自己"的输入输出，不依赖其他节点；
- generate_roadmap 用 monkeypatch 替换 LLM 依赖：
  测试不花钱、不联网、可重复。
"""

from pathlib import Path

from repo_mentor.models import LearnerProfile, TargetTask
from repo_mentor.adaptive_nodes import (
    analyze_learner,
    analyze_target,
    collect_evidence,
    generate_roadmap,
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
