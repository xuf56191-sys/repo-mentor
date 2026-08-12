# RepoMentor

RepoMentor 是一个面向开源贡献新人的自适应仓库学习与贡献准备 Agent。

它根据用户当前的技术基础、可用学习时间和目标任务或目标 Issue，
分析代码仓库中的 README、CONTRIBUTING、目录结构和相关源码，
生成有真实仓库证据支持的个性化学习路线。

RepoMentor 不仅告诉用户应该阅读哪些文件，还会为每个学习阶段生成：

- 文件阅读任务；
- 代码定位任务；
- 小型实践任务；
- 可验证的完成标准；
- 基于仓库内容的测验。

系统会根据用户的完成情况和测验结果识别薄弱知识点，
动态调整后续学习计划，并评估用户是否已经具备尝试第一个开源贡献任务的能力。

## 项目背景

初学者第一次接触一个开源项目时，通常会遇到以下问题：

- 不知道当前目标任务与哪些文件和模块有关；
- 不知道应该先学习哪些前置知识；
- 面对大量目录和源码，不知道合理的阅读顺序；
- 普通仓库分析报告很难转化为可以执行的学习任务；
- 学习过程缺少代码定位题和实践任务；
- 阅读一段时间后，无法判断自己是否真正掌握；
- 不知道自己是否已经具备尝试某个 Issue 的能力。

RepoMentor 希望解决的不是单纯的“看懂仓库”，而是：

> 以用户当前的基础，为了完成一个具体的开源任务，
> 下一步应该学习什么、阅读什么、实践什么，
> 以及如何判断自己已经具备开始贡献的能力。

## 项目定位

RepoMentor 不以通用仓库问答、完整架构分析或全仓代码扫描作为核心目标。

仓库结构分析、代码检索和问答能力在本项目中主要作为证据层，
用于支持以下核心功能：

1. 生成有依据的个性化学习路线；
2. 解释为什么推荐某个文件；
3. 根据真实源码生成测验和实践任务；
4. 评估用户对当前模块的掌握情况；
5. 根据薄弱点重新规划学习任务；
6. 分析完成目标 Issue 所需的能力差距；
7. 评估用户的开源贡献准备度。

RepoMentor 的核心工作流程是：

```text
学习者画像
→ 目标任务或目标 Issue
→ 仓库证据收集
→ 个性化学习路线
→ 阅读与实践任务
→ 掌握度评估
→ 自适应重新规划
→ 贡献准备度评估
```

## openEuler 实践场景

RepoMentor 后续将结合 openEuler 开源实习进行真实场景验证。

计划选择本人在实习中实际接触的小型仓库或具体 Issue，
将 RepoMentor 生成的学习路线与真实入门过程进行对照，包括：

- 推荐文件是否与实际任务相关；
- 学习顺序是否合理；
- 是否遗漏重要的贡献指南或社区规范；
- 实践任务是否有助于理解目标代码；
- 测验结果能否反映真实掌握情况；
- 使用 RepoMentor 后是否减少了仓库入门成本。

第一阶段不会直接分析完整的 openEuler 内核仓库，
而是优先从实际实习涉及的小仓库、文档任务或明确的 Issue 开始。

## 当前版本

当前版本为 **V0.4 开发阶段**

## 当前已实现

RepoMentor 当前已经完成 V0.2 个性化路线原型，
并正在实现 V0.4 真实仓库证据层。

目前支持：

