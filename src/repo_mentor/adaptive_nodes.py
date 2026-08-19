"""V0.6 自适应工作流的核心节点。

每个节点 = 函数(state) -> 局部更新 dict，LangGraph 负责 merge：

- inspect_request       ：检查原始输入并构造严格领域模型
- request_clarification ：生成具体的澄清问题（纯规则，无 LLM）
- analyze_learner       ：分析学习者画像（纯规则，无 LLM）
- analyze_target        ：分析目标任务关键词（纯规则）
- collect_evidence      ：收集目标相关证据（复用 V0.4 证据层）
- generate_roadmap      ：调用 LLM 生成学习路线（唯一需要 LLM 的节点）

节点间接力：analyze_learner / analyze_target 的中间产物
→ collect_evidence 收集证据 → generate_roadmap 产出路线。
"""

from __future__ import annotations
from dataclasses import replace
from repo_mentor.repository_tools import read_repo_file
from repo_mentor.models import (
    LearnerProfile,
    RepositoryEvidence,
    TargetTask,
)
from repo_mentor.repository_ranker import (
    extract_target_keywords,  # 从目标任务提取文件路径关键词
    rank_target_files,        # V0.4 目标相关文件排序
)
from repo_mentor.repository_reader import (
    read_repository_onboarding_docs,  # 读取 README 等入门资料
)
from repo_mentor.repository_tree import build_tree  # 生成目录树
from repo_mentor.roadmap_generator import (
    generate_structured_roadmap,  # 现有路线生成器（内部调 LLM）
)
from repo_mentor.workflow_state import AgentState  # 共享状态定义


# ---------------- 节点 1：检查原始请求信息（纯规则，无 LLM） ----------------

def inspect_request(state: AgentState) -> dict:
    """检查原始输入；信息完整时转换为严格领域模型。"""
    learner_input = state.get("learner_input") or {}
    target_input = state.get("target_input") or {}

    missing_fields: list[str] = []
    clarification_questions: list[str] = []

    # 先安全读取并清理文本字段
    current_level = str(
        learner_input.get("current_level") or ""
    ).strip()

    learning_goal = str(
        learner_input.get("learning_goal") or ""
    ).strip()

    title = str(
        target_input.get("title") or ""
    ).strip()

    description = str(
        target_input.get("description") or ""
    ).strip()

    task_type = str(
        target_input.get("task_type") or ""
    ).strip()

    expected_outcome = str(
        target_input.get("expected_outcome") or ""
    ).strip()

    # 检查学习者信息
    if len(current_level) < 2:
        missing_fields.append("learner_input.current_level")
        clarification_questions.append(
            "请说明你当前的技术水平。"
        )

    if len(learning_goal) < 2:
        missing_fields.append("learner_input.learning_goal")
        clarification_questions.append(
            "请提供具体的学习目标（至少两个字符）。"
        )

    if learner_input.get("daily_hours") is None:
        missing_fields.append("learner_input.daily_hours")
        clarification_questions.append(
            "请提供每天可投入的学习时间（小时数）。"
        )

    if learner_input.get("available_days") is None:
        missing_fields.append("learner_input.available_days")
        clarification_questions.append(
            "请提供计划学习的天数。"
        )

    # 检查目标任务信息
    if len(title) < 2:
        missing_fields.append("target_input.title")
        clarification_questions.append(
            "请提供任务标题（至少两个字符）。"
        )

    if len(description) < 5:
        missing_fields.append("target_input.description")
        clarification_questions.append(
            "请提供更详细的任务描述（至少五个字符）。"
        )

    if not task_type:
        missing_fields.append("target_input.task_type")
        clarification_questions.append(
            "请选择目标任务类型。"
        )

    if len(expected_outcome) < 5:
        missing_fields.append("target_input.expected_outcome")
        clarification_questions.append(
            "请明确预期结果（至少五个字符）。"
        )

    # 信息不足：不构造严格模型，交给条件路由处理
    if missing_fields:
        return {
            "missing_fields": missing_fields,
            "clarification_questions": clarification_questions,
        }

    # 信息完整：转换成后续业务节点需要的严格模型
    return {
        "missing_fields": [],
        "clarification_questions": [],
        "learner_profile": LearnerProfile.model_validate(
            learner_input
        ),
        "target_task": TargetTask.model_validate(
            target_input
        ),
    }


