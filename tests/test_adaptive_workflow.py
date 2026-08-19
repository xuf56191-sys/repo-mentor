from pathlib import Path

from repo_mentor import adaptive_nodes
from repo_mentor.models import (
    DailyPlan,
    EvidenceSource,
    LearnerProfile,
    LearningRoadmap,
    LearningTask,
    TargetTask,
)

from repo_mentor.adaptive_workflow import (
    build_adaptive_graph,
    run_adaptive_workflow,
    route_after_request,
    route_after_evidence,
)


def make_learner() -> LearnerProfile:
    return LearnerProfile(
        current_level="beginner",
        known_skills=["python"],
        unfamiliar_skills=["pydantic"],
        learning_goal="理解目录树扫描",
        daily_hours=2.0,
        available_days=7,
    )

def make_target() -> TargetTask:
    return TargetTask(
        title="理解目录树扫描",
        description="理解仓库目录树生成流程",
        task_type="understand_module",
        expected_outcome="能说明目录树生成流程",
    )


def make_mini_repo(tmp_path: Path) -> Path:
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


def fake_generator(
    user_profile,
    target_task,
    repository_readme,
    repository_tree,
) -> LearningRoadmap:
    """假生成器：返回一个最小但真实的 LearningRoadmap。"""
    learner = LearnerProfile.model_validate(user_profile)
    target = TargetTask.model_validate(target_task)

    task = LearningTask(
        title="理解目录树扫描",
        objective="能说明目录树生成流程",
        evidence_sources=[
            EvidenceSource(
                file_path="src/repository_tree.py",
                evidence_type="source",
                reason="核心实现",
            )
        ],
        reading_task="阅读核心源码实现",
        code_location_task="定位核心文件",
        practice_task="写个小练习",
        completion_criteria=["能解释流程"],
        estimated_hours=1.0,
    )
    return LearningRoadmap(
        learner_profile=learner,
        target_task=target,
        learner_summary="离线测试路线",
        skill_gaps=["pydantic"],
        daily_plans=[
            DailyPlan(
                day=1,
                theme="核心流程",
                tasks=[task],
                daily_outcome="能说明流程",
            )
        ],
        total_estimated_hours=1.0,
    )

def test_graph_has_expected_nodes():
    """图结构测试：4 个节点都注册了，顺序与流程图一致。"""
    graph = build_adaptive_graph().get_graph()
    # graph.nodes 是 dict，迭代得到节点 id（含虚拟 __start__/__end__）
    node_ids = set(graph.nodes)
    assert {
        "inspect_request",
        "request_clarification",
        "analyze_learner",
        "analyze_target",
        "collect_evidence",
        "generate_roadmap",
    } <= node_ids

    # 边必须按流程图顺序连接
    edges = {(e.source,e.target) for e in graph.edges}
    assert ("inspect_request", "analyze_learner") in edges
    assert ("inspect_request", "request_clarification") in edges
    assert ("analyze_learner", "analyze_target") in edges
    assert ("analyze_target", "collect_evidence") in edges
    assert ("collect_evidence", "generate_roadmap") in edges
    assert ("collect_evidence", "request_clarification") in edges

def test_run_adaptive_workflow_returns_roadmap(
        monkeypatch,
        tmp_path:Path,
):
    """整合测试：整条图一次 invoke 产出 LearningRoadmap（LLM 打桩）。"""
    repo = make_mini_repo(tmp_path)
    # 用假生成器替换真实 LLM 依赖（测试不花钱不联网）
    monkeypatch.setattr(
        adaptive_nodes,
        "generate_structured_roadmap",
        fake_generator,
    )

    roadmap = run_adaptive_workflow(
        repository_path=str(repo),
        learner_profile=make_learner(),
        target_task=make_target(),
    )

    assert isinstance(roadmap, LearningRoadmap)
    assert roadmap.daily_plans[0].tasks[0].title == "理解目录树扫描"


def test_route_after_request_chooses_correct_branch():
    assert route_after_request({
        "missing_fields": ["learner_input.daily_hours"],
    }) == "needs_clarification"

    assert route_after_request({
        "missing_fields": [],
    }) == "ready"


def test_route_after_evidence_chooses_correct_branch():
    assert route_after_evidence({
        "repo_evidence": [],
    }) == "needs_clarification"

    assert route_after_evidence({
        "repo_evidence": [object()],
    }) == "enough_evidence"


def test_graph_routes_missing_time_to_clarification():
    learner_input = make_learner().model_dump(mode="json")
    learner_input.pop("daily_hours")

    result = build_adaptive_graph().invoke({
        "learner_input": learner_input,
        "target_input": make_target().model_dump(mode="json"),
        "repository_path": "not-used",
        "repo_evidence": [],
        "messages": [],
        "errors": [],
        "step_count": 0,
    })

    assert result["missing_fields"] == [
        "learner_input.daily_hours"
    ]
    assert result["clarification_questions"] == [
        "请提供每天可投入的学习时间（小时数）。"
    ]
    assert "roadmap" not in result


def test_graph_routes_empty_evidence_to_clarification(
    monkeypatch,
):
    def fake_empty_evidence(state):
        return {
            "repo_evidence": [],
            "repo_readme": "",
            "repo_tree": "",
        }

    monkeypatch.setattr(
        adaptive_nodes,
        "collect_evidence",
        fake_empty_evidence,
    )

    result = build_adaptive_graph().invoke({
        "learner_input": make_learner().model_dump(mode="json"),
        "target_input": make_target().model_dump(mode="json"),
        "repository_path": "not-used",
        "repo_evidence": [],
        "messages": [],
        "errors": [],
        "step_count": 0,
    })

    assert result["missing_fields"] == ["repo_evidence"]
    assert result["clarification_questions"] == [
        "当前仓库证据不足，请提供更具体的目标文件、"
        "模块名称或 Issue 信息。"
    ]
    assert "roadmap" not in result
