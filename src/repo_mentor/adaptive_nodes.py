"""RepoMentor V0.6/V0.7 自适应工作流的核心节点。

每个节点 = 函数(state) -> 局部更新 dict，LangGraph 负责 merge：

- inspect_request       ：检查原始输入并构造严格领域模型
- request_clarification ：生成具体的澄清问题（纯规则，无 LLM）
- analyze_learner       ：分析学习者画像（纯规则，无 LLM）
- analyze_target        ：分析目标任务关键词（纯规则）
- collect_evidence      ：收集目标相关证据（复用 V0.4 证据层）
- generate_roadmap      ：调用 LLM 生成学习路线
- confirm_roadmap       ：暂停图并等待用户确认路线
- generate_assessment   ：调用 LLM 生成证据约束的评估包
- collect_learner_answers：暂停图并等待学习者提交答案
- evaluate_answers      ：组合规则、模型和人工复核结果
- update_profile        ：根据实际评估证据更新掌握度画像
- reflect_on_mastery    ：根据掌握度和次数上限作出重规划决定
- apply_mastery_replan  ：把补练或复习决定转换为可追溯任务

节点间接力：
generate_roadmap 产出路线
→ confirm_roadmap 等待人工批准或修改
"""

from __future__ import annotations
from langgraph.types import Overwrite, interrupt
from repo_mentor.repository_safeguards import EvidenceBudget
from dataclasses import replace
from repo_mentor.repository_tools import read_repo_file
from repo_mentor.models import (
    LearnerProfile,
    RepositoryEvidence,
    TargetTask,
    RoadmapConfirmation,
    AssessmentPackage,
    EvaluationResult,
    LearningTask,
    MasteryProfile,
    ReplanDecision,
    AssessmentSubmission,
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
from repo_mentor.assessment_generator import (
    generate_structured_assessment,
)
from repo_mentor.assessment_evaluator import (
    evaluate_code_location_answer,
    evaluate_concept_answer,
    mark_practice_for_human_review,
)
from repo_mentor.mastery_updater import (
    build_mastery_profile,
)
from repo_mentor.mastery_replanner import (
    build_supplemental_task,
    decide_replan,
)

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

# ---------------- 节点 9：等待用户确认路线（HITL） ----------------

def confirm_roadmap(
    state: AgentState,
) -> dict:
    """暂停工作流，等待用户批准路线或提交修改。"""
    roadmap = state.get("roadmap")

    if roadmap is None:
        raise ValueError(
            "确认路线前必须先生成 roadmap"
        )

    # interrupt 的数据必须可以被 JSON 序列化。
    payload = {
        "kind": "roadmap_confirmation",
        "question": "是否批准当前路线，或修改目标/难度后重新生成？",
        "target": state["target_task"].model_dump(
            mode="json"
        ),
        "learner": {
            "current_level": (
                state["learner_profile"].current_level
            ),
            "daily_hours": (
                state["learner_profile"].daily_hours
            ),
            "available_days": (
                state["learner_profile"].available_days
            ),
        },
        "roadmap": roadmap.model_dump(mode="json"),
        "allowed_actions": [
            "approve",
            "revise",
        ],
        "revision_count": state.get(
            "revision_count",
            0,
        ),
    }

    # 第一次执行在这里暂停；
    # 使用 Command(resume=...) 后，返回人工输入。
    raw_decision = interrupt(payload)

    # 人工输入也是外部输入，必须经过严格模型校验。
    confirmation = RoadmapConfirmation.model_validate(
        raw_decision
    )

    if confirmation.action == "approve":
        status = "approved"
    else:
        status = "revision_requested"

    return {
        "human_confirmation": confirmation,
        "confirmation_status": status,
    }


# ---------------- 节点 10：应用人工修改并重置派生状态 ----------------

def apply_human_revision(
    state: AgentState,
) -> dict:
    """合并人工修改、重建领域模型并清理旧路线状态。"""
    raw_confirmation = state.get(
        "human_confirmation"
    )

    if raw_confirmation is None:
        raise ValueError(
            "应用人工修改前必须存在 human_confirmation"
        )

    # Checkpointer 恢复后可能得到模型或可校验字典，
    # 因此在节点边界再次进行严格校验。
    confirmation = RoadmapConfirmation.model_validate(
        raw_confirmation
    )

    if confirmation.action != "revise":
        raise ValueError(
            "只有 revise 决定可以进入人工修改节点"
        )

    # 从已校验模型构造回退输入，确保缺少原始 dict 时也能工作。
    learner_input = dict(
        state.get("learner_input")
        or state["learner_profile"].model_dump(
            mode="json"
        )
    )
    target_input = dict(
        state.get("target_input")
        or state["target_task"].model_dump(
            mode="json"
        )
    )

    # 人工更新覆盖原字段，未修改字段继续保留。
    learner_input.update(
        confirmation.learner_updates
    )
    target_input.update(
        confirmation.target_updates
    )

    # 合并后的外部输入必须重新经过完整领域模型校验。
    learner_profile = LearnerProfile.model_validate(
        learner_input
    )
    target_task = TargetTask.model_validate(
        target_input
    )

    # 新目标获得新的读取预算，但保留原来的限制配置。
    current_budget = state.get("evidence_budget")

    if current_budget is None:
        new_budget = EvidenceBudget(
            max_files=2,
        )
    else:
        new_budget = EvidenceBudget(
            max_files=current_budget.max_files,
            max_chars=current_budget.max_chars,
        )

    return {
        # 新的输入基线
        "learner_input": learner_input,
        "target_input": target_input,
        "learner_profile": learner_profile,
        "target_task": target_task,

        # 旧输入产生的分析结果失效
        "learner_analysis": {},
        "target_analysis": {},

        # repo_evidence 有 operator.add reducer，
        # 必须用 Overwrite 才能真正替换为空列表。
        "repo_evidence": Overwrite([]),

        # 重置证据补读循环
        "step_count": 0,
        "evidence_budget": new_budget,
        "evidence_candidates": [],
        "read_evidence_files": [],
        "evidence_stop_reason": None,

        # 旧路线和旧确认结果失效
        "roadmap": None,
        # 旧目标/难度产生的评估结果全部失效
        "assessment": None,
        "learner_answers": {},
        "evaluation_results": [],
        "mastery": None,
        "confirmation_status": "not_requested",
        "human_confirmation": None,
        "revision_count": (
            state.get("revision_count", 0) + 1
        ),

        # 清理旧一轮产生的问题和错误；
        # checkpoint 历史仍然保留这些旧信息。
        "missing_fields": [],
        "clarification_questions": [],
        "errors": Overwrite([]),
    }

# ---------------- 节点 11：生成证据约束的评估包 ----------------

def generate_assessment(
    state: AgentState,
) -> dict:
    """根据已批准路线的首个任务生成结构化评估。"""
    roadmap = state.get("roadmap")

    if roadmap is None:
        raise ValueError(
            "生成评估前必须先存在 LearningRoadmap"
        )

    # V0.7 当前先评估路线中的第一个任务。
    # 后续增加 current_task_id 后再改为按进度选择。
    learning_task = next(
        (
            task
            for daily_plan in roadmap.daily_plans
            for task in daily_plan.tasks
        ),
        None,
    )

    if learning_task is None:
        raise ValueError(
            "当前 LearningRoadmap 中没有可评估任务"
        )

    assessment = generate_structured_assessment(
        learner_profile=state["learner_profile"],
        learning_task=learning_task,
        repo_evidence=state.get(
            "repo_evidence",
            [],
        ),
    )

    return {
        "assessment": assessment,
    }

# ---------------- 节点 12：暂停并收集学习者答案 ----------------

def collect_learner_answers(
    state: AgentState,
) -> dict:
    """展示结构化评估，并等待学习者提交答案。"""
    # 1：读取 assessment，并检查是否存在。
    raw_assessment = state.get("assessment")
    if raw_assessment is None:
        raise ValueError("收集答案前必须存在 AssessmentPackage")

    # 2：恢复 checkpoint 中可能保存为 dict 的模型。
    assessment = AssessmentPackage.model_validate(
        raw_assessment
    )

    # 3：保持两道问题在前、实践任务在后的顺序。

    expected_item_ids = [
        question.question_id
        for question in assessment.questions
    ]
    expected_item_ids.append(
        assessment.practice_task.practice_id
    )

    # 答案 4：暂停工作流，并把测验展示给调用方。
    raw_submission = interrupt({
        "kind": "assessment_submission",
        "question": "请完成当前测验并提交答案。",
        "assessment": assessment.model_dump(
            mode="json"
        ),
        "expected_item_ids": expected_item_ids,
    })

    # 答案 5：恢复后校验提交数据的结构。
    submission = AssessmentSubmission.model_validate(
        raw_submission
    )

    # 答案 6：只把答案字典写入共享 State。
    return {
        "learner_answers": dict(
            submission.answers
        ),
    }

# ---------------- 节点 13：组合评估学习者答案 ----------------

def evaluate_answers(
    state: AgentState,
) -> dict:
    """根据项目类型选择规则、模型或人工复核。"""
    raw_assessment = state.get("assessment")

    if raw_assessment is None:
        raise ValueError(
            "评估答案前必须先存在 AssessmentPackage"
        )

    # Checkpoint 恢复后可能得到模型或可校验字典，
    # 节点边界统一恢复成严格模型。
    assessment = AssessmentPackage.model_validate(
        raw_assessment
    )
    learner_answers = state.get(
        "learner_answers",
        {},
    )

    expected_ids = {
        question.question_id
        for question in assessment.questions
    }
    expected_ids.add(
        assessment.practice_task.practice_id
    )

    unknown_ids = (
        set(learner_answers)
        - expected_ids
    )

    if unknown_ids:
        raise ValueError(
            "学习者答案包含未知评估项目："
            + "、".join(sorted(unknown_ids))
        )

    results = []

    for question in assessment.questions:
        answer = learner_answers.get(
            question.question_id,
            "",
        )

        if not isinstance(answer, str):
            raise ValueError(
                "学习者答案必须是字符串："
                f"{question.question_id}"
            )

        if question.question_type == "concept":
            result = evaluate_concept_answer(
                question,
                answer,
            )
        else:
            result = evaluate_code_location_answer(
                question,
                answer,
            )

        results.append(result)

    practice = assessment.practice_task
    submission = learner_answers.get(
        practice.practice_id,
        "",
    )

    if not isinstance(submission, str):
        raise ValueError(
            "实践任务提交说明必须是字符串："
            f"{practice.practice_id}"
        )

    results.append(
        mark_practice_for_human_review(
            practice,
            submission,
        )
    )

    return {
        "evaluation_results": results,
    }


# ---------------- 节点 14：更新证据驱动的掌握度画像 ----------------

def update_profile(
    state: AgentState,
) -> dict:
    """根据可靠评估结果构建 MasteryProfile。"""
    raw_results = state.get(
        "evaluation_results",
        [],
    )

    if not raw_results:
        raise ValueError(
            "更新学习者画像前必须存在评估结果"
        )

    target_task = state.get("target_task")

    if target_task is None:
        raise ValueError(
            "更新学习者画像前必须存在 TargetTask"
        )

    # Checkpoint 恢复或外部调用后，列表元素可能是 dict。
    # 在节点边界重新恢复成严格模型。
    evaluation_results = [
        EvaluationResult.model_validate(result)
        for result in raw_results
    ]

    mastery = build_mastery_profile(
        target_task=target_task,
        evaluation_results=evaluation_results,
        profile_id=(
            "mastery-revision-"
            f"{state.get('revision_count', 0)}"
        ),
    )

    return {
        "mastery": mastery,
    }


# ---------------- 节点 15：反思掌握度并决定下一步 ----------------

def reflect_on_mastery(
    state: AgentState,
) -> dict:
    """根据掌握度分段和次数上限生成重规划决定。"""
    raw_mastery = state.get("mastery")

    if raw_mastery is None:
        raise ValueError(
            "反思掌握度前必须存在 MasteryProfile"
        )

    # Checkpoint 恢复后可能是 dict，
    # 在节点边界恢复为严格模型。
    mastery = MasteryProfile.model_validate(
        raw_mastery
    )
    replan_count = state.get("replan_count", 0)
    max_replans = state.get("max_replans", 1)

    decision = decide_replan(
        mastery,
        replan_count=replan_count,
        max_replans=max_replans,
    )

    return {
        "replan_decision": decision,
    }


# ---------------- 节点 16：应用有界的自适应重规划 ----------------

def apply_mastery_replan(
    state: AgentState,
) -> dict:
    """为补练或复习决定追加一项可追溯任务。"""
    raw_mastery = state.get("mastery")
    raw_decision = state.get("replan_decision")

    if raw_mastery is None:
        raise ValueError(
            "应用重规划前必须存在 MasteryProfile"
        )

    if raw_decision is None:
        raise ValueError(
            "应用重规划前必须存在 ReplanDecision"
        )

    mastery = MasteryProfile.model_validate(
        raw_mastery
    )
    decision = ReplanDecision.model_validate(
        raw_decision
    )

    if decision.action not in {
        "add_practice",
        "add_review",
    }:
        raise ValueError(
            "apply_mastery_replan 只能处理"
            " add_practice 或 add_review"
        )

    current_count = state.get("replan_count", 0)
    max_replans = state.get("max_replans", 1)

    if current_count >= max_replans:
        raise ValueError(
            "已达到重规划次数上限，不能再追加任务"
        )

    task = build_supplemental_task(
        mastery,
        decision,
    )
    existing_tasks = [
        LearningTask.model_validate(item)
        for item in state.get("supplemental_tasks", [])
    ]

    return {
        "supplemental_tasks": [
            *existing_tasks,
            task,
        ],
        "replan_count": current_count + 1,
    }