# ---------------- 节点 2：请求用户补充具体信息（纯规则，无 LLM） ----------------

def request_clarification(state: AgentState) -> dict:
    """返回具体澄清问题，不调用 LLM。"""
    missing_fields = list(state.get("missing_fields") or [])
    questions = list(state.get("clarification_questions") or [])

    # 输入检查已经产生问题时，直接保留。
    # 没有输入问题却进入本节点，说明仓库证据不足。
    if not missing_fields:
        missing_fields.append("repo_evidence")
        questions.append(
            "当前仓库证据不足，请提供更具体的目标文件、"
            "模块名称或 Issue 信息。"
        )

    return {
        "missing_fields": missing_fields,
        "clarification_questions": questions,
    }


# ---------------- 节点 3：分析学习者（纯规则，无 LLM） ----------------

def analyze_learner(state: AgentState) -> dict:
    """读取 learner_profile，产出能力总结与技能差距。"""
    # 从共享 State 读取学习者画像（Pydantic 模型）
    profile = state["learner_profile"]

    # 已掌握技能转成新 list（避免直接引用模型内部列表）
    known = list(profile.known_skills)
    # 不熟悉技能视为技能差距（简单规则：unfamiliar == gap）
    unknown = list(profile.unfamiliar_skills or [])

    # 节点只返回"局部更新"：LangGraph 会把返回值 merge 进全局 State
    return {
        "learner_analysis": {           # 输出到 State 的新字段
            "current_level": profile.current_level,   # 当前水平
            "known_skills": known,                    # 已掌握
            "skill_gaps": unknown,                    # 差距
            "daily_capacity_hours": (                 # 总可用小时
                profile.daily_hours * profile.available_days
            ),
        }
    }

# ---------------- 节点 4：分析目标（纯规则，复用现有工具） ----------------

def analyze_target(state: AgentState) -> dict:
    """读取 target_task，提炼用于文件匹配的关键词。"""
    target = state["target_task"]

    # 复用 V0.4：把中文目标词映射为文件路径关键词（如"签名"-> sign）
    keywords = extract_target_keywords(target)

    return {
        "target_analysis": {
            "keywords": sorted(keywords),   # 排序保证输出稳定可测
            "task_type": target.task_type,  # 任务类型（understand_module 等）
        }
    }


# ---------------- 节点 5：收集证据（复用 V0.4 证据层） ----------------

def collect_evidence(state: AgentState) -> dict:
    """根据目标收集仓库证据，并顺带取回 README 与目录树。"""
    path = state["repository_path"]   # 目标仓库路径（调用方提供）
    target = state["target_task"]     # 目标任务

    # 3.1 读取 onboarding 文档，只取 README 的正文
    readme = ""
    onboarding = read_repository_onboarding_docs(path)
    for doc in onboarding.documents:
        if doc.document_type == "readme":
            readme = doc.content

    # 3.2 生成受限目录树文本（深度/文件数上限，防大仓库失控）
    tree_result = build_tree(path, max_depth=4, max_files=200)

    # 3.3 目标相关文件排序 -> 展平为证据列表
    ranked = rank_target_files(path, target, top_n=8)

    evidence_candidates = [
        item.file_path
        for item in ranked
    ]
    evidence: list[RepositoryEvidence] = []
    for item in ranked:
        # 每个候选文件自带 evidence（README 引用等），展平收集
        evidence.extend(item.evidence)

    return {
        "repo_evidence": evidence,
        "repo_readme": readme,
        "repo_tree": tree_result.tree,
        "evidence_candidates": evidence_candidates,
    }


# ---------------- 节点 6：补读一个候选文件（有限循环） ----------------

