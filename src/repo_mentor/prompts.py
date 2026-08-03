"""RepoMentor学习路线Prompt。"""

from langchain_core.prompts import ChatPromptTemplate


SYSTEM_PROMPT = """
你是RepoMentor，一个面向开源初学者的仓库学习与贡献准备助手。

你的职责不是全面总结仓库，也不是回答任意仓库问题，
而是根据学习者基础、目标任务和真实仓库信息，
生成可以执行、可以验证的学习路线。

不得编造仓库中不存在的文件。
信息不足时必须明确说明，不得猜测。
""".strip()


PROMPT_V1 = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """
请根据以下用户资料和仓库信息，生成一份7天学习路线。

用户资料：
{user_profile}

目标任务：
{target_task}

仓库README：
{repository_readme}

仓库目录：
{repository_tree}
""".strip(),
        ),
    ]
)


PROMPT_V2 = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """
请根据以下信息，为用户生成个性化仓库学习路线。

用户资料：
{user_profile}

目标任务：
{target_task}

仓库README：
{repository_readme}

仓库目录：
{repository_tree}

必须遵守以下要求：

1. 只能推荐仓库目录中真实存在的文件；
2. 先分析用户已经具备的能力和缺少的能力；
3. 学习任务必须围绕目标任务；
4. 每天至少包含一个阅读任务和一个实践任务；
5. 每项任务都要给出明确完成标准；
6. 不确定的信息必须标记为“需要进一步确认”；
7. 不要输出与目标任务无关的通用知识清单。
""".strip(),
        ),
    ]
)


PROMPT_V3 = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """
请为该用户生成一份“有仓库证据支持”的个性化学习路线。

【学习者画像】
{user_profile}

【目标任务】
{target_task}

【仓库README】
{repository_readme}

【仓库目录】
{repository_tree}

请按照以下顺序输出：

## 1. 学习者分析

说明用户已经掌握什么，以及完成目标仍然缺少什么。

## 2. 目标任务分析

说明目标任务可能涉及哪些模块。
所有判断必须来自README或目录结构。

## 3. 学习路线

每天必须包含：

- 当天学习目标；
- 推荐阅读的真实文件；
- 推荐该文件的依据；
- 阅读时重点关注的内容；
- 一个代码定位任务；
- 一个小型实践任务；
- 可验证的完成标准；
- 预计学习时间。

## 4. 风险与不确定信息

列出当前仓库资料无法确认的内容。

重要限制：

- 不得编造文件；
- 不得把通用仓库问答作为主要输出；
- 不得直接替用户修改代码；
- 路线必须围绕目标任务；
- 没有证据时必须明确表示无法判断。
""".strip(),
        ),
    ]
)


ROADMAP_PROMPTS = {
    "v1_baseline": PROMPT_V1,
    "v2_constrained": PROMPT_V2,
    "v3_evidence_based": PROMPT_V3,
}