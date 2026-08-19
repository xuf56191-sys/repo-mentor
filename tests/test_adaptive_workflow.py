from pathlib import Path
from repo_mentor.workflow_state import create_initial_state
from repo_mentor import adaptive_nodes
from repo_mentor.models import (
    DailyPlan,
    EvidenceSource,
    LearnerProfile,
    LearningRoadmap,
    LearningTask,
    TargetTask,
    RepositoryEvidence,
)
from repo_mentor.repository_safeguards import EvidenceBudget
from repo_mentor.adaptive_workflow import (
    GRAPH_RECURSION_LIMIT,
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
    """图结构测试：8 个业务节点和有限循环均已注册。"""
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
        "read_more_evidence",
        "conservative_evidence_stop",
    } <= node_ids

    # 边必须按流程图顺序连接
    edges = {(e.source,e.target) for e in graph.edges}
    assert ("inspect_request", "analyze_learner") in edges
    assert ("inspect_request", "request_clarification") in edges
    assert ("analyze_learner", "analyze_target") in edges
    assert ("analyze_target", "collect_evidence") in edges
    assert ("collect_evidence", "generate_roadmap") in edges
    assert ("collect_evidence", "read_more_evidence") in edges
    assert (
               "collect_evidence",
               "conservative_evidence_stop",
           ) in edges

    assert (
               "read_more_evidence",
               "generate_roadmap",
           ) in edges
    assert (
               "read_more_evidence",
               "read_more_evidence",
           ) in edges
    assert (
               "read_more_evidence",
               "conservative_evidence_stop",
           ) in edges

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


def make_repository_evidence(
    snippet: str | None,
) -> RepositoryEvidence:
    """构造路径证据或内容证据。"""
    return RepositoryEvidence(
        source_path="src/repository_tree.py",
        snippet=snippet,
        reason="与目标模块相关。",
        confidence=0.8,
    )


def test_route_after_evidence_prefers_success_at_step_limit():
    """第2次补读获得内容后，应生成路线而不是停止。"""
    state = {
        "repo_evidence": [
            make_repository_evidence(
                "def build_tree():\n    return 'tree'"
            )
        ],
        "step_count": 2,
        "max_steps": 2,
        "evidence_candidates": [],
        "read_evidence_files": [],
    }

    assert (
        route_after_evidence(state)
        == "enough_evidence"
    )


def test_route_after_evidence_reads_more_when_allowed():
    """只有路径证据且仍有候选文件时，继续补读。"""
    state = {
        "repo_evidence": [
            make_repository_evidence(None)
        ],
        "step_count": 0,
        "max_steps": 2,
        "evidence_budget": EvidenceBudget(max_files=2),
        "evidence_candidates": [
            "src/repository_tree.py"
        ],
        "read_evidence_files": [],
    }

    assert route_after_evidence(state) == "read_more"


def test_route_after_evidence_stops_at_step_limit():
    """没有内容证据且达到补读上限时停止。"""
    state = {
        "repo_evidence": [
            make_repository_evidence(None)
        ],
        "step_count": 2,
        "max_steps": 2,
        "evidence_candidates": [
            "src/repository_tree.py"
        ],
        "read_evidence_files": [],
    }

    assert route_after_evidence(state) == "stop"


def test_route_after_evidence_stops_when_budget_stopped():
    """预算对象已经停止时，不得继续读取。"""
    state = {
        "repo_evidence": [
            make_repository_evidence(None)
        ],
        "step_count": 0,
        "max_steps": 2,
        "evidence_budget": EvidenceBudget(
            max_files=2,
            stopped=True,
            stop_reason="文件读取预算已耗尽。",
        ),
        "evidence_candidates": [
            "src/repository_tree.py"
        ],
        "read_evidence_files": [],
    }

    assert route_after_evidence(state) == "stop"


def test_route_after_evidence_stops_without_unread_candidates():
    """所有候选文件都尝试过后必须停止。"""
    state = {
        "repo_evidence": [
            make_repository_evidence(None)
        ],
        "step_count": 1,
        "max_steps": 2,
        "evidence_budget": EvidenceBudget(max_files=2),
        "evidence_candidates": [
            "src/repository_tree.py"
        ],
        "read_evidence_files": [
            "src/repository_tree.py"
        ],
    }

    assert route_after_evidence(state) == "stop"


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


