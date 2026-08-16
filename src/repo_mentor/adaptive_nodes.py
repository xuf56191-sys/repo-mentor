"""V0.6 自适应工作流的四个核心节点。

每个节点 = 函数(state) -> 局部更新 dict，LangGraph 负责 merge：

- analyze_learner  ：分析学习者画像（纯规则，无 LLM）
- analyze_target   ：分析目标任务关键词（纯规则）
- collect_evidence ：收集目标相关证据（复用 V0.4 证据层）
- generate_roadmap ：调用 LLM 生成学习路线（唯一需要 LLM 的节点）

节点间接力：analyze_learner / analyze_target 的中间产物
→ collect_evidence 收集证据 → generate_roadmap 产出路线。
"""

from __future__ import annotations

from repo_mentor.models import RepositoryEvidence
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


# ---------------- 节点 1：分析学习者（纯规则，无 LLM） ----------------

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


# ---------------- 节点 2：分析目标（纯规则，复用现有工具） ----------------

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


# ---------------- 节点 3：收集证据（复用 V0.4 证据层） ----------------

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
    evidence: list[RepositoryEvidence] = []
    for item in ranked:
        # 每个候选文件自带 evidence（README 引用等），展平收集
        evidence.extend(item.evidence)

    return {
        "repo_evidence": evidence,          # 给 generate_roadmap 用
        "repo_readme": readme,              # 路线生成需要 README 文本
        "repo_tree": tree_result.tree,      # 路线生成需要目录树文本
    }


# ---------------- 节点 4：生成路线（唯一调 LLM 的节点） ----------------

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