def read_more_evidence(state: AgentState) -> dict:
    """补读一个尚未尝试的候选文件，并安全更新证据预算。"""
    candidates = list(
        state.get("evidence_candidates") or []
    )
    attempted_files = list(
        state.get("read_evidence_files") or []
    )

    # 从 candidates 中选择第一个不在 attempted_files 中的路径。
    # 找不到时 next_candidate 应为 None。
    next_candidate = next(
        (
            path
            for path in candidates
            if path not in attempted_files
        ),
        None,
    )

    if next_candidate is None:
        return {
            "evidence_stop_reason": (
                "没有尚未读取的候选文件，"
                "当前证据仍不足。"
            ),
        }

    # 只要真正发起读取尝试，step_count 就增加，
    # 即使本次文件读取失败。
    next_step_count = state["step_count"] + 1
    updated_attempted_files = [
        *attempted_files,
        next_candidate,
    ]

    result = read_repo_file.invoke({
        "repository_path": state["repository_path"],
        "relative_path": next_candidate,
    })

    common_update = {
        "step_count": next_step_count,
        "read_evidence_files": updated_attempted_files,
    }

    # 文件读取失败：记录错误，但不消耗成功读取预算。
    if not result.get("ok"):
        return {
            **common_update,
            "errors": [
                (
                    f"补读 {next_candidate} 失败："
                    f"{result.get('message', '未知错误')}"
                )
            ],
        }

    content = str(result.get("content") or "")

    # 必须复制预算，不能直接修改 State 中的旧对象。
    updated_budget = replace(
        state["evidence_budget"]
    )

    # 先判断本次内容是否还能进入 State。
    if not updated_budget.can_consume(
        file_count=1,
        char_count=len(content),
    ):
        # consume 会设置 stopped 和具体 stop_reason。
        updated_budget.consume(
            file_count=1,
            char_count=len(content),
        )

        return {
            **common_update,
            "evidence_budget": updated_budget,
            "evidence_stop_reason": (
                updated_budget.stop_reason
                or "证据读取预算不足。"
            ),
        }

    updated_budget.consume(
        file_count=1,
        char_count=len(content),
    )

    # 空文件消耗一次文件预算，但不能形成有效证据。
    if not content:
        return {
            **common_update,
            "evidence_budget": updated_budget,
            "evidence_stop_reason": updated_budget.stop_reason,
            "errors": [
                f"补读 {next_candidate} 成功，但文件内容为空。"
            ],
        }

    evidence = RepositoryEvidence(
        source_path=result["source_path"],
        snippet=content,
        reason="有限循环补读的目标相关候选文件。",
        confidence=1.0,
    )

    # repo_evidence 有 operator.add reducer，
    # 因此这里只返回本轮新增的一条证据。
    return {
        **common_update,
        "evidence_budget": updated_budget,
        "repo_evidence": [evidence],
        "evidence_stop_reason": updated_budget.stop_reason,
    }


# ---------------- 节点 7：证据不足时保守停止（纯规则） ----------------

def conservative_evidence_stop(
    state: AgentState,
) -> dict:
    """说明停止原因，并请求更具体的仓库定位信息。"""
    reason = state.get("evidence_stop_reason")
    budget = state.get("evidence_budget")

    # 如果 reason 为空、budget 存在且 budget.stop_reason 非空，
    # 使用预算对象中的停止原因。
    if not reason and budget is not None and budget.stop_reason:
        reason = budget.stop_reason

    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 2)

    # 如果 reason 仍为空，并且 step_count >= max_steps，
    # 设置为：
    # f"已达到最多 {max_steps} 次证据补读上限。"
    if not reason and step_count >= max_steps:
        reason = f"已达到最多 {max_steps} 次证据补读上限。"

    # 如果 reason 仍为空，说明不是次数或预算问题，
    # 设置为：
    # "没有尚未读取的候选文件。"
    if not reason:
        reason = "没有尚未读取的候选文件。"

    question = (
        f"证据补充已停止：{reason}"
        "当前仍缺少能够证明目标实现位置的源码内容，"
        "请提供更具体的目标文件、模块名称或 Issue 信息。"
    )

    return {
        "evidence_stop_reason": reason,
        "missing_fields": ["repo_evidence"],
        "clarification_questions": [question],
    }

# ---------------- 节点 8：生成路线（唯一调 LLM 的节点） ----------------

def generate_roadmap(state: AgentState) -> dict:
    """调用现有路线生成器，产出 LearningRoadmap。"""
    # Pydantic 模型 -> dict：生成器接口要求 dict 参数
    user_profile = state["learner_profile"].model_dump(mode="json")
    target_task = state["target_task"].model_dump(mode="json")

    # 内部会创建 LLM、做结构化输出，并校验 LearningRoadmap
    roadmap = generate_structured_roadmap(
        user_profile=user_profile,
        target_task=target_task,
        repository_readme=state["repo_readme"],
        repository_tree=state["repo_tree"],
    )
    return {"roadmap": roadmap}
