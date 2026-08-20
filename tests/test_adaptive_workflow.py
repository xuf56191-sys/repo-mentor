from pathlib import Path
import pytest
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
    make_thread_config,
    resume_adaptive_workflow,
    run_adaptive_workflow,
    start_adaptive_workflow,
    route_after_request,
    route_after_evidence,
    route_after_confirmation,
    start_adaptive_workflow,
    resume_adaptive_workflow,
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
    """图结构测试：10 个业务节点、有限证据循环和人工确认闭环均已注册。"""
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
        "confirm_roadmap",
        "apply_human_revision",
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
    assert (
               "generate_roadmap",
               "confirm_roadmap",
           ) in edges

    assert (
               "confirm_roadmap",
               "apply_human_revision",
           ) in edges

    assert (
               "apply_human_revision",
               "analyze_learner",
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

    result = build_adaptive_graph().invoke(
        {
            "learner_input": learner_input,
            "target_input": make_target().model_dump(mode="json"),
            "repository_path": "not-used",
            "repo_evidence": [],
            "messages": [],
            "errors": [],
            "step_count": 0,
        },
        config=make_thread_config("missing-time"),
    )

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

    result = build_adaptive_graph().invoke(
        {
            "learner_input": make_learner().model_dump(mode="json"),
            "target_input": make_target().model_dump(mode="json"),
            "repository_path": "not-used",
            "repo_evidence": [],
            "messages": [],
            "errors": [],
            "step_count": 0,
        },
        config=make_thread_config("empty-evidence"),
    )

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

    result = build_adaptive_graph().invoke(
        initial,
        config=make_thread_config("bounded-loop"),
    )

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

    result = build_adaptive_graph().invoke(
        initial,
        config=make_thread_config("second-read-succeeds"),
    )

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


def test_route_after_confirmation_chooses_correct_branch():
    assert route_after_confirmation({
        "confirmation_status": "approved",
    }) == "approved"

    assert route_after_confirmation({
        "confirmation_status": "revision_requested",
    }) == "revision_requested"


def test_route_after_confirmation_rejects_invalid_status():
    with pytest.raises(
        ValueError,
        match="人工确认路由收到非法状态",
    ):
        route_after_confirmation({
            "confirmation_status": "not_requested",
        })


def test_same_thread_can_resume_after_confirmation(
    monkeypatch,
    tmp_path: Path,
):
    """相同 thread_id 可以从路线确认中断点继续。"""
    repo = make_mini_repo(tmp_path)

    # 用确定性的假生成器替代真实 LLM，避免网络和费用。
    monkeypatch.setattr(
        adaptive_nodes,
        "generate_structured_roadmap",
        fake_generator,
    )

    # InMemorySaver 绑定在编译后的 app 上，恢复时必须复用它。
    app = build_adaptive_graph()
    thread_id = "confirmation-session-a"

    # 第一次调用会执行到 confirm_roadmap，并在 interrupt() 暂停。
    paused = start_adaptive_workflow(
        app,
        thread_id=thread_id,
        repository_path=str(repo),
        learner_profile=make_learner(),
        target_task=make_target(),
    )

    assert "__interrupt__" in paused

    interrupt_value = paused["__interrupt__"][0].value
    assert interrupt_value["kind"] == "roadmap_confirmation"
    assert interrupt_value["allowed_actions"] == [
        "approve",
        "revise",
    ]

    # Command(resume=...) 不携带旧状态；相同 thread_id 负责定位它。
    resumed = resume_adaptive_workflow(
        app,
        thread_id=thread_id,
        confirmation={"action": "approve"},
    )

    assert resumed["confirmation_status"] == "approved"
    assert resumed["human_confirmation"].action == "approve"
    assert isinstance(resumed["roadmap"], LearningRoadmap)
    assert "__interrupt__" not in resumed

    # next 为空元组表示工作流已经执行到 END，没有待运行节点。
    snapshot = app.get_state(
        make_thread_config(thread_id)
    )
    assert snapshot.next == ()


def test_different_threads_are_isolated(
    monkeypatch,
    tmp_path: Path,
):
    """不同 thread_id 的 checkpoint 状态必须互不干扰。"""
    repo = make_mini_repo(tmp_path)

    # 使用同一个确定性假生成器，使测试只关注会话隔离，
    # 不受 LLM 网络请求和随机输出影响。
    monkeypatch.setattr(
        adaptive_nodes,
        "generate_structured_roadmap",
        fake_generator,
    )

    # 两个会话必须共用同一个 app：
    # 这样才能证明隔离来自 thread_id，而不是来自两个独立 Saver。
    app = build_adaptive_graph()

    target_a = make_target().model_copy(
        update={
            "title": "理解目录树扫描",
        }
    )
    target_b = make_target().model_copy(
        update={
            "title": "学习人工确认节点",
            "description": "理解人工确认节点的中断与恢复流程",
            "expected_outcome": "能够解释人工确认节点如何恢复执行",
        }
    )

    # 会话 A、B 分别使用不同的 thread_id 启动，
    # 两者都会停在各自的 confirm_roadmap interrupt 上。
    paused_a = start_adaptive_workflow(
        app,
        thread_id="session-a",
        repository_path=str(repo),
        learner_profile=make_learner(),
        target_task=target_a,
    )
    paused_b = start_adaptive_workflow(
        app,
        thread_id="session-b",
        repository_path=str(repo),
        learner_profile=make_learner(),
        target_task=target_b,
    )

    assert "__interrupt__" in paused_a
    assert "__interrupt__" in paused_b

    # 每个 interrupt payload 都应携带自己会话中的目标，
    # 不能因为共用 app 而相互覆盖。
    payload_a = paused_a["__interrupt__"][0].value
    payload_b = paused_b["__interrupt__"][0].value
    assert payload_a["target"]["title"] == target_a.title
    assert payload_b["target"]["title"] == target_b.title

    # 只批准会话 A。Checkpointer 会通过 session-a 找到 A 的暂停点。
    resumed_a = resume_adaptive_workflow(
        app,
        thread_id="session-a",
        confirmation={"action": "approve"},
    )
    assert resumed_a["confirmation_status"] == "approved"
    assert resumed_a["target_task"].title == target_a.title

    # A 已到达 END，所以没有待执行节点。
    snapshot_a = app.get_state(
        make_thread_config("session-a")
    )
    assert snapshot_a.next == ()

    # B 没有收到 resume，仍应停在自己的确认节点，
    # 并继续保存 B 的目标和未确认状态。
    snapshot_b = app.get_state(
        make_thread_config("session-b")
    )
    assert snapshot_b.next == ("confirm_roadmap",)
    assert snapshot_b.values["target_task"].title == target_b.title
    assert snapshot_b.values["confirmation_status"] == "not_requested"


def test_revising_target_regenerates_roadmap(
    monkeypatch,
    tmp_path: Path,
):
    """修改目标后清理旧派生状态，并用新目标重新生成路线。"""
    repo = make_mini_repo(tmp_path)
    generated_target_titles: list[str] = []

    def tracking_generator(
        user_profile,
        target_task,
        repository_readme,
        repository_tree,
    ) -> LearningRoadmap:
        """记录每次生成路线时真正收到的目标标题。"""
        generated_target_titles.append(target_task["title"])
        return fake_generator(
            user_profile=user_profile,
            target_task=target_task,
            repository_readme=repository_readme,
            repository_tree=repository_tree,
        )

    monkeypatch.setattr(
        adaptive_nodes,
        "generate_structured_roadmap",
        tracking_generator,
    )

    app = build_adaptive_graph()
    thread_id = "revision-session"
    original_target = make_target()

    # 第一轮先按原目标生成路线，并停在人工确认节点。
    first_pause = start_adaptive_workflow(
        app,
        thread_id=thread_id,
        repository_path=str(repo),
        learner_profile=make_learner(),
        target_task=original_target,
    )
    assert "__interrupt__" in first_pause
    first_payload = first_pause["__interrupt__"][0].value
    assert first_payload["target"]["title"] == original_target.title
    assert first_payload["revision_count"] == 0

    revised_title = "掌握 LangGraph checkpoint 恢复"
    revised_description = "理解 checkpoint、thread_id 与中断恢复的协作流程"
    revised_outcome = "能够实现可暂停、可修改并可恢复的工作流"

    # revise 会先恢复 confirm_roadmap，再进入 apply_human_revision。
    # 修订节点重建严格模型、清理旧派生状态，然后重新执行分析和生成。
    second_pause = resume_adaptive_workflow(
        app,
        thread_id=thread_id,
        confirmation={
            "action": "revise",
            "target_updates": {
                "title": revised_title,
                "description": revised_description,
                "expected_outcome": revised_outcome,
            },
        },
    )

    # 新路线生成后会再次进入 confirm_roadmap，因此第二次仍应中断。
    assert "__interrupt__" in second_pause
    second_payload = second_pause["__interrupt__"][0].value
    assert second_payload["target"]["title"] == revised_title
    assert second_payload["roadmap"]["target_task"]["title"] == (
        revised_title
    )
    assert second_payload["revision_count"] == 1

    # 生成器被调用两次，且第二次收到的已经是修改后的目标。
    assert generated_target_titles == [
        original_target.title,
        revised_title,
    ]

    # 第二次中断时，checkpoint 中保存的是新领域模型和新路线。
    revised_snapshot = app.get_state(
        make_thread_config(thread_id)
    )
    assert revised_snapshot.next == ("confirm_roadmap",)
    assert revised_snapshot.values["target_task"].title == revised_title
    assert revised_snapshot.values["roadmap"].target_task.title == (
        revised_title
    )
    assert revised_snapshot.values["revision_count"] == 1

    # 用户最终批准第二版路线，同一会话才真正到达 END。
    final_result = resume_adaptive_workflow(
        app,
        thread_id=thread_id,
        confirmation={"action": "approve"},
    )
    assert final_result["confirmation_status"] == "approved"
    assert final_result["human_confirmation"].action == "approve"
    assert final_result["target_task"].title == revised_title
    assert final_result["roadmap"].target_task.title == revised_title

    final_snapshot = app.get_state(
        make_thread_config(thread_id)
    )
    assert final_snapshot.next == ()