def test_graph_routes_empty_evidence_to_conservative_stop(
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
    assert result["evidence_stop_reason"] == (
        "没有尚未读取的候选文件。"
    )

    question = result["clarification_questions"][0]
    assert "证据补充已停止" in question
    assert "没有尚未读取的候选文件" in question
    assert "源码内容" in question
    assert "roadmap" not in result

def test_bounded_evidence_loop_stops_after_two_failed_reads(
    monkeypatch,
    tmp_path: Path,
):
    """连续读取失败时，循环最多执行 max_steps 次。"""
    candidates = [
        "src/a.py",
        "src/b.py",
        "src/c.py",
    ]
    read_calls: list[str] = []

    def fake_collect_evidence(state):
        """只返回路径证据，不返回源码内容。"""
        return {
            "repo_evidence": [
                RepositoryEvidence(
                    source_path="src/a.py",
                    snippet=None,
                    reason="候选文件路径与目标相关。",
                    confidence=0.7,
                )
            ],
            "repo_readme": "",
            "repo_tree": "",
            "evidence_candidates": candidates,
        }

    class AlwaysFailingReadTool:
        """记录读取路径，并模拟所有文件读取失败。"""

        def invoke(self, arguments):
            relative_path = arguments["relative_path"]
            read_calls.append(relative_path)

            return {
                "ok": False,
                "error_type": "file_not_found",
                "message": f"无法读取 {relative_path}",
            }

    monkeypatch.setattr(
        adaptive_nodes,
        "collect_evidence",
        fake_collect_evidence,
    )
    monkeypatch.setattr(
        adaptive_nodes,
        "read_repo_file",
        AlwaysFailingReadTool(),
    )

    initial = create_initial_state(
        make_learner(),
        make_target(),
    )
    initial.update({
        "learner_input": (
            make_learner().model_dump(mode="json")
        ),
        "target_input": (
            make_target().model_dump(mode="json")
        ),
        "repository_path": str(tmp_path),
    })

    result = build_adaptive_graph().invoke(initial)

    # 最核心的有限循环断言：
    # 即使有三个候选文件，也只能读取前两个。
    assert read_calls == [
        "src/a.py",
        "src/b.py",
    ]
    assert "src/c.py" not in read_calls

    assert result["step_count"] == 2
    assert result["read_evidence_files"] == [
        "src/a.py",
        "src/b.py",
    ]

    # 读取失败不消耗“成功读取文件”预算。
    assert result["evidence_budget"].used_files == 0

    assert result["evidence_stop_reason"] == (
        "已达到最多 2 次证据补读上限。"
    )
    assert result["missing_fields"] == ["repo_evidence"]
    assert "roadmap" not in result

    # 两次失败都通过 errors reducer 累积下来。
    assert len(result["errors"]) == 2

def test_evidence_loop_finishes_when_second_read_succeeds(
    monkeypatch,
    tmp_path: Path,
):
    """第二次补读成功时，应退出循环并生成路线。"""
    candidates = [
        "src/a.py",
        "src/b.py",
        "src/c.py",
    ]
    read_calls: list[str] = []

    def fake_collect_evidence(state):
        return {
            "repo_evidence": [
                RepositoryEvidence(
                    source_path="src/a.py",
                    snippet=None,
                    reason="候选文件路径与目标相关。",
                    confidence=0.7,
                )
            ],
            "repo_readme": "",
            "repo_tree": "",
            "evidence_candidates": candidates,
        }

    class SecondReadSucceedsTool:
        """第一次失败，第二次返回真实内容证据。"""

        def invoke(self, arguments):
            relative_path = arguments["relative_path"]
            read_calls.append(relative_path)

            if len(read_calls) == 1:
                return {
                    "ok": False,
                    "error_type": "file_not_found",
                    "message": f"无法读取 {relative_path}",
                }

            return {
                "ok": True,
                "source_path": relative_path,
                "size_bytes": 40,
                "content": (
                    "def build_tree():\n"
                    "    return 'tree'\n"
                ),
            }

    monkeypatch.setattr(
        adaptive_nodes,
        "collect_evidence",
        fake_collect_evidence,
    )
    monkeypatch.setattr(
        adaptive_nodes,
        "read_repo_file",
        SecondReadSucceedsTool(),
    )
    monkeypatch.setattr(
        adaptive_nodes,
        "generate_structured_roadmap",
        fake_generator,
    )

    initial = create_initial_state(
        make_learner(),
        make_target(),
    )
    initial.update({
        "learner_input": (
            make_learner().model_dump(mode="json")
        ),
        "target_input": (
            make_target().model_dump(mode="json")
        ),
        "repository_path": str(tmp_path),
    })

    result = build_adaptive_graph().invoke(initial)

    assert read_calls == [
        "src/a.py",
        "src/b.py",
    ]
    assert "src/c.py" not in read_calls

    assert result["step_count"] == 2
    assert result["read_evidence_files"] == [
        "src/a.py",
        "src/b.py",
    ]

    # 第一次失败不消耗预算，第二次成功消耗一个文件预算。
    assert result["evidence_budget"].used_files == 1

    # 新增证据中必须包含真正读取到的源码。
    assert any(
        evidence.snippet
        and "def build_tree" in evidence.snippet
        for evidence in result["repo_evidence"]
    )

    assert len(result["errors"]) == 1
    assert isinstance(result["roadmap"], LearningRoadmap)
    assert result["missing_fields"] == []