- 根据学习者基础、目标任务和学习时间生成结构化学习路线；
- 使用 Pydantic Schema 约束路线输出结构；
- 将学习路线保存为 JSON 和 Markdown；
- 使用多类学习者和目标任务进行差异化验证；
- 接收并校验真实本地仓库路径；
- 安全生成真实仓库目录树；
- 忽略 `.git`、`.idea`、虚拟环境、缓存、`.env` 和生成结果目录；
- 限制仓库扫描深度和文件数量；
- 安全读取 README、CONTRIBUTING、项目配置和 docs 入口资料；
- 为读取到的仓库资料保存真实来源路径；
- 根据用户目标任务对真实仓库文件进行初步相关性排序；
- 使用目标关键词、README 引用和文件角色建立可解释评分规则；
- 输出带有分数、理由和 `RepositoryEvidence` 的 Top-N 候选文件；
- 区分“真实路径已经确认”和“源码内容仍待确认”；
- 开始使用 pytest 为仓库证据层增加自动化测试。
- 将真实仓库证据能力封装为 LangChain Tools；
- 提供 `get_repo_tree` 获取受限目录树；
- 提供 `get_onboarding_docs` 读取仓库入门和贡献资料；
- 提供 `read_repo_file` 受控读取单个真实仓库文件；
- 提供 `rank_target_files` 根据目标排序真实候选文件；
- 每个 Tool 使用明确的输入 Schema、docstring 和结构化返回值；
- Tool 执行错误能够返回可读的结构化错误；
- `read_repo_file` 拒绝读取 `.env` 等被忽略或敏感路径；
- 开始使用 pytest 验证 Repository Tools 的独立调用行为。



## Target-Driven Evidence Collection

RepoMentor 的目标不是尽可能读取更多仓库文件，
而是根据用户当前目标选择必要证据。

例如，当目标是：

> 理解 RepoMentor 的目录树扫描流程

模型实际可以形成如下证据收集过程：

```text
目标
↓
get_repo_tree
确认真实仓库结构
↓
rank_target_files
确定与目标最相关的文件
↓
read_repo_file
读取 repository_tree.py
↓
read_repo_file
读取 repository_service.py
↓
根据真实源码总结目录树扫描流程
```

当前正在完成：
- 让模型根据具体目标自主选择 Repository Tools；
- 记录模型产生的 tool calls、参数和调用次数；
- 将 Tool 结果通过 ToolMessage 返回模型；
- 限制模型无目的地读取大量无关仓库文件。

当前还没有完成：

- 自动读取真实本地仓库；
- LangGraph 工作流；
- 代码库 RAG 问答；
- 测验和学习进度保存；
- Streamlit 页面。

## Repository Tool Safeguards

RepoMentor 在目标驱动 Tool Calling 外增加了一层确定性的工具执行保护机制。

当前 Repository Tool 执行流程为：

```text
AIMessage.tool_calls
↓
检查 Tool 是否存在
↓
检查证据读取预算
↓
对日志参数进行敏感字段脱敏
↓
执行 Tool 并记录耗时
↓
暂时性失败最多重试一次
↓
生成安全的结果摘要
↓
统计文件数和文本字符预算
↓
ToolMessage
↓
返回模型继续推理
```

当前保护能力包括：

* 对 Tool 调用记录执行名称、耗时、尝试次数和结果摘要；
* 不在日志中输出完整源码内容；
* 对 `api_key`、`token`、`password`、`secret`、`authorization` 等敏感字段进行递归脱敏；
* 使用 `EvidenceBudget` 限制进入模型上下文的文件数量；
* 使用 `EvidenceBudget` 限制进入模型上下文的文本字符总量；
* 暂时性的 `TimeoutError`、`ConnectionError`、部分 `OSError` 最多额外重试一次；
* 参数错误、非法路径和安全限制等确定性错误不会进行无意义重试；
* Tool 最终失败后返回结构化错误，而不是直接终止整个 Agent；
* 当证据预算耗尽后，后续读取请求会得到 `BudgetExceeded`，模型根据已经获取的真实证据完成总结。

### Evidence Budget

当前证据预算限制的是提供给模型的仓库文本证据，而不是磁盘读取字节数。

例如：

```text
max_files = 4
max_chars = 30000
```

表示一次目标驱动分析最多允许有限数量的真实文件正文和文本字符进入模型上下文。

文件数量和字符数量同时受到限制：

* 文件数预算防止模型无目的地读取大量小文件；
* 字符预算防止模型读取少量但体积巨大的文件。

预算由确定性 Python 代码维护，而不是依赖 Prompt 要求模型自行遵守。

## Testing

项目使用 `pytest` 对仓库证据层进行自动化测试。

当前测试覆盖：

* 目标相关文件排序及真实路径验证；
* README 真实引用证据；
* Repository Tools 独立调用；
* Tool 参数 Schema 和敏感文件读取限制；
* Tool 注册表和 `ToolMessage` 调用 ID 对应关系；
* 敏感字段日志脱敏；
* 文件读取预算限制；
* 字符读取预算限制；
* 暂时性错误最多重试一次；
* 确定性错误不进行无意义重试；
* 日志中不暴露 API Key。

运行全部测试：

```bash
python -m pytest -v
```

## Current Limitations

当前安全执行层仍属于 V0.4 阶段的第一版实现：

* 当前记录 Tool 实际耗时，但尚未实现真正的强制执行超时；
* 当前字符预算限制的是 Tool 结果进入模型上下文的文本量，文件可能已经先被读取到 Python 内存；
* 重试策略目前较简单，尚未使用指数退避等机制；
* Tool Calling 仍使用手写有限循环，尚未迁移到 LangGraph；
* 当前主要保护结构化敏感字段，不进行复杂的自由文本密钥模式扫描；
* Tool description 和预算参数仍需要通过更多真实仓库实验继续调整。

RepoMentor 当前仍坚持：

**模型负责决策，确定性代码负责执行、验证和安全边界。**


## 目标相关仓库证据

RepoMentor 不把“仓库中最重要的文件”
直接等同于“用户当前最应该学习的文件”。

例如，同一个仓库中：

- 当目标是理解目录树扫描流程时，
  `repository_tree.py`、`repository_service.py`
  应该获得更高优先级；

- 当目标是理解结构化学习路线生成流程时，
  `roadmap_generator.py`、`models.py`、`prompts.py`
  应该获得更高优先级。

当前 V0.4 使用可解释的规则排序器，
综合考虑：

- 目标任务关键词；
- 文件路径名称；
- README 中的真实文件引用；
- 入口文件；
- 配置文件；
- 测试文件；
- 仓库入门与贡献资料。

候选文件必须来自真实文件系统，
而不是由模型生成文件路径。

对于尚未真正读取源码内容的文件，
RepoMentor 会将其标记为：

`needs_confirmation`

避免根据文件名直接推断文件内部实现。

## 当前限制

当前项目仍处于 V0.4 仓库证据层开发阶段。

主要限制包括：

- 目标相关文件排序仍主要依赖规则和路径关键词；
- 普通源码只有在目标驱动 Tool Calling 明确选择后才会读取；
- 当前 Tool Calling 使用手写有限循环，
  尚未迁移到 LangGraph；
- 当前只限制 Tool Calling 轮数，
  尚未加入完整的文件读取预算和 Token / 字符预算；
- 尚未实现完善的 Tool 失败重试和调用耗时统计；
- Tool description 和系统提示词仍需要通过更多目标实验继续优化；
- 当前模型可能选择“合理但非必要”的额外 Tool，
  因此后续需要进一步优化工具选择效率；
- 当前不进行全仓库源码批量读取；
- 当前不自动修改代码、不自动创建 PR。

## 当前演示效果

目前可以调用 DeepSeek 模型，并连续获得两次回复。

示例输出：

```text
==============================
第 1 次模型调用
==============================
AI Agent 是一种能够感知环境、自主决策并采取行动以达成特定目标的智能体。

==============================
第 2 次模型调用
==============================
AI Agent 是一种能够感知环境、自主决策并采取行动以完成特定目标的智能体。
```

当前测试说明：

## Tests

项目使用 `pytest` 验证仓库证据层和 Tool Calling 的核心行为。

当前测试覆盖：

- 不同目标产生不同的目标文件排序；
- `top_n` 限制候选文件数量；
- Repository Tools 可以独立 `.invoke()`；
- README、目录树、单文件读取和目标排序 Tool 能够正常执行；
- Tool 输入 Schema 能拒绝非法参数；
- 敏感文件读取能够被限制；
- Tool 注册表能够正确维护四个 Repository Tools；
- `execute_tool_call()` 能根据模型提供的工具名称和参数执行真实 Tool；
- Tool 执行结果能够转换为 `ToolMessage`；
- `ToolMessage.tool_call_id` 与原始 Tool Call ID 保持一致。

运行全部测试：

```bash
python -m pytest -v
```
运行 Tool Calling 测试：

```bash
python -m pytest tests/test_target_tool_calling.py -v
```


## 后续计划

项目将按照以下顺序逐步开发：

1. 调用大模型生成学习路线；
2. 使用 Pydantic生成结构化结果；
3. 自动读取本地代码仓库；
4. 增加仓库读取工具；
5. 使用 LangGraph管理工作流；
6. 增加代码库问答；
7. 增加测验和学习反馈；
8. 保存用户学习进度。

## 当前暂不实现

为了控制项目难度，当前版本暂时不实现：

- 多 Agent；
- 自动运行仓库代码；
- 自动修改代码；
- 自动提交 Pull Request；
- 大型代码仓库分析；
- 向量数据库；
- 复杂网页前端。

## 项目结构

```text
repo-mentor/
├── data/
│   ├── demo_repo/
│   └── evaluation/
├── docs/
│   ├── learning-log.md
│   ├── product-positioning.md
│   └── prompt-experiments.md
├── evaluation/
│   ├── roadmap_review.md
├── src/
│   └── repo_mentor/
│       ├── __init__.py
│       ├── config.py
│       └── evaluation.py
│       ├── llm_service.py
│       └── main.py
│       ├── models.py
│       └── model_demo.py
│       └── prompt_experiment.py
│       └── prompts.py
│       ├── repository_service.py
│       ├── repository_tree.py
│       ├── repository_reader.py
│       ├── repository_tools.py
│       ├── repository_ranker.py
│       ├── roadmap_generator.py
│       └── target_tool_calling.py
├── tests/
│   └── test_repository_ranker.py
│   └── test_target_tool_calling.py
│   └── test_repository_tools.py
├── pytest.ini
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

各个核心文件的作用：

- `main.py`：读取演示用户资料、README 和目录结构；
- `config.py`：读取并校验模型配置；
- `llm_service.py`：创建 DeepSeek 模型并完成模型调用；
- `user_profile.json`：保存演示用户的学习基础和目标；
- `tree.txt`：保存演示仓库目录结构；
- `.env.example`：提供环境变量配置模板；
- `learning-log.md`：记录项目开发过程和学习复盘。
- repository_service.py
    ↓
- 仓库路径是否合法？
- repository_tree.py
    ↓
- 仓库里有哪些文件？
- repository_reader.py
    ↓
- 仓库的重要入门资料实际写了什么？

## 环境配置

项目使用 `.env` 保存本地模型配置。

首先复制项目根目录中的：

```text
.env.example
```
并创建一个新的：
```text
.env
```
在`.env`文件中填写自己的大模型
```aiexclude
MODEL_PROVIDER：模型服务提供商；
MODEL_NAME：使用的模型名称；
MODEL_API_KEY：模型平台提供的 API Key；
MODEL_BASE_URL：自定义接口地址，没有时可以留空；
TEMPERATURE：模型生成随机性，当前建议设置为 0.2
```
## 运行方式

创建并激活 Python 虚拟环境后，安装依赖：

```bash
pip install -r requirements.txt
```

运行当前版本：

```bash
python -m src.repo_mentor.config
```

## Tests

项目开始使用 `pytest` 对仓库证据层进行自动化验证。

当前测试主要位于：

```text
tests/
└── test_repository_ranker.py

## 下一步任务

下一步将完成：

1. 设计 RepoMentor 的学习路线 Prompt；
2. 将用户资料、仓库 README 和目录树交给模型；
3. 生成第一版普通文本学习路线；
4. 比较不同 Prompt 的输出效果；
5. 检查模型是否推荐了不存在的文件。

## 项目状态

项目目前处于学习和持续开发阶段。

## Engineering Principles

RepoMentor 当前遵循以下原则：

1. **真实路径优先**

   推荐文件必须来自真实文件系统，
   不允许模型凭空生成仓库路径。

2. **证据和推断分离**

   文件存在、README 引用和源码内容属于不同等级的证据，
   未读取源码时不会声称已经理解文件内部实现。

3. **确定性操作不用 LLM**

   路径校验、文件存在判断、大小限制、
   敏感文件过滤和基础规则排序优先使用普通 Python 实现。

4. **目标相关性优先**

   RepoMentor 关注的是
   “为了当前学习或贡献目标最值得看的文件”，
   而不是简单返回仓库中通用的重要文件。

5. **逐步增加自动化测试**

   使用 pytest 保存核心行为约束，
   避免项目增长后只能依赖手工运行验证。