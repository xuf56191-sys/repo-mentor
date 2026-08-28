# RepoMentor学习记录

## 2026-07-29

### 今天完成

- 创建GitHub仓库；
- 将仓库克隆到本地；
- 创建Python虚拟环境；
- 创建项目基础目录；
- 准备用户信息、README和目录树测试数据；
- 编写并运行第一个Python程序。

### 今天理解的内容

- 本地项目和GitHub仓库的区别；
- Commit表示一次代码版本；
- Push表示把本地提交上传到GitHub；
- `.env`和`.venv`不应该上传到GitHub；
- 一个复杂项目应该先从最小输入输出开始。

### 遇到的问题

json文件如果为空，会报错。

### 下一步

调用大模型，根据固定测试数据生成第一份学习路线。

## 2026-07-30: 模型配置管理

### 今天的目标

为RepoMentor建立模型配置读取和校验功能。

### 今天完成

- 创建`.env`虚拟环境配置文件；
- 创建`.env.example`配置模板；
- 获取deep seek api并添加在配置文件中；
- 使用`python-dotenv`读取环境变量；
- 增加Temperature格式和范围检查；
- 验证真实API Key不会输出到终端；
- 编写并运行config.py文件获取配置文件内容。

### 今天理解的内容

- `.env`保存本地真实配置，不能上传GitHub；
- `.env.example`只保存字段模板，可以上传；
- API Key不能直接写在Python代码中；
- 配置读取和模型调用应该分开；
- 程序应该在启动阶段尽早发现配置错误。

### 测试结果

1. API Key为空：
   - 结果：
    `==================================================
    配置检查失败
    ==================================================
    缺少配置项 MODEL_API_KEY，请检查项目根目录下的 .env 文件。`

2. Temperature不是数字：
   - 结果：
   `==================================================
    配置检查失败
    ==================================================
    TEMPERATURE 必须是数字，当前内容为：'ab'`

3. 正常配置：
   - 结果：
   `==================================================
    配置检查成功
    ==================================================
    模型提供商：deepseek
    模型名称：deepseek-v4-flash
    自定义接口地址：https://api.deepseek.com
    Temperature：0.2
    API Key：已读取，但不会显示具体内容
`

### 遇到的问题

暂未发现具体问题。

### 下一步

创建模型服务，并完成RepoMentor的第一次真实模型调用。

## 2026-07-31: Deepseek大模型调用

### 今天的目标

创建模型服务，并完成RepoMentor的第一次真实模型调用。

### 今天完成

- 用命令：`pip install -U langchain-deepseek`安装langchain_deepseek
- 它的作用是连接 DeepSeek 和 LangChain 的桥梁
- 大模型调用文件；
- 完成模型的创建；
- 完成deepseek大模型的调用；
- 增加prompt为空时的提示；
- 验证真实API Key不会输出到终端；
- 编写并运行llm_service.py文件调用大模型。

### 今天理解的内容

- `from config import ConfigError , load_settings`这个引用命令建议改为相对导入，.config；
- 创建模型时，参数：`model_provider`不需要，需要删除config文件中的model_provider；
- invoke是调用的意思；


### 测试结果

1. prompt为空：
   - 结果：
    `==============================
     第1次模型调用
     ==============================
     模型调用失败：prompt不能为空
`

2. 两次调用：
   - 结果：
   `==============================
   第1次模型调用
   ==============================
   AI Agent 是一种能够感知环境、自主决策并采取行动以实现特定目标的智能体。
   ==============================
   第2次模型调用
   ==============================
   AI Agent 是一种能够感知环境、自主决策并采取行动以实现特定目标的智能体。`


### 遇到的问题

引用config时报错：模型调用失败：'Settings' object has no attribute 'model_provider'。

### 下一步

学习 Prompt 的角色、约束、输入变量和输出要求；理解为什么要避免模糊指令

## 2026-08-02：证据驱动Prompt实验

### 今天完成

- 新增目标任务输入；
- 编写三版学习路线Prompt；
- 使用相同输入运行三版Prompt；
- 比较个性化程度、目标相关性和文件真实性；
- 记录各版Prompt的优点与问题。

### 主要结论

三版中，V3证据驱动版综合表现最好

### 遇到的问题

未发现明显问题。

### 下一步

为学习路线建立Pydantic结构化数据模型。

## 2026-08-03：学习路线数据模型

### 今天完成

- 定义LearnerProfile；
- 定义TargetTask；
- 定义EvidenceSource；
- 定义LearningTask和DailyPlan；
- 定义LearningRoadmap；
- 验证合法嵌套数据；
- 验证错误时间；
- 验证未知字段；
- 导出本地示例JSON。

### 今天理解

- Prompt负责描述模型应该完成什么；
- Pydantic负责约束程序最终接受什么；
- 模型输出不能因为看起来合理就直接进入系统；
- 仓库推荐需要保存来源和可信度；
- 数据模型应该在接入大模型前先独立验证。

### 下一步

让DeepSeek按照LearningRoadmap模型返回结构化结果。

## 2026-08-04：结构化学习路线输出与导出

### 今天的目标

将证据驱动Prompt、DeepSeek模型和Pydantic学习路线模型连接，
生成可以被程序直接使用的结构化学习路线。

### 今天完成

- 从三版实验Prompt中整理正式Prompt；
- 使用`with_structured_output`绑定`LearningRoadmap`；
- 使用`include_raw=True`保留解析错误信息；
- 成功获得`LearningRoadmap`对象；
- 将学习路线保存为`roadmap.json`；
- 将学习路线渲染为`roadmap.md`；
- 重新读取JSON并通过Pydantic校验；
- 检查计划天数和每天预计时间；
- 人工检查文件幻觉和内容推断。

### 今天理解的内容

- Prompt负责约束模型应该生成什么内容；
- Pydantic负责约束程序最终接受什么数据；
- 结构正确不代表内容一定正确；
- Pydantic可以发现缺字段和类型错误，但不能自动判断源码事实；
- 仓库文件真实性和源码推断仍然需要额外校验；
- Markdown应该由程序根据结构化对象生成，而不是让模型同时负责格式和内容。

### 测试结果

1. 模型返回类型：
   - `LearningRoadmap` 
   - 结果：通过
2. JSON重新读取结果：
   - 成功重新创建`LearningRoadmap`
   - 结果：通过
3. Markdown显示结果：
   - 成功生成`outputs/roadmap.md`
   - 结果：通过
4. 是否出现不存在文件：
    -并未出现
5. 质量检查：
   - 成功发现7天全部超时；
   - 说明结构化输出正确不代表内容质量正确。
6. 是否超过每日时间限制：
   - 结果：未通过
   - 模型每天生成两个2小时任务，
     导致每天总时间为4小时，
     超过用户每天可用的2小时。


### 遇到的问题

**问题一**：**使用DeepSeek思考模式配合LangChain
`with_structured_output(method="function_calling")`
时，API返回400错误：

`Thinking mode does not support this tool_choice`

原因是function calling会通过tool_choice要求模型调用结构化输出工具，
而DeepSeek V4思考模式不接受该参数。

解决方法是在结构化输出调用中通过
`extra_body={"thinking": {"type": "disabled"}}`
关闭思考模式，继续使用function calling生成Pydantic对象。

**问题二：** `roadmap.model_dump(mode="json")`写成了`roadmap.model_dump(model="json")`

**问题三：**
Prompt虽然要求每天任务不能超过用户可用时间，
但没有明确说明`estimated_hours`表示一个LearningTask中
阅读、定位和实践活动的总时间。
模型将每天可用的2小时分配给了每一个LearningTask，
从而导致每天总时间变成4小时。

**解决方法：**

- 明确每天所有任务时间之和不得超过`daily_hours`；
- 明确`estimated_hours`表示完整任务总时间；
- V0.2阶段限制每天只生成一个LearningTask；
- 增加总时间、任务数量和day编号检查。
### 下一步

使用多组学习者画像和目标任务验证学习路线的差异，
并完成V0.2阶段评测。

## 2026-08-05：V0.2差异化验证

### 今天的目标

验证RepoMentor是否能够根据不同学习者画像和不同目标任务，
生成存在合理差异的学习路线。

### 今天完成

- 创建3类学习者画像；
- 创建2个不同目标任务；
- 批量生成6份结构化学习路线；
- 检查计划天数和每日时间；
- 检查不存在的文件路径；
- 检查无源码依据的实现推断；
- 比较不同学习者的路线差异；
- 比较不同目标任务的路线差异；
- 检查实践任务是否可执行；
- 完成`evaluation/roadmap_review.md`。

### 实验结果

1. 6个案例成功数量：
2. 时间约束通过数量：
3. 出现虚构路径的案例：
4. 出现错误source证据的案例：
5. 个性化差异是否明显：
6. 目标任务差异是否明显：

### 当前结论

根据实际结果填写，不能只写“效果很好”。

### 下一步

开始V0.4源码证据层，接收真实本地仓库路径，
自动读取README和目录结构。

## 2026-08-06：本地仓库路径校验

### 今天的目标

让RepoMentor可以接收本地仓库路径，
并在读取仓库内容前完成基础校验。

### 今天完成

- 创建`repository_service.py`；
- 使用`pathlib.Path`处理本地路径；
- 支持相对路径转换为绝对路径；
- 支持展开用户目录；
- 处理带引号的路径；
- 检查路径是否存在；
- 检查路径是否为文件夹；
- 尝试访问目录并处理权限错误；
- 返回结构化的`RepositoryInfo`；
- 记录目标目录是否存在`.git`；
- 测试正常路径、空路径、不存在路径和文件路径。

### 今天理解的内容

- 用户输入不能直接交给后续目录扫描程序；
- 路径存在不代表它一定是文件夹；
- 相对路径容易受到当前工作目录影响；
- 应该尽早把路径转换成规范的绝对路径；
- 没有`.git`的目录也可能是可以分析的源码目录；
- 路径校验和仓库内容分析应该分成不同职责。

### 测试结果

1. RepoMentor项目根目录：
   - 结果：
   `
测试案例：正常的RepoMentor项目路径
=======================
输入内容：WindowsPath('D:/PPT文档/agent初学代码/repo-mentor')
=======================
本地仓库路径校验成功
=======================
仓库名称：repo-mentor
绝对路径：D:\PPT文档\agent初学代码\repo-mentor
Git元数据：已发现.git`

2. 空路径：
   - 结果：
   `测试案例：空路径
============================================================
输入内容：'   '
校验失败仓库路径不能为空，请输入一个本地文件夹路径。`

3. 不存在的路径：
   - 结果：
    `测试案例：不存在的路径
============================================================
输入内容：WindowsPath('D:/PPT文档/agent初学代码/repo-mentor/this_repository_does_not_exist')
校验失败仓库路径不存在：D:\PPT文档\agent初学代码\repo-mentor\this_repository_does_not_exist`
4. README文件路径：
   - 结果：
       `测试案例：路径指向文件而不是文件夹
   ============================================================
   输入内容：WindowsPath('D:/PPT文档/agent初学代码/repo-mentor/README.md')
   校验失败仓库路径不是文件夹：D:\PPT文档\agent初学代码\repo-mentor\README.md`

5.另一个真实本地项目：
   - 结果： 
   `测试案例：另一个本地代码项目
============================================================
输入内容：'D:\\AI做的好玩的东西\\AI_Pet_2.01'
============================================================
本地仓库路径校验成功
============================================================
仓库名称：AI_Pet_2.01
绝对路径：D:\AI做的好玩的东西\AI_Pet_2.01
Git元数据：未发现.git`


### 遇到的问题

无。

### 下一步

根据经过校验的本地仓库路径生成安全、有限制的目录树，
并忽略`.git`、虚拟环境和缓存目录。

## 2026-08-07：安全生成真实仓库目录树

### 今天的目标

根据经过校验的本地仓库路径，
生成稳定、安全且有限制的真实目录树。

### 今天完成

- 创建`repository_tree.py`；
- 使用`Path.iterdir()`遍历真实仓库；
- 自动区分文件和目录；
- 对目录和文件进行稳定排序；
- 默认忽略`.git`、`.idea`、`.venv`、`.env`和缓存目录；
- 增加最大扫描深度；
- 增加最大文件数量；
- 达到限制时返回截断提示；
- 不跟随符号链接；
- 记录扫描文件数和目录数；
- 在RepoMentor和另一个真实项目上完成测试。

### 今天理解的内容

- 目录扫描必须设置范围限制；
- 不能直接递归一个未知大小的仓库；
- 目录树应该保持稳定排序，方便测试和后续模型输入；
- `.git`和`.env`不应该进入模型上下文；
- `.env.example`可以保留；
- 符号链接可能让递归扫描离开目标仓库；
- 路径真实存在不等于源码内容已经被理解。

### 测试结果

1. RepoMentor正常目录树：
   - 结果：
    `check .env, ignore=True
check .env.example, ignore=False
check .git, ignore=True
check .gitignore, ignore=False
check .idea, ignore=True
check data, ignore=False
check docs, ignore=False
check evaluation, ignore=False
check outputs, ignore=False
check README.md, ignore=False
check requirements.txt, ignore=False
check src, ignore=False
check tests, ignore=False
check demo_repo, ignore=False
check evaluation, ignore=False
check README.md, ignore=False
check target_task.json, ignore=False
check tree.txt, ignore=False
check user_profile.json, ignore=False
check learner_profiles, ignore=False
check target_tasks, ignore=False
check beginner.json, ignore=False
check intermediate.json, ignore=False
check limited_time.json, ignore=False
check prepare_new_tool.json, ignore=False
check understand_tool_calling.json, ignore=False
check learning-code.md, ignore=False
check learning-log.md, ignore=False
check product-positioning.md, ignore=False
check prompt-experiments.md, ignore=False
check roadmap_review.md, ignore=False
check evaluation, ignore=False
check prompt_experiments, ignore=False
check roadmap.json, ignore=False
check roadmap.md, ignore=False
check sample_roadmap.json, ignore=False
check beginner__prepare_new_tool.json, ignore=False
check beginner__prepare_new_tool.md, ignore=False
check beginner__understand_tool_calling.json, ignore=False
check beginner__understand_tool_calling.md, ignore=False
check intermediate__prepare_new_tool.json, ignore=False
check intermediate__prepare_new_tool.md, ignore=False
check intermediate__understand_tool_calling.json, ignore=False
check intermediate__understand_tool_calling.md, ignore=False
check limited_time__prepare_new_tool.json, ignore=False
check limited_time__prepare_new_tool.md, ignore=False
check limited_time__understand_tool_calling.json, ignore=False
check limited_time__understand_tool_calling.md, ignore=False
check v1_baseline.md, ignore=False
check v2_constrained.md, ignore=False
check v3_evidence_based.md, ignore=False
check repo_mentor, ignore=False
check config.py, ignore=False
check evaluation_runner.py, ignore=False
check llm_service.py, ignore=False
check main.py, ignore=False
check models.py, ignore=False
check model_demo.py, ignore=False
check prompts.py, ignore=False
check prompt_experiment.py, ignore=False
check repository_service.py, ignore=False
check repository_tree.py, ignore=False
check roadmap_generator.py, ignore=False
check __init__.py, ignore=False
check __pycache__, ignore=True
============================================================
仓库目录树
============================================================
repo-mentor/
 ├── data/
 │   ├── demo_repo/
 │   │   ├── README.md
 │   │   ├── target_task.json
 │   │   ├── tree.txt
 │   │   └── user_profile.json
 │   └── evaluation/
 │       ├── learner_profiles/
 │       │   ├── beginner.json
 │       │   ├── intermediate.json
 │       │   └── limited_time.json
 │       └── target_tasks/
 │           ├── prepare_new_tool.json
 │           └── understand_tool_calling.json
 ├── docs/
 │   ├── learning-code.md
 │   ├── learning-log.md
 │   ├── product-positioning.md
 │   └── prompt-experiments.md
 ├── evaluation/
 │   └── roadmap_review.md
 ├── outputs/
 │   ├── evaluation/
 │   │   ├── beginner__prepare_new_tool.json
 │   │   ├── beginner__prepare_new_tool.md
 │   │   ├── beginner__understand_tool_calling.json
 │   │   ├── beginner__understand_tool_calling.md
 │   │   ├── intermediate__prepare_new_tool.json
 │   │   ├── intermediate__prepare_new_tool.md
 │   │   ├── intermediate__understand_tool_calling.json
 │   │   ├── intermediate__understand_tool_calling.md
 │   │   ├── limited_time__prepare_new_tool.json
 │   │   ├── limited_time__prepare_new_tool.md
 │   │   ├── limited_time__understand_tool_calling.json
 │   │   └── limited_time__understand_tool_calling.md
 │   ├── prompt_experiments/
 │   │   ├── v1_baseline.md
 │   │   ├── v2_constrained.md
 │   │   └── v3_evidence_based.md
 │   ├── roadmap.json
 │   ├── roadmap.md
 │   └── sample_roadmap.json
 ├── src/
 │   └── repo_mentor/
 │       ├── __init__.py
 │       ├── config.py
 │       ├── evaluation_runner.py
 │       ├── llm_service.py
 │       ├── main.py
 │       ├── model_demo.py
 │       ├── models.py
 │       ├── prompt_experiment.py
 │       ├── prompts.py
 │       ├── repository_service.py
 │       ├── repository_tree.py
 │       └── roadmap_generator.py
 ├── tests/
 ├── .env.example
 ├── .gitignore
 ├── README.md
 └── requirements.txt

============================================================
扫描统计
============================================================
文件数量：48
目录数量：13
是否截断：否`

2. `.git/.idea/.venv/.env`：
   - 是否成功忽略：是

3. `max_depth=1`：
   - 结果：

4. `max_files=5`：
   - 结果：

5. 错误`max_depth=0`：
   - 结果：

6. 错误`max_files=0`：
   - 结果：

7. 另一个真实项目：
   - 结果：

### 遇到的问题

#### 1. TreeBuildResult字段不一致

创建`TreeBuildResult`时传入了`directory_count`，
但数据类中没有定义该字段，因此出现：

`TreeBuildResult.__init__() got an unexpected keyword argument 'directory_count'`

修复方法是在`TreeBuildResult`中改为`directory_count`字段，
并保证返回对象和数据模型定义一致。

#### 2. .env没有被扫描规则忽略

调试`should_ignore()`时发现：

`.env → ignore=False`

说明Git的`.gitignore`和RepoMentor自己的目录扫描规则是两套独立机制。

最终在仓库扫描规则中单独处理`.env`和`.env.*`，
同时保留公开的`.env.example`。

另外将`outputs/`加入扫描忽略规则，
避免把RepoMentor自身生成的路线和评测结果重新作为仓库输入。

### 下一步

安全读取真实仓库中的README、CONTRIBUTING和项目配置文件，
为学习路线提供真实的仓库文本证据。

## 2026-08-08：读取真实仓库入门资料

### 今天的目标

安全读取真实本地仓库中的README、
CONTRIBUTING、项目配置和docs入口，
为后续学习路线建立真实文本证据。

### 今天完成

- 创建`repository_reader.py`；
- 读取README候选文件；
- 读取CONTRIBUTING候选文件；
- 读取`pyproject.toml`和`requirements.txt`；
- 尝试读取常见docs入口；
- 使用`RepositoryDocument`保存内容和真实来源路径；
- 增加单文件大小限制；
- 增加简单二进制检测；
- 支持UTF-8中文内容；
- 阻止读取仓库范围外的路径；
- 跳过符号链接文件；
- 缺少文件时返回警告而不是崩溃。

### 今天理解的内容

- 目录树只能证明文件存在，不能证明文件里面是什么；
- 后续仓库理解必须建立在真实文件内容上；
- 每段模型上下文都应该尽可能保留来源；
- 文件读取应该限制大小，不能把未知大文件直接送给模型；
- 确定性的文件检查不应该交给大模型；
- 读取失败应该尽量隔离，不能因为一个文件失败让整个仓库失效。

### 测试结果

1. RepoMentor README：
   - 结果：
   `============================================================
仓库入门资料：repo-mentor
============================================================

------------------------------------------------------------
资料类型：readme
来源路径：README.md
文件大小：9999 bytes
   - ============================================================
读取警告
============================================================
- 未找到CONTRIBUTING文件。
- 检测到可能的二进制文件，已跳过：requirements.txt`

2. requirements.txt：
   - 结果：

3. 缺少README：
   - 结果：
    `============================================================
仓库入门资料：repo-mentor
============================================================
没有读取到可用资料。

============================================================
读取警告
============================================================
- 未找到README文件。
- 未找到CONTRIBUTING文件。
- 检测到可能的二进制文件，已跳过：requirements.txt
`
4. 中文README：
   - 结果：

5. 超大文件：
   - 结果：

6. 二进制文件：
   - 结果：

7. 另一个真实仓库：
   - 结果：

### 遇到的问题

`.relative_to()`写成了`.resolve_to(other)`注意区分。

### 下一步

根据用户目标和仓库信息，
为真实仓库中的文件建立相关性评分和证据模型。

## 2026-08-09：目标相关文件排序与 pytest 基础测试

### 今天的目标

让 RepoMentor 不再只寻找“仓库中的重要文件”，
而是根据当前目标任务，从真实仓库中寻找真正相关的文件，
并为推荐结果保存可追溯的证据。

同时开始为 RepoMentor 建立自动化测试，
学习 pytest 的基本使用方式和 Python package 的导入机制。

---

### 今天完成

- 定义 `RepositoryEvidence`，用于保存真实仓库证据；
- 定义目标相关文件排序结果模型；
- 实现目标关键词提取；
- 建立中文目标词到英文路径关键词的映射；
- 从真实文件系统中收集候选文件；
- 根据目标关键词和文件路径计算相关性；
- 根据 README 中的真实文件引用增加推荐证据；
- 对入口文件、配置文件和测试文件增加辅助评分；
- 输出 Top-N 目标相关文件；
- 每个候选包含文件路径、分数、推荐理由和证据；
- 对尚未读取源码内容的文件标记为 `needs_confirmation`；
- 使用同一 RepoMentor 仓库的不同目标进行排序对照；
- 创建 `tests/test_repository_ranker.py`；
- 创建 `pytest.ini`；
- 将 `src` 配置为 pytest 的 Python 模块搜索路径；
- 将测试相关代码逐步改为标准 `repo_mentor` package 导入；
- 成功使用 pytest 运行目标文件排序测试；
- 当前 2 个测试通过。

---

### 今天理解的目标相关文件排序

#### 1. “重要文件”不等于“目标相关文件”

例如：

`README.md`、`main.py` 可能是一个项目中的重要文件，

但如果用户的目标是：

“理解 RepoMentor 的目录树生成流程”

那么：

`repository_tree.py`

和：

`repository_service.py`

通常应该比通用入口文件获得更高优先级。

因此 RepoMentor 的排序目标不是：

“找这个仓库最重要的文件”

而是：

“为了用户当前的具体学习目标，哪些文件最值得优先查看”。

---

#### 2. 候选文件必须来自真实文件系统

不能让模型直接生成文件路径。

正确的数据流应该是：

真实仓库
→ 实际扫描得到文件路径
→ 根据目标计算相关性
→ 排序
→ 返回 Top-N

这样可以从结构上减少模型推荐不存在文件的问题。

---

#### 3. 文件真实存在不代表已经知道文件内容

例如：

`src/repo_mentor/repository_tree.py`

真实存在，只能证明：

“这个路径存在”。

如果还没有读取源码，就不能直接断言：

“该文件中的某个函数使用了某种具体实现方式”。

因此目前对普通源码候选使用：

`needs_confirmation`

表示：

“路径和目标存在相关性，但具体源码职责仍需要读取真实内容后确认”。

---

#### 4. RepositoryEvidence 必须可以追溯

证据不能只保存一句推荐理由，还需要记录：

- `source_path`：证据来自哪个真实文件；
- `snippet`：真实文件中的文本片段；
- `reason`：为什么这条证据与目标相关；
- `confidence`：这条证据规则本身的强弱。

其中 `confidence` 表示的是：

“这条推荐依据有多强”

而不是：

“模型觉得自己有多大概率是正确的”。

---

### 今天学习的 pytest

#### 1. pytest 是什么

pytest 是 Python 中常用的自动化测试框架。

以前验证程序主要依靠：

运行 Python 文件
→ 看终端输出
→ 人工判断结果是否正确

使用 pytest 后，可以把预期行为写成代码：

输入
→ 调用被测试函数
→ 使用 assert 检查结果
→ 自动判断 PASS / FAIL

例如：

```python
assert len(results) <= 3
```

### 遇到的问题：pytest无法导入项目模块

首次运行`test_repository_ranker.py`时出现：

`ModuleNotFoundError: No module named 'models'`

原因是此前项目代码主要通过PyCharm直接运行单个Python文件，
因此使用了：

`from models import TargetTask`

这种同目录脚本式导入。

pytest从`tests/`目录收集测试时，
`models.py`并不是顶层Python模块，
真正的包路径应该是：

`repo_mentor.models`

解决方法：

- 将`src`作为项目源码根目录；
- 新增`pytest.ini`，配置`pythonpath = src`；
- 测试代码改用`from repo_mentor.models import ...`；
- 将repository模块之间的导入逐步改为标准包导入。

这个问题让我理解了直接运行Python脚本与
从Python package中导入模块的区别。

### 当前 pytest 测试结果

运行命令：

```powershell
& "D:\Anac\envs\agent\python.exe" -m pytest tests/test_repository_ranker.py -v
```
### 今日开发轨迹
写目标排序器
↓
NameError
↓
理解函数作用域和定义

开始写pytest
↓
ModuleNotFoundError
↓
理解脚本导入和package导入

PowerShell运行pytest
↓
No module named pytest
↓
发现IDE解释器与终端Python不是同一环境

显式使用agent环境
↓
pytest成功收集测试
↓
4 passed

## 2026-08-10：仓库证据 Tools 封装

### 今天的目标

将此前实现的仓库路径校验、目录树、
入门资料读取、单文件读取和目标文件排序能力，
封装为具有明确输入 Schema 和调用说明的 LangChain Tools。

### 今天完成

- 创建 `repository_tools.py`；
- 学习 LangChain Tool 与普通 Python 函数的区别；
- 定义 `get_repo_tree`；
- 定义 `get_onboarding_docs`；
- 定义 `read_repo_file`；
- 定义 `rank_target_files`；
- 为每个 Tool 定义输入 Pydantic Schema；
- 为每个 Tool 编写明确 docstring；
- 使用结构化 dict 返回 Tool 结果；
- 区分 Schema 参数错误和业务执行错误；
- 对 `read_repo_file` 增加敏感路径保护；
- 创建统一 `REPOSITORY_TOOLS` 列表；
- 使用 `.invoke()` 独立测试每个 Tool；
- 使用 pytest 增加 Repository Tool 测试。

### 今天理解的内容

#### 1. Tool 不是重新实现业务逻辑

Tool 层负责向模型暴露能力，
真正的仓库逻辑仍由已有的
`repository_tree`、`repository_reader`
和 `repository_ranker` 完成。

#### 2. Tool 的 name、description 和 Schema 是模型的使用说明

模型以后并不是直接阅读 Python 实现判断怎么调用，
而是主要根据 Tool 的名称、说明和参数结构决定使用哪个工具。

因此 Tool 描述不仅要说明“它能做什么”，
还应该说明“什么时候应该用”和“什么时候不应该用”。

#### 3. `.invoke()` 可以在没有 LLM 的情况下测试 Tool

今天还没有让模型调用 Tool。

先通过：

`tool.invoke({...})`

单独验证每个 Tool 的输入、执行和输出，
可以把 Tool 本身的问题与模型 Tool Calling 的问题分开。

#### 4. Schema 错误和执行错误不同

例如 `max_depth=0`
属于参数 Schema 不合法，
应该在真正执行 Tool 前被 Pydantic 拒绝。

而不存在的仓库路径属于参数格式合法、
但业务执行失败，应返回受控错误信息。

#### 5. Tool 应优先复用确定性 Python 能力

目录扫描、文件读取、路径检查和目标相关性规则
已经有确定性 Python 实现，
不应该为了使用 Agent 而重新交给 LLM 完成。

### 测试结果

填写实际结果：

- `test_repository_ranker.py`：
- `test_repository_tools.py`：
========================================================================= test session starts =========================================================================
```platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- D:\Anac\envs\agent\python.exe
cachedir: .pytest_cache
rootdir: D:\PPT文档\agent初学代码\repo-mentor
configfile: pytest.ini
plugins: anyio-4.14.2, langsmith-0.10.12
collected 1 item                                                                                                                                                        

tests/test_repository_tools.py::test_get_repo_tree_can_invoke PASSED                                                                                             [100%] 

========================================================================== warnings summary =========================================================================== 
src\repo_mentor\repository_tools.py:4
  D:\PPT文档\agent初学代码\repo-mentor\src\repo_mentor\repository_tools.py:4: DeprecationWarning: 'msilib' is deprecated and slated for removal in Python 3.13
    from msilib.schema import Class

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
==================================================================== 1 passed, 1 warning in 0.61s ===================================================================== 
PS D:\PPT文档\agent初学代码\repo-mentor> & "D:\Anac\envs\agent\python.exe" -m pytest tests/test_repository_tools.py -v
========================================================================= test session starts =========================================================================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- D:\Anac\envs\agent\python.exe
cachedir: .pytest_cache
rootdir: D:\PPT文档\agent初学代码\repo-mentor
configfile: pytest.ini
plugins: anyio-4.14.2, langsmith-0.10.12
collected 6 items                                                                                                                                                       

tests/test_repository_tools.py::test_get_repo_tree_can_invoke PASSED                                                                                             [ 16%] 
tests/test_repository_tools.py::test_get_onboarding_docs_can_invoke PASSED                                                                                       [ 33%] 
tests/test_repository_tools.py::test_read_repo_file_can_invoke PASSED                                                                                            [ 50%] 
tests/test_repository_tools.py::test_rank_target_files_can_invoke PASSED                                                                                         [ 66%] 
tests/test_repository_tools.py::test_invalid_tool_argument_is_rejected PASSED                                                                                    [ 83%] 
tests/test_repository_tools.py::test_read_repo_file_rejects_env PASSED                                                                                           [100%] 

========================================================================== warnings summary =========================================================================== 
src\repo_mentor\repository_tools.py:4
  D:\PPT文档\agent初学代码\repo-mentor\src\repo_mentor\repository_tools.py:4: DeprecationWarning: 'msilib' is deprecated and slated for removal in Python 3.13
    from msilib.schema import Class

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
==================================================================== 6 passed, 1 warning in 0.69s ===================================================================== 
PS D:\PPT文档\agent初学代码\repo-mentor>
```

- 总测试数量：6
- 通过数量：6

### 遇到的问题

填写今天真实出现的问题，不提前编写结论。

### 下一步

让模型绑定 `REPOSITORY_TOOLS`，
根据具体学习目标产生 tool calls，
执行工具并将 ToolMessage 返回模型。

### 草稿

昨天已经有：

```
REPOSITORY_TOOLS = [
    get_repo_tree,
    get_onboarding_docs,
    read_repo_file,
    rank_target_files,
]
```
现在假设：
```

llm = create_llm(...)
llm_with_tools = llm.bind_tools(REPOSITORY_TOOLS)

```
问题：
第一题：
① bind_tools() 会不会立即执行这四个 Tool？
② 调用 llm_with_tools.invoke(...) 后，是 Python 在选择工具，还是模型在选择工具？
③ 如果模型决定调用 rank_target_files，它会直接拿到工具执行结果吗？
④ llm 和 llm_with_tools 的区别是什么？

答案：
①不会
②模型在选择工具
③不会
④llm_with_tools 是 “配备了工具说明书” 的模型，而 llm 是“赤手空拳”的模型。说明书（工具定义）让模型学会了“如何请求外部能力”，但真正的“伸手去做（执行）”仍需你编写代码实现。

第二题：

一条 tool_call 最重要的三个字段是什么？为什么除了 name 和 args 之外，还必须有 id？
- id（唯一调用标识符）
- name（要调用的工具名称）
- args（传递给工具的参数）
- name 和 args 解决的是 “做什么” 和 “怎么做” 的问题（语义和逻辑）。
- id 解决的是 “这次请求是谁发的” 和 “结果要回传给谁” 的问题（上下文追踪）。
思考题
假设：
模型同时调用：
get_repo_tree
get_onboarding_docs
如果没有：
tool_call_id 模型后来收到两个 Tool 结果时，怎么知道哪个结果属于哪个请求？

| 实验 | 目标 | 实际 Tool Calls                                                                         | 调用数 | 是否合理 |
| :--- | :--- |:--------------------------------------------------------------------------------------|----:|:-----|
| A | 只看目录 | `get_repo_tree`                                                                       |   1 | 合理   |
| B | 项目介绍/依赖/贡献 | `get_onboarding_docs → get_repo_tree`                                                 |   2 | 合理   |
| C | 理解目录树扫描流程 | `get_repo_tree → rank_target_files → 2×read_repo_file`                                |   4 | 合理   |
| D | 已知 README，只读取 | `read_repo_file`                                                                                      |   1 | 合理   |

## 2026-08-11：目标驱动 Tool Calling

### 今天的目标

让 RepoMentor 不再由 Python 代码提前决定调用哪个仓库工具，
而是把 Repository Tools 提供给模型，
让模型根据用户当前的具体学习或贡献目标
自主判断是否需要工具以及应该使用哪个工具。

同时实现一个最小、有限轮次的 Tool Calling 循环，
把真实工具执行结果重新返回模型，
使模型能够根据新获得的仓库证据继续决策。

---

### 今天完成

- 创建 `target_tool_calling.py`；
- 将四个 Repository Tools 绑定给 LLM；
- 理解 `bind_tools()` 与真正 Tool 执行之间的区别；
- 学习并观察 `AIMessage.tool_calls`；
- 理解 Tool Call 中 `name`、`args` 和 `id` 的作用；
- 创建 Tool 名称到 Tool 对象的注册表；
- 根据模型提供的 `name` 查找真实 Tool；
- 根据模型提供的 `args` 执行 Tool；
- 将 Tool 返回结果序列化为可传递给模型的内容；
- 使用 `ToolMessage` 将工具结果重新放回消息历史；
- 保证 `ToolMessage.tool_call_id`
  与对应 `AIMessage.tool_calls[].id` 一致；
- 支持同一次模型响应产生多个 Tool Call；
- 实现最多两轮的 Tool Calling 循环；
- 记录 Tool 名称、参数、调用 ID、轮次和总调用次数；
- 达到最大 Tool Calling 轮次后，
  使用不绑定工具的模型进行最终总结；
- 增加强制总结指令，
  防止模型在已经禁止工具调用时继续模拟 Tool Call；
- 使用多个不同目标测试模型的工具选择行为；
- 为 Tool 注册表和 ToolMessage 执行流程增加 pytest 测试；
- 修复项目内部剩余的 Python package 导入问题；
- 当前相关 pytest 测试均已通过。

---

### 今天理解的核心流程

RepoMentor 当前的最小 Tool Calling 流程为：

```text
SystemMessage + HumanMessage
↓
llm.bind_tools(REPOSITORY_TOOLS)
↓
llm_with_tools.invoke(messages)
↓
AIMessage
↓
检查 AIMessage.tool_calls
↓
根据 tool_call["name"] 找到 Tool
↓
使用 tool_call["args"] 执行 Tool
↓
获得真实 Tool 结果
↓
创建 ToolMessage
↓
tool_call["id"]
=
ToolMessage.tool_call_id
↓
将 ToolMessage 加入 messages
↓
再次调用模型
↓
继续调用 Tool 或生成最终回答
```

## 2026-08-12：日志、错误与范围限制

### 今天的目标

在已经能够完成目标驱动 Tool Calling 的基础上，为 Repository Tools 增加工程化保护。

目标不是继续增加更多 Tool，而是控制已有 Tool：

* 执行了什么；
* 执行了多久；
* 是否失败；
* 是否值得重试；
* 允许读取多少仓库证据；
* 日志中是否可能泄露敏感信息。

---

### 今天完成

* 新增 `repository_safeguards.py`；
* 使用标准 `logging` 记录 Tool 执行状态；
* 学习并区分 DEBUG、INFO、WARNING、ERROR 日志级别；
* 实现 `redact_for_log()` 对日志参数进行递归脱敏；
* 支持嵌套 dict、list、tuple 中敏感字段的保护；
* 定义 `EvidenceBudget`；
* 同时限制进入模型上下文的文件数量和字符数量；
* 保存 `used_files`、`used_chars`、`stopped` 和 `stop_reason`；
* 实现 Tool 执行耗时统计；
* 区分可重试错误和不可重试错误；
* 暂时性失败最多额外重试一次；
* 最终 Tool 失败转换为结构化错误，不直接使整个 Agent 崩溃；
* 日志只记录 Tool 结果摘要，不打印完整仓库源码；
* 将 safeguards 接入目标驱动 Tool Calling；
* 证据预算耗尽后阻止后续文件读取；
* 即使 Tool 因预算被拒绝，仍返回与原 Tool Call ID 对应的 `ToolMessage`；
* 使用 pytest 验证日志脱敏、预算、重试和 Tool Calling 相关行为；
* 全量自动化测试通过。

---

### 1. 日志和 print 的区别

以前项目中很多调试主要通过：

```python
print(...)
```

观察程序行为。

随着 Tool Calling 流程变长，需要区分不同严重程度的信息，因此开始使用 Python `logging`。

目前理解为：

```text
DEBUG
→ 开发调试细节，例如脱敏后的 Tool 参数

INFO
→ 正常生命周期，例如 Tool 开始、完成、耗时

WARNING
→ 出现异常情况，但程序仍然能够继续，例如准备重试或预算耗尽

ERROR
→ 某项操作最终失败
```

日志的目的不是打印所有数据，而是帮助定位：

```text
哪个Tool
什么时候执行
是否成功
用了多久
尝试几次
为什么停止
```

---

### 2. Tool 计时不等于强制超时

使用：

```python
time.perf_counter()
```

记录：

```text
Tool开始时间
↓
Tool执行
↓
Tool结束时间
↓
计算elapsed_seconds
```

可以知道 Tool 实际执行了多长时间。

但这只是：

```text
计时
```

不是：

```text
强制超时
```

如果一个 Tool 实际执行 8 秒，
`perf_counter()` 只能在它结束后告诉程序：

```text
运行了8秒
```

不会在第3秒自动终止 Tool。

因此当前版本记录执行耗时，
真正的强制超时机制留给后续进一步实现。

---

### 3. 重试不是“失败就再跑一次”

今天开始区分：

```text
暂时性失败
```

和：

```text
确定性失败
```

例如：

```text
TimeoutError
ConnectionError
部分临时 OSError
```

下一次执行可能成功，因此可以最多重试一次。

但是：

```text
ValueError
参数Schema错误
路径本身不存在
敏感文件访问被拒绝
预算已经耗尽
```

使用相同参数重新执行通常不会改变结果，因此不应该进行无意义重试。

当前：

```text
max_retries = 1
```

含义是：

```text
第一次正常执行
+
最多额外重试1次

最多执行2次
```

而不是总共只执行一次。

---

### 4. 日志脱敏

新增：

```python
redact_for_log()
```

用于在 Tool 参数进入日志之前隐藏敏感字段。

例如原始数据：

```text
MODEL_API_KEY = sk-xxxx
password = 123456
```

日志中的安全副本应变成：

```text
MODEL_API_KEY = ***REDACTED***
password = ***REDACTED***
```

当前匹配的敏感语义包括：

* api_key
* apikey
* token
* password
* secret
* authorization

判断使用“字段名包含敏感关键词”，而不仅仅是完全相等。

原因是实际配置字段可能是：

```text
MODEL_API_KEY
OPENAI_API_KEY
ACCESS_TOKEN
```

这些名称不会与 `api_key` 或 `token` 完全相等，但仍然属于敏感字段。

---

### 5. 为什么日志脱敏返回新对象

`redact_for_log()` 不应该直接修改真正的 `tool_args`。

正确关系是：

```text
真实 tool_args
├── Tool执行
│   └── 保留真实参数
│
└── logging
    ↓
redact_for_log()
    ↓
只记录脱敏后的副本
```

否则如果直接把：

```text
api_key
```

替换成：

```text
***REDACTED***
```

真正执行 Tool 时也会失去需要的真实参数。

因此：

```text
业务数据
```

和：

```text
日志展示数据
```

需要分离。

---

### 6. EvidenceBudget

今天新增确定性的证据读取预算。

主要字段：

```text
max_files
max_chars

used_files
used_chars

stopped
stop_reason
```

预算判断不是针对单次请求，而是累计计算：

```text
used_files + 本次file_count
used_chars + 本次char_count
```

如果任何一项超过限制，本次证据不会继续进入模型上下文。

例如：

```text
max_chars = 10000
used_chars = 8000
本次结果 = 5000 chars
```

则：

```text
8000 + 5000
= 13000
> 10000
```

本次结果被拒绝。

并且被拒绝的 5000 字符不会计入：

```text
used_chars
```

---

### 7. 为什么同时需要文件数和字符数预算

只有：

```text
max_files
```

时，模型可能只读取几个非常大的文件。

只有：

```text
max_chars
```

时，模型又可能不断读取大量非常小的文件。

因此同时使用：

```text
max_files
+
max_chars
```

分别控制：

```text
文件数量
+
证据总体积
```

能够更有效限制模型无目的地扩大读取范围。

---

### 8. 字符预算使用 len(content)，而不是 size_bytes

当前预算关注的是：

```text
有多少文本字符进入模型上下文
```

而不是：

```text
文件在磁盘上占多少字节
```

因此对于 `read_repo_file`：

```python
len(result["content"])
```

比：

```text
size_bytes
```

更加符合当前 EvidenceBudget 的语义。

特别是中文 UTF-8 文本中：

```text
字符数量
≠
字节数量
```

---

### 9. 预算由 Python 控制，而不是依赖 Prompt

如果只在 System Prompt 中告诉模型：

```text
不要读取太多文件
```

这只是一个软约束。

模型仍然可能请求：

```text
read file1
read file2
...
read file20
```

现在真正决定是否允许执行的是：

```text
EvidenceBudget
```

因此流程变成：

```text
LLM：
我想继续读取

↓ 请求

Python：
检查预算

↓ 允许

执行Tool

或

↓ 拒绝

BudgetExceeded
```

这让我理解到：

```text
模型拥有决策能力
≠
模型拥有无限执行权限
```

真正的安全边界应该由确定性程序控制。

---

### 10. 预算拒绝也必须返回 ToolMessage

假设同一个 AIMessage 请求：

```text
Tool Call A
Tool Call B
```

执行 A 后预算耗尽。

不能直接：

```text
break
```

然后不给 B 返回结果。

否则消息历史中会出现：

```text
Tool Call A → ToolMessage
Tool Call B → 没有对应结果
```

正确做法是：

```text
Tool Call A
→ 正常ToolMessage

Tool Call B
→ BudgetExceeded ToolMessage
```

并保持：

```text
tool_call["id"]
=
ToolMessage.tool_call_id
```

这样即使 Tool 没有真正执行，
Tool Calling 消息协议仍然完整。

---

### 11. Tool 结果日志只保存摘要

如果直接：

```text
logger.info(tool_result)
```

`read_repo_file` 很可能把完整源码写入日志。

因此增加 Tool 结果摘要。

例如：

```text
read_repo_file
→ source_path
→ chars
→ elapsed
→ attempts
```

而不是记录整个：

```text
content
```

目录树和文件排序也只记录：

```text
file_count
candidate_count
top_files
truncated
```

等必要信息。

这样日志既能够帮助定位问题，
又不会变成第二份源码或敏感数据存储。

---

### 12. 自动化测试

今天新增 safeguards 相关 pytest。

当前全量测试结果：

```text
18 passed in 2.31s
```

测试覆盖包括：

* 不同目标文件排序；
* Top-N 限制；
* 推荐文件真实存在；
* README 真实证据片段；
* Repository Tools 独立调用；
* Tool 参数错误；
* `.env` 文件访问限制；
* Tool 注册表；
* ToolMessage 与原 Tool Call ID 对应；
* 敏感日志字段脱敏；
* 文件数量预算；
* 暂时性失败重试；
* 确定性错误不重试；
* 日志不暴露 API Key。
* 字符预算测试


---

### 当前不足

当前 safeguards 仍是第一版：

* 当前只有耗时统计，没有真正的强制 Tool 超时；
* EvidenceBudget 主要限制 Tool 结果进入模型上下文，
  不能阻止文件首先被读取到 Python 内存；
* 重试策略仍然较简单；
* 当前主要根据结构化字段名称进行日志脱敏；
* 尚未实现复杂的秘密文本检测；
* 当前 Tool Calling 仍然是手写有限循环；
* 预算大小仍需要通过更多真实仓库实验调整。

---

### 今天的核心认识

昨天解决的问题是：

```text
模型会不会使用Tool？
```

今天解决的问题是：

```text
即使模型会使用Tool，
程序应该允许它做到什么程度？
```

当前形成的职责划分是：

```text
LLM
↓
理解目标
选择Tool
生成参数

Python
↓
验证Tool
检查预算
保护敏感信息
执行Tool
控制重试
记录日志
限制范围
返回结果
```

因此 RepoMentor 当前的 Agent 设计逐渐变成：

```text
LLM负责决策
+
Tool负责能力
+
确定性代码负责安全边界
```

而不是让 LLM 无限制控制整个程序。

---

### 下一步

完成 V0.4 源码证据层的三仓库验证：

* 在 RepoMentor 自身进行完整验证；
* 选择另外两个小型 Python 仓库；
* 使用不同目标测试目标文件排序和 Tool Calling；
* 人工核对候选文件与真实证据；
* 检查工具选择是否存在冗余；
* 检查预算和异常保护；
* 更新 V0.4 演示和 README。

---

## 2026-08-13：V0.4 三仓库验证与证据质量检查

### 今天的目标

在 RepoMentor 自身和两个小型 Python 仓库（ItsDangerous、Pipfile）上
验证 V0.4 证据层，复习 Tool 与普通函数的区别，并人工检查证据质量。

### 今天完成

* 复习 Tool 与普通函数的区别；
* 在三个真实仓库上运行六个 Case（R1-A/B、R2-A/B、R3-A/B）；
* 人工核对候选文件与证据，完成 `evaluation/v04_evidence_review.md`；
* 根据结论完成修复（max_rounds=3、onboarding 预算、Ranker 改进、
  三仓库排序演示）；
* 清理重复测试并新增修复相关测试，pytest 22 个全部通过；
* 更新 README；
* 2026-08-15 执行六 Case 完整复验：
  R2/R3 中 3 个 Fail 修复为 Pass，R2-B 残留预算问题。

---

### 1. Tool 与普通函数的区别

普通函数：

* 直接 `函数名(...)` 调用；
* 只负责具体的计算或 IO，LLM 看不到也调不了；
* 例如 `build_tree()`、`rank_target_files_core()`、
  `read_repository_onboarding_docs()`。

Tool：

* 用 `@tool(args_schema=...)` 装饰并绑定到 LLM；
* 有输入 Schema、docstring 和结构化返回值；
* LLM 只能通过 Tool Call 间接调用，中间经过 `execute_tool_call` 的
  校验、预算、重试、脱敏；
* 例如 `get_repo_tree`、`get_onboarding_docs`、
  `read_repo_file`、`rank_target_files`。

一句话：普通函数是「能力」，Tool 是「给 LLM 的受控接口」，
确定性代码负责执行、验证和安全边界。

---

### 2. 三仓库验证发现的问题

* `max_rounds=2` 不足：外部仓库「发现 → 排序 → 读源码」
  需要至少 3 轮，导致 R2/R3 四个 Case 全部没有执行 `read_repo_file`；
* `get_onboarding_docs` 按文档数占用 3 / 4 文件预算；
* Ranker 缺少中文概念映射，核心源码无加分，
  svg logo 和 `requirements.txt` 被顶到排序第一；
* 资源文件未过滤，README 引用加成对非源码文件过强。

---

### 3. 修复内容

* `target_tool_calling.py`：默认轮次 2 → 3；
* `repository_safeguards.py`：整份 onboarding 按 1 个文件计费；
* `repository_ranker.py`：补充中文概念映射、
  核心 Python 源码 +2.0、资源文件过滤、
  非源码文件 README 引用降权；
* `v04_evaluation.py`：新增三仓库排序演示与六 Case 运行器；
* 测试：清理重复定义，新增 4 个修复相关测试。

---

### 4. 六 Case 复验结果（2026-08-15）

| Case | 旧结论 | 新结论 |
| --- | --- | --- |
| R1-A | Pass with Issues | Pass with Issues |
| R1-B | PASS | PASS |
| R2-A | Fail | Pass |
| R2-B | Fail | Fail（明显改善） |
| R3-A | Fail | Pass |
| R3-B | Fail | Pass |

R2-B 残留：对「如何被测试」类目标，
模型先读两个大实现文件（25880/30000 字符）占满预算，
导致测试文件被字符超限拦截。

---

### 下一步

* 修复 R2-B：提高字符预算（30_000 → 40_000），
  并引导「如何被测试」类目标优先读取测试文件；
* 重跑 R2-B 复验；
* 继续观察工具选择经济性问题。

## 2026-08-14：设计 AgentState（V0.6 自适应工作流第一步）

### 今天的目标

学习 LangGraph 的 State、共享数据和状态边界，为 V0.6
自适应工作流定义共享状态模型。

### 今天完成

* 学习 State 与普通 dict 的区别、reducer 的覆盖/累积语义；
* 新建 workflow_state.py，定义 8 个字段并注明来源与使用节点；
* 实现 create_initial_state() 与 validate_state_no_secrets()；
* 新增 5 个单元测试，全部通过；
* 完成最小 LangGraph 演示（step_count/errors 语义验证）；
* 提交 feat: define adaptive learning state。

### 1. State、reducer 与状态边界

* State 是节点共享的通道：节点只返回局部更新，LangGraph 合并；
* messages 用 add_messages（按 id 去重/更新）；
* errors 用 operator.add（累积）；
* step_count 用覆盖语义（节点自己 +1）；
* State 不放 API Key，validate_state_no_secrets 只查键名防误报；
* 模块导入不应有副作用：演示代码必须放在独立文件或
  if __name__ == "__main__" 里。

### 2. 今天踩的坑

* `target_task: TargetTask` 存了类而不是实例；
* `def f(state, Any)` 是两参数不是注解；
* `str(key).lower` 少了括号；
* 测试里 `message` 写成单数导致 KeyError（fail loudly 是好事）。

## 2026-08-15：拆分核心节点（V0.6 自适应工作流第二步）

### 今天的目标

学习节点读取 State、返回局部更新和单一职责，
为 V0.6 自适应工作流拆分核心节点。

### 今天完成

* 学习单一职责：一个节点只做一件事，输出是下一步的输入；
* AgentState 新增 5 个字段（repository_path、learner_analysis、
  target_analysis、repo_readme、repo_tree）；
* 新建 adaptive_nodes.py：analyze_learner / analyze_target /
  collect_evidence / generate_roadmap 四个节点；
* 修复 roadmap_generator.py 与 prompt_experiment.py 的
  脆弱 import（改为 repo_mentor. 前缀）；
* 4 个节点各配一个独立单元测试（generate_roadmap 用
  monkeypatch 打桩，不调真实 LLM），全部通过；
* 4 节点最小图运行验证 State 流转；
* 提交 feat: add adaptive planning nodes。

### 1. 节点与单一职责

* 节点 = 函数(state) -> 局部更新 dict；
* 判断职责的口诀：输入是什么、输出是什么、
  为什么输出刚好是下一步要用的；
* 需要 LLM 的只有 generate_roadmap，其余三个节点
  都是纯规则或复用 V0.4 证据层。

### 2. 测试里如何不花钱地测 LLM 节点

* monkeypatch 用假函数替换真实依赖，测试快、免费、可重复；
* 顺带断言参数被正确传递（captured 记录）。

### 3. 挖出的历史技术债

* roadmap_generator / prompt_experiment / repository_service /
  evaluation_runner / model_demo 存在裸 import 或 src. 前缀，
  已修前两者，其余列入待清理。

## 2026-08-16：连接基础工作流（V0.6 自适应工作流第三步）

### 今天的目标

学习 START/END、add_node、add_edge、compile、invoke，
把四个核心节点组装成可复用的基础图。

### 今天完成

* 学习 LangGraph 图 API：图不是顺序调用，支持分支/循环/路由；
* 新建 adaptive_workflow.py：
  build_adaptive_graph() + run_adaptive_workflow()；
* 一次 invoke 返回结构化 LearningRoadmap（含类型校验）；
* 图结构测试：节点齐全、边顺序与流程图一致；
* 整合测试：monkeypatch 打桩后整图跑通；
* （可选）真实 LLM 一次 invoke 验证；
* 提交 feat: build adaptive roadmap graph。

### 1. 图 vs 顺序调用

* 顺序调用写死流程；图把流程变成可组合、可动态决策的结构；
* 后面信息不足路由、证据循环都在此基础上加。

## 2026-08-17：信息不足条件路由

### 今天完成

- 学习 add_conditional_edges、路由函数和 path_map；
- 区分节点状态更新与路由控制；
- 区分原始草稿输入和严格 Pydantic 领域模型；
- 新增 inspect_request 和 request_clarification；
- 输入不完整时返回具体缺失字段和澄清问题；
- 仓库证据为空时进入澄清分支；
- 保持路由函数确定、轻量且不调用 LLM；
- 完成输入不足、证据不足和正常规划三条整图测试；
- 全量测试 40 个全部通过。

### 核心认识

节点负责产生状态，路由函数只根据状态选择下一步。同一源节点
不应同时使用固定边和条件边。需要澄清的信息不是系统错误，
因此使用独立的 missing_fields 和 clarification_questions 保存。

---

## 2026-08-18：有限证据补充循环

### 今天的目标

学习 LangGraph 循环、递归上限、证据读取预算和停止条件，
让工作流在仓库证据不足时最多补读两个候选文件，
并在证据充分或达到限制时可预测地结束，不出现无限循环或无目的仓库读取。

### 今天完成

* 为 `AgentState` 增加 `max_steps`、`evidence_budget`、
  `evidence_candidates`、`read_evidence_files` 和
  `evidence_stop_reason`；
* 在 `create_initial_state()` 中设置 `max_steps=2` 和
  `EvidenceBudget(max_files=2)`；
* 证明每次运行都会创建独立的预算与列表对象，
  不会在多个 State 之间共享可变数据；
* 让 `collect_evidence` 返回排序后且去重的候选文件路径；
* 新增 `read_more_evidence` 节点，每轮只补读一个未尝试候选文件；
* 使用 `dataclasses.replace()` 复制 `EvidenceBudget`，
  避免原地修改旧 State 中的可变对象；
* 将“路径匹配证据”和“真实源码内容证据”分开，
  只有非空 `RepositoryEvidence.snippet` 才能进入路线生成分支；
* 将 `route_after_evidence` 升级为
  `enough_evidence` / `read_more` / `stop` 三分支路由；
* 新增 `conservative_evidence_stop` 节点，
  明确返回停止原因、缺少的证据以及用户可补充的定位信息；
* 将两个新节点接入 LangGraph，形成可终止的证据补充循环；
* 在生产工作流入口设置 `recursion_limit=20`，
  作为图整体执行的第二层安全熔断；
* 更新 README 中的 V0.6 工作流、运行时状态、
  测试覆盖和后续计划；
* 完整测试集共 52 个测试，全部通过。

### 1. LangGraph 有限循环

本次循环不是用 Python `while` 实现，
而是让补读节点执行后再次进入条件路由：

```text
collect_evidence
→ route_after_evidence
  ├─ enough_evidence → generate_roadmap → END
  ├─ read_more → read_more_evidence ─┐
  │                                  └→ route_after_evidence
  └─ stop → conservative_evidence_stop → END
```

每次 `read_more_evidence` 只处理一个候选文件，
然后把最新 State 交给路由函数。
路由函数根据证据、步数、预算和未读候选文件决定是否继续。

### 2. 循环状态的职责划分

* `step_count`：已经发起的补读尝试数，文件读取失败也要计数；
* `max_steps`：业务允许的最大补读次数，当前固定为 2；
* `evidence_budget`：限制成功进入 State 的文件数和字符数；
* `evidence_candidates`：排序后可供补读的候选文件；
* `read_evidence_files`：记录已尝试文件，防止重复读取；
* `evidence_stop_reason`：把预算、步数或候选文件耗尽的原因
  传递给保守停止节点。

`step_count` 和 `EvidenceBudget` 的意义不同。
读取失败会增加 `step_count`，但不消耗成功读取预算；
读取成功并将内容加入 State 时才更新 `EvidenceBudget`。

### 3. 路由判断顺序

`route_after_evidence` 必须按以下顺序判断：

1. 是否已经获得非空内容证据；
2. `step_count` 是否已达到 `max_steps`；
3. `EvidenceBudget` 是否已经停止；
4. 是否仍有尚未读取的候选文件；
5. 以上条件都不满足时继续补读。

成功条件必须优先于停止条件。
例如第二次补读成功时，`step_count == max_steps == 2`，
但因为已经获得内容证据，应该进入 `generate_roadmap`，
而不是被次数上限提前截断。

### 4. 业务停止与运行时熔断

* `max_steps=2` 是正常业务逻辑，
  达到后会进入 `conservative_evidence_stop`，
  以结构化状态说明为什么停止；
* `recursion_limit=20` 是 LangGraph 整图的异常熔断，
  用于防止图结构错误造成的意外循环，
  不应用它代替业务层的停止分支。

一句话：`max_steps` 负责“正常地停”，
`recursion_limit` 负责“异常时强制熔断”。

### 5. 今天踩的坑

* `state.get("repo_evidence") or []` 执行后一定是列表，
  不能再用 `is not None` 作为证据充分条件；
* 应该判断派生出来的业务条件 `has_content_evidence`，
  而不是只判断容器是否存在；
* 判断补读上限要使用 `>=`，而不是 `==`，
  避免异常状态超过上限后反而继续循环；
* 候选文件是否耗尽应判断 `has_unread_candidate`，
  而不是判断 `candidates is None`；
* 可变的 `EvidenceBudget` 不能直接在 State 原对象上修改；
* 失败读取也必须增加 `step_count`，
  否则连续失败可能使图永远无法达到停止条件；
* 停止原因本身已经带句号时，
  组装问题文本不要再额外添加句号。

### 6. 测试与验收

今天新增或扩展的测试覆盖：

* 初始状态中的有限循环默认值；
* 两个工作流不共享预算和可变列表；
* 候选文件生成、去重与顺序；
* 每次只补读一个文件；
* 跳过已尝试的候选文件；
* 旧的 `EvidenceBudget` 对象不被原地修改；
* 证据充分、继续补读和保守停止三条路由；
* 步数上限、预算停止和候选文件耗尽边界；
* 第二次获得有效证据时成功分支优先；
* 连续读取失败时最多尝试两个文件，
  第三个候选文件不会被读取；
* 第二次读取成功时会退出循环并生成 `LearningRoadmap`；
* 保守停止时会返回明确原因和仍然缺少的源码信息。

最终完整测试结果：

```text
52 passed in 2.72s
```

今日验收标准全部通过：

* 所有执行路径都能有限终止；
* 最多补读两个候选文件；
* 不会重复读取同一文件；
* 第二次补读成功时能正常生成路线；
* 达到上限时能说明停止原因与缺少的信息；
* 生产工作流配置了 LangGraph 运行时安全上限。

### 核心认识

有限循环不是“多跑几次节点”，
而是一套明确的状态机设计：

* 节点负责读取一个文件并产生局部 State 更新；
* 路由函数负责根据最新 State 选择下一步；
* 业务限制负责让正常流程可解释地结束；
* 运行时上限负责在图结构异常时熔断；
* 测试必须证明循环不仅能继续，还能在所有边界上结束。

### 下一步

* 在当前有限循环上学习 LangGraph 人工确认与中断恢复；
* 设计用户补充文件或模块信息后如何继续原工作流；
* 将路线生成结果进一步连接到测验、掌握度评估和重新规划闭环。

---

## 2026-08-19：人工确认与短期记忆

### 今天的目标

学习 LangGraph Checkpointer、`thread_id`、`interrupt()` 和
`Command(resume=...)`，让 RepoMentor 在生成学习路线后暂停，
等待用户批准路线或修改目标/学习难度，再从同一会话继续执行。

今天的验收标准是：

* 相同 `thread_id` 可以从中断点恢复；
* 不同 `thread_id` 的会话互相隔离；
* 用户修改目标后，旧的派生状态失效，路线会根据新目标重新生成。

### 今天完成

* 编写并运行最小 `checkpoint_interrupt_demo.py`，验证暂停、恢复和会话隔离；
* 使用 `InMemorySaver` 编译 RepoMentor 自适应工作流；
* 新增 `RoadmapConfirmation` 严格模型，校验 `approve` 与 `revise` 输入；
* 为 `AgentState` 增加 `confirmation_status`、`human_confirmation`
  和 `revision_count`；
* 新增 `confirm_roadmap` 节点，在生成路线后调用 `interrupt()`；
* 新增 `apply_human_revision` 节点，合并修改、重建领域模型并清理失效状态；
* 新增 `route_after_confirmation`，在批准结束和修改重生成之间路由；
* 将工作流扩展为 10 个节点，并形成“生成—确认—修改—重生成”闭环；
* 新增 `make_thread_config()`，统一传递 `thread_id` 和递归上限；
* 新增 `start_adaptive_workflow()` 和 `resume_adaptive_workflow()`；
* 保留 `run_adaptive_workflow()` 作为自动批准路线的旧接口兼容入口；
* 完成同会话恢复、不同会话隔离和目标修改后重新生成三项整合测试；
* 完整测试集共 66 个测试，全部通过。

### 1. Checkpoint 保存的是什么

Checkpoint 不是只保存业务字段的普通字典，
而是保存工作流在某一时刻继续执行所需的运行上下文，包括：

* 当前 `AgentState`；
* 已经执行到哪个节点；
* 下一步待执行节点；
* 中断任务及其恢复位置；
* 当前会话的历史 checkpoint。

因此，恢复时不需要把 `topic`、`roadmap` 或暂停节点重新传给
`Command(resume=...)`。恢复命令只携带人工回复，
LangGraph 会使用 `thread_id` 查找之前保存的完整执行上下文。

### 2. thread_id 为什么不属于 AgentState

`AgentState` 保存 RepoMentor 的业务数据，
例如学习者画像、目标任务、仓库证据和学习路线。
`thread_id` 保存的是“这次调用属于哪个运行会话”的定位信息，
属于 LangGraph Checkpointer 的运行时配置。

本项目统一使用：

```python
{
    "configurable": {
        "thread_id": thread_id,
    },
    "recursion_limit": 20,
}
```

把 `thread_id` 放进 State 会让业务模型与存储基础设施耦合，
也不能替代 `configurable.thread_id` 对 Checkpointer 的定位作用。

### 3. interrupt 与 resume 的执行关系

当前工作流的成功路径变为：

```text
generate_roadmap
→ confirm_roadmap
  → interrupt(确认信息)
  → 保存 checkpoint 并返回 __interrupt__

同一个 app + 同一个 thread_id
→ Command(resume={"action": "approve" | "revise"})
→ confirm_roadmap 从 interrupt 位置继续
```

使用 `approve` 时，确认状态变为 `approved`，随后到达 `END`。
使用 `revise` 时，确认状态变为 `revision_requested`，
随后进入 `apply_human_revision` 并重新运行分析、证据收集和路线生成。

恢复时必须复用同一个编译后 `app`，因为当前的
`InMemorySaver` 绑定在该 app 使用的内存存储上。
重新调用 `build_adaptive_graph()` 会得到新的 Saver，
它找不到旧 app 中的中断记录。

### 4. 人工输入也必须严格校验

用户提交的确认决定属于外部输入，不能直接决定控制流。
`RoadmapConfirmation` 使用以下协议：

* `approve`：不能同时携带更新内容；
* `revise`：必须至少提供 `target_updates` 或 `learner_updates`；
* 非法 action 或额外字段由严格 Pydantic 模型拒绝。

`confirm_roadmap` 先把恢复数据转换为
`RoadmapConfirmation`，再写入 State。
`route_after_confirmation` 只读取已经校验过的
`confirmation_status`，因此路由函数仍然保持确定、轻量和可测试。

### 5. 修改目标后的状态失效边界

目标发生变化后，不能只修改 `target_input` 并保留旧路线。
旧目标产生的下游状态已经失去语义有效性。

`apply_human_revision` 会：

* 合并 `target_updates` / `learner_updates`；
* 重新构造 `TargetTask` 和 `LearnerProfile`，再次执行严格校验；
* 清空 `target_analysis`、`learner_analysis` 和旧 `roadmap`；
* 使用 `Overwrite([])` 真正替换带 reducer 的旧证据和错误列表；
* 重置补读次数、证据预算、候选文件、已读文件和停止原因；
* 清理上一轮澄清问题；
* 增加 `revision_count`；
* 保留仓库未变化时仍然有效的 `repository_path`、`repo_readme`
  和 `repo_tree`。

这里使用 `Overwrite([])` 很重要。
`repo_evidence` 和 `errors` 使用累积 reducer，普通空列表更新只会被追加，
不能清除旧值；`Overwrite` 才表示用新值替换 reducer 的历史结果。

### 6. InMemorySaver 的适用边界

`InMemorySaver` 适合本地开发、单元测试和概念验证：

* 配置简单；
* 同一 Python 进程内可以暂停和恢复；
* 可以快速验证多个 `thread_id` 的隔离行为。

它不是生产持久化方案。Python 进程关闭后，
所有 checkpoint 都会丢失，也无法让多个服务实例共享会话。
后续需要根据部署方式换成 SQLite 或 PostgreSQL Checkpointer。

### 7. 测试与验收

今天新增或扩展的测试覆盖：

* `RoadmapConfirmation` 的批准、修改和非法组合；
* 人工确认相关 State 默认值；
* `confirm_roadmap` 的中断载荷和恢复结果；
* `apply_human_revision` 对目标、学习者和失效状态的处理；
* `route_after_confirmation` 的批准、修改和非法状态；
* 编译后图包含 10 个节点和人工确认闭环；
* 相同 `thread_id` 能在批准后继续到 `END`；
* 同一个 app 中不同 `thread_id` 保留各自目标和中断点；
* 修改目标后生成器依次收到旧标题和新标题；
* 新路线携带修改后的 `TargetTask`，并再次进入确认中断；
* 第二次路线最终批准后，会话正常结束。

最终完整测试结果：

```text
66 passed in 3.33s
```

8 月 19 日的三项验收标准全部通过。

### 今天踩的坑

* 启用 Checkpointer 后，所有 `invoke()` 都必须提供
  `configurable.thread_id`；只测试 `get_graph()` 不会暴露这个问题；
* `13 deselected` 表示 `-k` 过滤了未选中的测试，不表示测试失败；
* 函数 docstring 必须是函数体中的第一条语句；
* 恢复时不能重新创建 app，否则新的 `InMemorySaver` 没有旧 checkpoint；
* 修改目标后不能继续使用旧的严格模型、分析结果、证据和路线；
* 带累积 reducer 的字段不能用普通空列表清空；
* `interrupt()` 所携带的数据应该能够 JSON 序列化；
* 测试文件中不能保留同名未完成测试，后定义的函数会覆盖前一个定义。

### 核心认识

HITL 不是在普通函数中临时调用一次 `input()`，
而是把“等待人类决定”建模为工作流中的可恢复状态：

* Checkpointer 保存执行上下文；
* `thread_id` 定位具体会话；
* `interrupt()` 暂停并向调用方暴露问题；
* `Command(resume=...)` 把人工决定送回原中断点；
* 严格模型保护人工输入边界；
* 状态失效规则保证修改后不会混用旧目标产生的结果；
* 自动化测试证明恢复、隔离和重新生成都符合预期。

### 下一步

* 基于确认后的路线生成测验题和源码实践任务；
* 设计回答记录与掌握度评估 State；
* 将掌握度变化连接到后续路线重规划；
* 在需要跨进程恢复时，将 `InMemorySaver` 替换为持久化 Checkpointer。

---

## 2026-08-20：V0.6 集成与图示

### 今天的目标

复习 State、Node、Edge、Conditional Edge、有限循环和 Checkpoint，
让流程图、正式代码、测试、设计决策和演示程序保持一致，
完成 V0.6 自适应工作流阶段验收。

### 今天完成

* 审核正式图中的 10 个业务节点和全部条件分支；
* 在 README 中用 Mermaid 绘制输入澄清、证据补读、
  保守停止和人工修订闭环；
* 新增 `docs/design-decisions.md`，记录采用单一状态图而不是
  自由式多 Agent 的原因、代价和重新评估条件；
* 将旧的 4 节点 `demo_adaptive_flow.py` 升级为正式 V0.6 演示；
* 演示程序改为调用 `build_adaptive_graph()`、
  `start_adaptive_workflow()` 和 `resume_adaptive_workflow()`；
* 将硬编码仓库绝对路径改为基于 `__file__` 的可移植路径；
* 为离线演示实现返回真实 `LearningRoadmap` 的契约一致 Fake；
* 验证直接批准路线的执行路径；
* 验证修改学习水平后重新生成、再次确认和最终批准的执行路径；
* 为 Checkpoint 配置自定义类型的精确 Msgpack 反序列化白名单；
* 在 `LANGGRAPH_STRICT_MSGPACK=true` 下验证中断恢复；
* 当日 V0.6 基线共 66 个测试，全部通过。

### 1. 图、代码与文档必须表达同一个状态机

Mermaid 图不是装饰性图片，而是工作流架构的一种可审查表达。
图中的每一条固定边或条件边都应该能在 `build_adaptive_graph()`
中找到对应代码。

```text
START
→ inspect_request
  ├─ needs_clarification → request_clarification → END
  └─ ready → analyze_learner → analyze_target → collect_evidence
```

证据分支包含 `enough_evidence`、`read_more` 和 `stop`；
确认分支包含 `approved` 和 `revision_requested`。
如果图中缺少补读自循环或修订后回到分析节点，
就不能真实表达 V0.6 的行为。

### 2. 为什么当前不使用自由式多 Agent

当前流程存在明确的数据依赖：学习者与目标分析先于证据选择，
证据先于路线，路线先于人工确认。
显式状态图能直接表达这些依赖，并让路由、停止条件和权限边界可测试。

自由式多 Agent 会引入更多模型规划、角色交接、上下文同步和随机决策，
但当前流程没有足够的独立并行任务来抵消这些成本。
因此本阶段选择一个共享 `AgentState` 的确定性图，
并记录未来在存在真正独立角色、不同工具或可并行任务时再重新评估。

### 3. 演示程序应该调用公开入口

旧演示重新组装了一个 4 节点图。正式图增加澄清、循环和 checkpoint 后，
旧演示仍能运行，却不能证明当前产品流程正确。

升级后的演示只替换 LLM 生成器，图结构、节点、路由和 Checkpointer
全部使用生产实现。这保证演示测试的确是当前系统，而不是另一份复制代码。

### 4. Fake 必须保持接口契约

真实生成节点返回 `LearningRoadmap`，下游确认节点需要调用
`roadmap.model_dump()`。因此离线 Fake 不能返回普通字符串，
而要构造完整的 `LearningRoadmap → DailyPlan → LearningTask
→ EvidenceSource` 嵌套模型。

Fake 可以省略真实网络调用和模型随机性，
但不能改变参数和返回类型，否则只能证明假流程能运行。

### 5. Checkpoint 反序列化白名单

严格模式验证发现 Checkpoint 中包含 RepoMentor 自定义 Pydantic 模型和
`EvidenceBudget`。默认宽松模式会恢复这些类型，但提示未来版本将阻止
未注册类型。

本项目使用 `JsonPlusSerializer(allowed_msgpack_modules=...)`
精确列出 State 中实际保存的类型，而不是设置为 `True` 允许任意模块。
这样既能恢复 checkpoint，又保持明确的反序列化安全边界。

### 测试与验收

两条交互式演示均通过：

```text
approve → approved → END
```

```text
revise → intermediate → revision_count=1
→ 重新生成 → 再次 interrupt → approve → END
```

严格 Msgpack 模式下不再出现未注册类型或阻止反序列化警告。
Mermaid、代码、README 和演示表达同一 10 节点工作流，
测试数量远高于计划要求的 10 个。V0.6 阶段验收完成。

### 核心认识

阶段集成不是简单把已有代码放在一起，
而是检查模型契约、图结构、文档、演示、安全配置和自动化测试
是否共同描述同一个系统。

---

## 2026-08-21：测验与任务模型

### 今天的目标

理解概念题、代码定位题和实践任务分别评估什么，
为 V0.7 定义可追溯、可校验的测验、任务、评估结果和掌握度模型。

### 今天完成

* 定义 `QuizQuestionType` 和 `AssessmentDifficulty`；
* 新增 `QuizQuestion`，支持概念题和代码定位题；
* 新增 `PracticeTask`，记录操作说明、交付物和完成标准；
* 新增 `EvaluationResult`，记录答案、评分方式、状态、得分和反馈；
* 新增 `MasteryProfile`，汇总知识点分数、优势、薄弱点和评估结果；
* 所有题目和实践任务都记录路线任务、仓库来源和知识点；
* 使用模型验证器保证得分、状态、评分方式和掌握度范围一致；
* 将 `AgentState.mastery` 从临时 `dict` 升级为
  `MasteryProfile | None`；
* 初始状态使用 `mastery=None`，不伪造尚未产生的评估结果；
* 新增 11 个评估模型测试和 1 个 State 测试；
* 最终完整测试集共 78 个测试，全部通过。

### 1. 三类评估内容的边界

概念题要求学习者解释“是什么、为什么、如何工作”；
代码定位题要求指出真实文件、函数或类；
实践任务要求提交代码、测试、图示或说明文档等可检查产物。

前两者使用 `QuizQuestion`，通过 `question_type` 区分；
实践任务使用独立的 `PracticeTask`，因为它需要 `deliverable`、
`completion_criteria` 和人工复核信息，不能只依靠参考答案判断。

### 2. 来源可追溯性

`related_task_title` 把题目连接到当前学习路线，
`evidence_sources` 把题目连接到真实仓库文件，
`knowledge_points` 说明该题实际评估什么能力。

这三个字段共同防止生成与当前目标无关、仓库中不存在或无法解释来源的题目。
例如 Mermaid 实践任务关联
`src/repo_mentor/adaptive_workflow.py`，并记录
`StateGraph`、`Conditional Edge` 和 `Checkpoint` 知识点。

### 3. EvaluationResult 的一致性规则

单项结果支持 `rule`、`model` 和 `human` 三种评分方式，
并区分 `evaluated`、`needs_human_review` 和 `uncertain` 状态。

模型保证：

* 实际得分不能高于最高分；
* `evaluated` 必须提供实际得分；
* `needs_human_review` 必须使用 `human` 评分方式。

这些约束把业务规则放进数据边界，避免下游节点接收到互相矛盾的结果。

### 4. MasteryProfile 是聚合结果

`EvaluationResult` 表示一道题或一个实践任务的单次结果；
`MasteryProfile` 表示围绕当前目标聚合后的能力画像。

`knowledge_scores` 的每个值必须位于 0 到 1，
同一个 `item_id` 不能重复计入画像。
`overall_score` 不强制等于知识点简单平均值，
因为未来可能根据目标重要性使用不同权重。

### 5. None 与零分不是同一状态

初始 `mastery=None` 表示尚未产生任何评估证据；
`MasteryProfile(overall_score=0)` 表示已经评估并确认当前掌握度为零。
如果用空字典或零分画像表示“尚未评估”，
后续重新规划节点就无法区分缺少数据和真实薄弱。

### 测试与验收

新增测试证明：

* 概念题、代码定位题和实践任务都能序列化；
* 题目必须包含真实仓库来源和知识点；
* Mermaid 实践任务能保存交付物和完成条件；
* 非法分数和互相矛盾的评分状态会被拒绝；
* 掌握度范围和评估结果唯一性受到校验；
* 初始 State 不会创建虚假的掌握度画像。

最终全量结果：

```text
78 passed in 3.13s
```

8 月 21 日验收标准全部通过。

### 核心认识

评估模型不只是保存问题文本。
它需要同时表达评估对象、真实来源、知识点、参考标准、评分状态
和聚合关系，才能成为后续测验生成、答案评估与路线重规划的可靠输入。

### 下一步

* 根据确认后的 `LearningRoadmap` 和仓库证据生成测验与实践任务；
* 实现 `generate_assessment` 节点；
* 保证题目难度与学习者基础匹配；
* 为参考答案保留可审查的仓库来源。

---

## 2026-08-22：生成目标相关测验

### 今天的目标

学习如何利用当前学习任务、真实仓库证据片段和学习者基础，
生成难度合适、来源可追溯的概念题、代码定位题和实践任务，
并避免询问仓库中不存在或尚未读取的内容。

### 今天完成

* 新增 `AssessmentPackage`，一次封装一题概念题、一题代码定位题
  和一个实践任务；
* 校验三个项目的路线任务、难度和 ID 一致性；
* 为 `AgentState` 增加 `assessment`、`learner_answers` 和
  `evaluation_results`；
* 为新状态字段设置不共享的空字典和空列表默认值；
* 新增 `assessment_generator.py`；
* 实现路径标准化和学习者难度推断；
* 实现只选择任务相关内容证据的证据防火墙；
* 新增 `ASSESSMENT_PROMPT`，约束 LLM 只使用允许的路径和片段；
* 实现 `generate_structured_assessment()` 结构化 LLM 调用；
* 对 LLM 结果执行任务、难度、路径、excerpt 和定位答案后置校验；
* 新增 `generate_assessment` LangGraph 节点；
* 人工修改目标或难度时同步清理旧测验、答案和评估结果；
* 使用 Fake LLM 验证生成流程，不联网、不产生模型费用；
* 当日完成后全量测试达到 100 个，全部通过。

### 1. 测验生成是受约束转换

测验生成不是把整个仓库目录交给模型自由出题，
而是一个有输入和输出防火墙的转换过程：

```text
LearnerProfile
+ 当前 LearningTask
+ 与任务文件匹配的 RepositoryEvidence.snippet
                ↓
        结构化 LLM 生成
                ↓
任务、难度、路径、excerpt、定位答案后置校验
                ↓
        AssessmentPackage
```

确定性代码负责选择“模型允许看到什么”，
LLM 只负责在已批准上下文内组织题目和参考答案。

### 2. 路径证据不等于内容证据

`LearningTask.evidence_sources` 说明路线建议关注哪些文件，
但不能单独证明文件内部存在某个函数或行为。
只有仓库工具实际读取并写入 `RepositoryEvidence.snippet` 的内容，
才允许用于询问内部实现。

`select_assessment_evidence()` 同时要求：

* 文件路径被当前学习任务引用；
* `snippet` 去除空白后非空；
* 路径标准化后没有重复。

没有合格内容证据时明确抛出错误，不把不确定信息交给模型猜测。

### 3. 难度由规则确定

`infer_assessment_difficulty()` 从 `LearnerProfile.current_level`
映射 `beginner`、`intermediate` 和 `advanced`。
无法识别的描述保守回退到 `beginner`，
避免模型因为自由理解用户水平而生成过难题目。

难度既写入 Prompt，又在 LLM 返回后与 `AssessmentPackage.difficulty`
比较。Prompt 是指导，Python 后置校验才是强制边界。

### 4. AssessmentPackage 的集合级约束

单个 `QuizQuestion` 或 `PracticeTask` 合法，
不代表三者组合后仍然满足业务要求。
`AssessmentPackage` 进一步保证：

* 恰好两道问题；
* 同时包含 `concept` 和 `code_location`；
* 只有一个实践任务；
* 三项内容对应同一路线任务；
* 三项内容使用统一难度；
* 题目和实践 ID 不重复。

这个顶层容器也是 `with_structured_output()` 的正式输出 Schema。

### 5. 生成后的真实性校验

Pydantic 能证明返回值结构正确，但不能证明路径和 excerpt 真实。
`validate_assessment_against_context()` 使用实际输入证据再次检查：

* 评估包必须对应本次路线任务；
* 难度必须匹配本次学习者；
* 所有来源路径必须在允许集合内；
* excerpt 必须原样存在于真实 snippet；
* 实践任务必须进入人工复核；
* 代码定位题参考答案必须包含真实来源路径。

### 6. 节点职责

`generate_assessment` 节点只负责：

1. 确认已经存在 `LearningRoadmap`；
2. 选择当前版本的首个学习任务；
3. 把学习者、任务和证据交给生成器；
4. 返回 `{"assessment": assessment}`。

节点没有复制 Prompt、证据筛选或结果校验逻辑，
因此生成器可以独立测试和复用。

### 测试与验收

新增测试覆盖：

* 三种学习者水平和未知水平回退；
* Windows/Unix 路径统一；
* 忽略路径证据、无关文件和重复文件；
* 没有内容证据时停止；
* 评估包题型、任务和难度组合；
* Fake LLM 只收到筛选后的片段；
* 未授权文件、虚构 excerpt 和错误难度被拒绝；
* 实践任务必须人工复核；
* 节点选择路线首个任务；
* 修改目标后旧评估状态全部失效。

8 月 22 日验收标准全部通过：题目不依赖仓库外内容，
难度与学习者匹配，参考答案和所有项目均保留真实来源。

### 核心认识

减少测验幻觉不能只依赖一句“不得编造”的 Prompt。
可靠方案是输入最小化、结构化输出、上下文后置校验和离线边界测试共同工作。

---

## 2026-08-23：回答评估器

### 今天的目标

学习规则评分、模型评分和人工复核各自适合什么任务，
实现 `evaluate_answers`，让评分理由具体，
并在模型不确定或输出异常时避免产生虚假高分。

### 今天完成

* 为 `PracticeTask` 增加 `max_score`；
* 新增 `assessment_evaluator.py`；
* 实现代码定位题的完整路径、文件名和错误路径规则评分；
* 实现实践任务人工复核结果；
* 新增 `ConceptEvaluationDraft` 受限模型评分草稿；
* 新增 `CONCEPT_EVALUATION_PROMPT`；
* 实现概念题结构化 LLM 评分；
* 模型调用失败、解析失败、无效草稿和越界分数均降级为
  `uncertain + score=None`；
* 空概念题回答不调用 LLM，直接规则评分为零；
* 评分反馈组合已体现和仍缺少的关键点；
* 新增 `evaluate_answers` 节点，按项目类型分发三种评估方式；
* 未知题目 ID 和非字符串答案会在节点边界被拒绝；
* 完整测试集达到 115 个，全部通过。

### 1. 不同任务需要不同评估方式

```text
code_location → rule
concept       → model
practice      → human
```

代码定位题的目标是判断是否找到了允许的仓库路径，
规则比模型更稳定、便宜且可解释。
概念题允许不同措辞表达相同语义，需要模型比较关键点。
实践任务涉及真实代码、测试质量和完成标准，
仅凭一段“已经完成”的提交说明不能自动通过，因此进入人工复核。

### 2. 代码定位题规则评分

当前规则明确且可测试：

* 包含完整允许路径：获得满分；
* 只包含正确文件名：获得 60% 分数；
* 没有允许路径或文件名：零分。

反馈会写出匹配到的路径，或者列出应该定位的来源文件，
不会只返回“错误”或“部分正确”。

### 3. 为什么不让 LLM 直接返回 EvaluationResult

`item_id`、`evaluation_method`、`max_score`、`knowledge_points`
和 `source_files` 都来自题目本身，是系统权威字段，
不应交给模型重新填写。

LLM 只生成 `ConceptEvaluationDraft`：

* `status`；
* 建议 `score`；
* `feedback`；
* `matched_points`；
* `missing_points`。

Python 再使用原问题字段重建最终 `EvaluationResult`。
这避免模型篡改题目身份、最高分或来源。

### 4. 不确定不是低置信度高分

`ConceptEvaluationDraft` 强制：

```text
evaluated → score 必须存在
uncertain → score 必须为 None
```

模型调用失败、结构化解析失败、返回错误类型或得分超过题目上限时，
评估器都返回 `uncertain + score=None`。
下游不能把一个看似精确的高分误认为可靠掌握证据。

空回答是确定事实，不需要消耗 LLM 调用，直接获得零分。

### 5. 实践任务保持人工边界

无论学习者是否提交了文字说明，实践结果都使用：

```text
status = needs_human_review
evaluation_method = human
score = None
```

反馈会列出 `completion_criteria`，帮助人工检查真实产物，
而不是根据“我已经写完测试”自动给分。

### 6. evaluate_answers 节点

节点恢复并校验 `AssessmentPackage`，读取
`learner_answers[item_id]`，再按题型分发。
缺失答案使用空字符串交给评估器保守处理；
未知 ID 则直接报错，避免把旧测验或拼错 ID 的答案静默忽略。

结果顺序保持为两道问题加一个实践任务，统一写入
`evaluation_results`，供下一步掌握度画像更新使用。

### 测试与验收

新增测试证明：

* 完整路径、文件名和错误路径得到预期规则分数；
* 规则定位评估器拒绝概念题；
* 实践任务始终人工复核；
* 正常概念评分包含已体现和缺失的具体理由；
* 空回答跳过 LLM 并得到零分；
* 不确定草稿、解析失败和越界分数没有得分；
* `evaluate_answers` 将三类项目分发给正确评估器；
* 未知 ID 被拒绝；
* 缺失答案按空回答处理。

最终全量结果：

```text
115 passed in 3.46s
```

8 月 23 日验收标准全部通过。

### 当前边界

`generate_assessment` 和 `evaluate_answers` 已作为独立节点实现，
但尚未接入 V0.6 主图。原因是答案提交需要新的 interrupt/resume 协议，
而后续还需要 `update_profile` 和 mastery-driven replan。
当前先保证每个组件独立正确，再组装完整 V0.7 闭环。

### 下一步

* 根据 `evaluation_results` 更新 `MasteryProfile`；
* 区分用户自述技能和实际评估证据；
* 让薄弱点可追溯到具体题目和源码；
* 再根据掌握度阈值进行自适应重新规划。

---

## 2026-08-24：更新学习者画像

### 今天的目标

理解“用户自述能力”和“评估证据证明的掌握度”之间的区别，
并根据 `EvaluationResult` 更新 `mastered_skills`、`weak_points`、
`completed_tasks`、`confidence` 和可追溯的知识点证据。

### 今天完成

* 新增 `KnowledgeMasteryStatus`，区分 `mastered`、`developing` 和 `weak`；
* 新增 `KnowledgeMasteryEvidence`，保存知识点分数、掌握状态、
  评估项目 ID 和真实源码文件；
* 扩展 `MasteryProfile`，增加 `mastered_skills`、`completed_tasks`、
  `confidence` 和 `knowledge_evidence`；
* 新增 `mastery_updater.py`，将可靠评估结果汇总为掌握度画像；
* 实现 `update_profile` LangGraph 节点，在节点边界恢复严格模型；
* 保留 `uncertain` 和 `needs_human_review` 结果用于解释，
  但不让它们产生虚假分数或已掌握结论；
* 为阈值、可靠结果筛选、重复 ID、无可靠结果和节点输入输出
  增加自动化测试。

### 1. 自述能力不等于已掌握

`LearnerProfile.known_skills` 表示用户对自己的初始描述，
它可以影响路线难度和解释方式，但不能直接写入
`MasteryProfile.mastered_skills`。

已掌握结论必须来自实际评估证据：

```text
用户自述 known_skills
        ≠
评估证据确认 mastered_skills
```

这个区分防止 Agent 因为用户说“我会 LangGraph”，
就跳过必要的评估和复习。

### 2. 只有可靠结果参与计算

`normalized_result_score()` 只接受：

```text
status == "evaluated"
且 score 不是 None
```

然后使用 `score / max_score` 将不同满分的项目统一到 0 至 1。
`uncertain` 表示系统无法可靠判断，
`needs_human_review` 表示还在等待人工结论；
二者都不应被当作零分，也不应被当作完成。

### 3. 知识点掌握度阈值

同一知识点可能被多道题评估。
系统先汇总该知识点的可靠归一化得分，再计算平均值：

```text
score >= 0.80        → mastered
0.60 <= score < 0.80 → developing
score < 0.60         → weak
```

这组阈值同时被 8 月 25 日的重规划使用，
因此定义在 `mastery_updater.py` 中作为唯一事实来源，
避免不同模块使用不一致的分数边界。

### 4. 薄弱点必须可追溯

只返回 `weak_points=["条件路由"]` 还不够，
因为用户无法知道这个结论从哪里来。
`KnowledgeMasteryEvidence` 进一步保存：

* 哪些 `assessment_item_ids` 支持结论；
* 这些评估项目来自哪些 `source_files`；
* 知识点的归一化得分和状态。

因此后续补练或复习任务能够重新引用真实源码，
而不是根据一个抽象标签自由生成。

### 5. confidence 表示证据覆盖度

`confidence` 不是 LLM 自己声明的主观信心，
而是一个确定性比例：

```text
可靠评分项目数 / 所有评估项目数
```

当实践任务还在等待人工复核时，
即使已有部分题目得分，`confidence` 也不会是 1.0。

### 6. update_profile 节点的边界

`update_profile` 只负责：

1. 确认 State 中存在评估结果和 `TargetTask`；
2. 把 checkpoint 恢复后可能出现的 dict 重新校验为 `EvaluationResult`；
3. 调用纯函数 `build_mastery_profile()`；
4. 只返回 `{"mastery": mastery}`。

节点不覆盖 `learner_profile`，
因此用户的初始自述与系统的证据画像可以并存。

### 测试与验收

测试覆盖：

* 0.80 和 0.60 阈值；
* 用户自述不会覆盖低分证据；
* `uncertain` 和待人工复核结果不参与得分；
* 薄弱点保留题目 ID 和源码路径；
* 无可靠得分时保守产生 0 分和 0 覆盖度；
* 重复评估 ID 被拒绝；
* `update_profile` 能恢复 dict 结果并保持节点单一职责。

8 月 24 日的针对性测试全部通过，
验收标准“自述不等于掌握，薄弱点可追溯”已满足。

### 核心认识

学习者画像不是一份可以被 Agent 随意改写的标签列表，
而是一个由可靠评估、真实源码和确定性规则共同支持的证据模型。

---

## 2026-08-25：自适应重新规划

### 今天的目标

理解 Reflection 节点与分数阈值路由，
根据掌握度选择进入下一模块、增加针对性实践、增加复习或保守停止，
并使用最多一次重规划的硬上限防止无限循环。

### 今天完成

* 新增 `ReplanAction` 和严格模型 `ReplanDecision`；
* 为 `AgentState` 增加 `replan_decision`、`supplemental_tasks`、
  `replan_count` 和 `max_replans`；
* 在 `create_initial_state()` 中设置 `max_replans=1` 和独立空列表；
* 新增 `mastery_replanner.py`，实现确定性分数分段决策；
* 实现 `select_focus_evidence_for_replan()`，保持焦点优先级并拒绝无证据知识点；
* 实现 `build_supplemental_task()`，生成可追溯的补练或复习任务；
* 新增 `reflect_on_mastery` 和 `apply_mastery_replan` 节点；
* 新增四分支 `route_after_mastery`；
* 为新增状态类型补充 checkpoint Msgpack 精确白名单；
* 完整测试集达到 157 个，全部通过。

### 1. Reflection 是决策，不是执行

`reflect_on_mastery` 读取 `MasteryProfile`、`replan_count` 和
`max_replans`，返回 `ReplanDecision`。
它不直接创建任务，也不提前增加重规划次数。

```text
MasteryProfile
      ↓
reflect_on_mastery
      ↓
ReplanDecision
      ↓
route_after_mastery
```

`apply_mastery_replan` 只处理 `add_practice` 和 `add_review`，
在真正追加一项 `LearningTask` 后才把 `replan_count` 增加 1。
这样可以区分“已经作出决定”和“已经完成重规划”。

### 2. 三个分数区间

```text
overall_score >= 0.80        → advance
0.60 <= overall_score < 0.80 → add_practice
overall_score < 0.60         → add_review
```

0.80 和 0.60 是必须单独测试的边界值：

* 0.80 已进入 `advance`；
* 0.79 仍属于 `add_practice`；
* 0.60 已进入 `add_practice`；
* 0.59 属于 `add_review`。

### 3. 判断顺序是业务语义的一部分

`advance` 必须在次数上限之前判断。
例如：

```text
score = 0.80
replan_count = 1
max_replans = 1
```

正确结果是 `advance`，不是 `stop`。
因为次数上限只限制再次追加补充任务，
不能阻止已经达标的学习者前进。

如果先判断 `replan_count >= max_replans`，
就会错误地把已达标的学习者留在当前模块。

### 4. 补充任务必须对应薄弱点

`ReplanDecision.focus_points` 不只是显示文本，
它是补充任务的强制输入。
`select_focus_evidence_for_replan()` 会：

1. 把 `knowledge_evidence` 转换为知识点到证据的映射；
2. 检查每个 `focus_point` 是否存在证据；
3. 按 `focus_points` 的原始优先级顺序返回证据。

如果一个知识点找不到对应证据，
系统会抛出错误，不会为它猜测学习任务。

### 5. 从证据构建 LearningTask

`build_supplemental_task()` 仅允许处理：

```text
add_practice
add_review
```

`advance` 和 `stop` 不需要补充任务，传入时会被拒绝。
函数会收集焦点证据的 `source_files`，
对重复路径去重，并在每个 `EvidenceSource.reason` 中记录
该文件支持的知识点。

任务的标题、目标、阅读要求、代码定位要求、实践内容和完成标准
都显式包含 `focus_points`，使“新增任务与薄弱点对应”可以自动化验证。

### 6. 有界重规划防止无限循环

`create_initial_state()` 默认设置：

```text
replan_count = 0
max_replans = 1
```

第一次追加补练或复习任务后，
`apply_mastery_replan` 返回 `replan_count=1`。
如果下次分数仍未达 0.80，Reflection 会返回 `stop`，
而不是再次生成任务。

这是业务级循环上限。LangGraph 的 `recursion_limit`
仍然作为整个图的最后运行时熔断保险，两者职责不同。

### 7. 为什么尚未接入 V0.6 主图

当前主图在 `confirm_roadmap` 批准后到达 `END`。
V0.7 已经有：

```text
generate_assessment
→ evaluate_answers
→ update_profile
→ reflect_on_mastery
→ route_after_mastery
```

但还没有“展示评估、收集 learner_answers、使用同一 thread_id 恢复”
的中断节点。如果现在强行连边，`evaluate_answers`
只能收到空答案，这不是完整的学习闭环。

因此当前完成的是可独立测试和复用的节点、纯函数与路由，
待答案提交协议完成后再一次性接入正式图。

### 测试与验收

自动化测试验证：

* 0.80、0.79、0.60 和 0.59 进入正确分支；
* 中间分数段选择 `developing` 和 `weak` 知识点；
* 低分段优先选择 `weak` 知识点；
* 缺少可追溯知识点证据时保守停止；
* 补充任务保留焦点顺序、证据路径和完成标准；
* 重复源文件不会生成重复 `EvidenceSource`；
* `advance` 不会被转换为补充任务；
* Reflection 节点不提前增加次数；
* 应用节点保留已有补充任务，每次只追加一项；
* 四种 `ReplanDecision.action` 都返回正确路由键。

最终完整测试结果：

```text
157 passed in 4.12s
```

8 月 25 日验收标准全部通过：
三个分数区间路由正确，新增任务与薄弱点和源码证据对应，
且最多只重新规划一次。

### 核心认识

可靠的自适应 Agent 不是让 LLM 随意决定“再学什么”，
而是先用评估证据形成掌握度，再用可测试的阈值和循环上限做决策，
最后只允许任务引用决策焦点对应的真实仓库证据。

---

## 2026-08-26：SQLite 学习进度持久化

### 今天的目标

学习 SQLite、主键、外键、唯一约束、时间戳和最小表设计，
让 RepoMentor 在 Python 进程结束后仍能恢复路线、薄弱点、补充任务和评估结果。

### 今天完成

* 新增 `progress_store.py`；
* 使用 Python 内置 `sqlite3`，无需增加第三方依赖；
* 首次构造 `SQLiteProgressStore` 时自动创建数据库目录和表；
* 建立 `repositories`、`learner_profiles`、`plans`、`tasks`、
  `assessment_results` 五张业务表；
* 使用规范化仓库路径和唯一约束实现幂等注册；
* 对 Windows 路径执行 `casefold()`，避免大小写不同产生重复仓库；
* 每个 SQLite 连接都显式开启外键；
* 使用会话上下文保证连接被关闭，使用 Connection 上下文
  保证事务提交或回滚；
* 使用参数化 SQL，不将用户路径拼接进查询字符串；
* 将 Pydantic 模型保存为 JSON，同时保留可查询的仓库 ID、顺序、
  任务类型和时间戳列；
* 数据库文件加入 `.gitignore`；
* 9 个持久化测试和当时全部 166 个测试通过。

### 1. AgentState、Checkpointer 和 SQLite 的区别

```text
AgentState
    当前图执行中的业务数据

InMemorySaver
    根据 thread_id 恢复暂停位置和当前 State

SQLiteProgressStore
    跨 Python 进程保存已完成的长期学习进度
```

`thread_id` 是运行会话定位键，`repository_id` 是长期业务数据隔离键。
它们职责不同，不应互相替代，也不需要都写入 `AgentState`。

### 2. 为什么同时使用关系列和 JSON

如果把整个 State 直接保存成一大段 JSON，
恢复很方便，但无法简单查询某个仓库、某类任务或某道评估结果。
如果把每个 Pydantic 字段都拆成数据库列，Schema 会变得很大，
模型字段变更时迁移成本也很高。

当前方案将关联和查询需要的字段放在普通列，
将完整领域模型放在 JSON 列，并在加载时再次执行
`model_validate()`。这同时保留了查询能力和领域模型边界。

### 3. 仓库隔离

`repositories.canonical_path` 具有唯一约束。
相同规范路径使用 `ON CONFLICT ... DO UPDATE`，因此重复注册
仍返回同一 `repository_id`。学习者、路线、任务和评估都通过外键
间接归属到该仓库，因此加载仓库 A 时不会返回仓库 B 的路线。

### 4. 事务与回滚

`learner_profiles`、`plans`、`tasks` 和 `assessment_results`
在同一 Connection 事务中写入。
测试故意提交两条相同 `item_id` 的评估结果，
触发唯一约束错误。事务回滚后，不会残留孤立的 plan 或 task。

### 5. 重启恢复验收

测试先使用一个 `SQLiteProgressStore` 保存进度，
再用同一数据库路径创建全新 Store 对象，最后验证：

* `LearningRoadmap` 恢复为严格模型；
* `MasteryProfile.weak_points` 保持不变；
* `ReplanDecision` 可恢复；
* 补充任务顺序保持不变；
* 评估结果可追溯到原题目和源码。

8 月 26 日验收标准全部通过。

### 核心认识

Checkpoint 是“运行恢复”，SQLite 学习进度是“业务恢复”。
生产级 Agent 通常同时需要两者。

---

## 2026-08-27：V0.7 学习闭环验收

### 今天的目标

完成一次“规划→学习→测验→评估→画像更新→重新规划”的
端到端演示，记录初始路线和低分评估后的任务调整，
并解释这为什么不是一次普通 Prompt。

### 今天完成

* 新增 `AssessmentSubmission`，约束 interrupt 恢复时的答案结构；
* 新增 `collect_learner_answers` 节点，展示评估包并暂停图；
* 新增 `resume_mastery_workflow()`，使用同一 `thread_id` 提交答案；
* `build_adaptive_graph()` 新增 `enable_mastery_loop` 可选参数；
* 默认仍保持 V0.6 批准后结束的兼容行为；
* 启用 V0.7 时注册并连接 6 个评估与掌握度节点；
* 新增同一 `thread_id` 两次恢复的端到端测试；
* 新增 `demo_mastery_loop.py` 离线演示；
* 演示将最终进度写入 SQLite，再用新 Store 对象恢复；
* 实际演示产生 0.2 掌握度、两个薄弱点和一项复习任务；
* 完整测试集达到 171 个，全部通过。

### 1. 答案提交也是 Human-in-the-loop

路线确认不是唯一需要 `interrupt()` 的地方。
生成测验后，工作流必须离开 Python 执行流，等待学习者思考和提交答案。

`collect_learner_answers` 首次运行时返回：

```text
kind = assessment_submission
assessment = 结构化评估包
expected_item_ids = 两道题 + 一个实践任务
```

调用方用相同 `thread_id` 和 `Command(resume={"answers": ...})`
恢复后，`interrupt()` 才将提交值返回节点。
`AssessmentSubmission` 先校验数据结构，`evaluate_answers`
再结合当前 `AssessmentPackage` 拒绝未知题目 ID。

### 2. 为什么 V0.7 是可选图模式

原有 `run_adaptive_workflow()` 和 V0.6 演示的契约是：
路线批准后到达 `END` 并返回 `LearningRoadmap`。
如果直接将批准分支改为答案中断，所有旧调用都会多出一次暂停。

因此新增：

```python
build_adaptive_graph(enable_mastery_loop=True)
```

默认值为 `False`，保持 V0.6 兼容；显式启用时才接入 V0.7 节点。

### 3. 完整节点接力

```text
inspect_request
→ analyze_learner
→ analyze_target
→ collect_evidence
→ generate_roadmap
→ confirm_roadmap (interrupt 1)
→ generate_assessment
→ collect_learner_answers (interrupt 2)
→ evaluate_answers
→ update_profile
→ reflect_on_mastery
→ route_after_mastery
→ apply_mastery_replan / END
```

端到端测试使用同一 `thread_id` 先批准路线，再提交答案。
如果换用另一 `thread_id`，Checkpointer 就无法找到当前评估包和暂停节点。

### 4. 初始路线与评估后调整

离线演示的初始任务是：

```text
定位并解释目录树生成流程
```

演示回答只部分解释了证据流程，并提交了错误的文件定位。
两道可靠评分题目的归一化得分是 0.4 和 0.0，
实践任务仍待人工复核，因此总体掌握度为：

```text
(0.4 + 0.0) / 2 = 0.2
```

Reflection 进入 `add_review`，针对“证据流程”和“代码定位”
产生一项引用真实仓库文件的复习任务。

### 5. 为什么这不是一次普通 Prompt

一次普通 Prompt 通常是“输入文本→模型输出文本”。
RepoMentor V0.7 则包含：

* 跨节点的结构化 `AgentState`；
* 来自真实仓库文件的可追溯证据；
* 两次需要图外人类输入的 `interrupt/resume`；
* 规则、LLM 和人工复核的混合评估；
* 由 Python 确定性计算的掌握度和分数阈值；
* 有次数上限的条件路由；
* 事务化 SQLite 保存和跨进程恢复；
* 离线、可重复的端到端自动化测试。

LLM 只负责适合语义生成和语义判断的部分，
数据边界、证据权限、得分计算、路由和循环上限均由可测试代码控制。

### 测试与验收

新增测试覆盖：

* `collect_learner_answers` 的 payload、项目顺序和恢复结果；
* 缺少 `AssessmentPackage` 时拒绝进入答案中断；
* V0.7 可选图的 6 个新节点和完整连边；
* 同一 `thread_id` 两次恢复并最终到达 `END`；
* 低分结果产生两个可追溯薄弱点和一项复习任务；
* 演示最终进度写入 SQLite 后可以由新 Store 恢复。

最终全量结果：

```text
171 passed in 4.32s
```

8 月 27 日验收标准全部通过。

### 核心认识

Agent 的价值不在于把一个长 Prompt 分成多段，
而在于让状态、证据、人类决定、确定性规则、模型推理、条件路由和持久化
在可解释、可中断、可恢复和可测试的工作流中协作。

---

## 2026-08-28：V0.8 限定范围检索设计

### 今天的目标

理解代码检索在 RepoMentor 中是学习证据层，
而不是通用仓库聊天产品。
在写切块、Embedding 或向量数据库代码之前，
先定义文件准入范围、预算、隔离键、信任边界和明确不做项。

### 今天完成

* 新增 `docs/retrieval-scope.md`；
* 明确区分 Discovery、Index Admission、Retrieval 和 Context Assembly；
* 定义当前检索范围由 `repository_id`、`TargetTask`、
  当前 `LearningTask`、`evidence_sources` 和薄弱点共同构成；
* 只允许当前模块相关的 README、docs、Python、测试和配置文件；
* 复用现有仓库根目录、符号链接、敏感路径、二进制和单文件大小保护；
* 定义目录发现、当前模块索引和单次上下文三层预算；
* 定义 Markdown、Python、测试和配置文件的结构感知切块策略；
* 定义 `repository_id + module_scope_id` 强制命名空间；
* 将仓库文本定义为不可信证据，不将其中文字当作系统指令；
* 明确不做全仓批量索引、完整架构扫描、通用聊天和安全分析；
* 补充 10 个面试追问和一段 60 秒项目回答。

### 1. 扫描到不等于允许索引

现有目录树最多发现 200 个文件，
这仅说明这些路径在受限扫描中被看到。
索引准入还必须检查：

* 路径和符号链接是否在仓库内；
* 是否属于敏感、忽略、二进制或过大文件；
* 文件类型是否在当前允许列表中；
* 能否解释它与当前学习目标的关系；
* 是否超过当前模块索引预算。

因此一个文件可以“存在于目录树”，但仍然“不允许进入索引”。

### 2. 已索引不等于全部进入 LLM

当前模块索引是一个可检索的小型证据集，
单次问题只从中选择少量 Top-K 证据块。
检索结果还要受 `EvidenceBudget` 的文件数和字符数限制。

这样可以防止“向量数据库中有很多内容，所以每次都全部传给模型”的误区。

### 3. 检索范围必须跟随学习任务

通用仓库聊天通常从用户当前问题开始全库搜索。
RepoMentor 则从已经校验的 `TargetTask` 和当前 `LearningTask` 开始，
将路线已引用证据设为最高优先级，再用 README 引用和目标排序补充。

如果一个证据不能支持当前的阅读、代码定位、实践或评估，
它就不是当前模块的必要索引内容。

### 4. 限定范围是产品取舍，不是技术缺陷

限定检索会降低对任意仓库问题的召回率，
但 RepoMentor 的用户是正在学习具体模块的初学者。
引入一个看似相关但实际无关的文件，很容易让学习者偏离任务。

因此当前优先保证 Precision、可追溯性、安全和成本可控；
证据不足时显式说明并请求更具体的范围，不偷偷扩大成全仓搜索。

### 5. 安全分析不在当前能力边界内

限定学习检索可以回答“当前目标下找到了哪些证据”，
但无法证明“整个仓库不存在漏洞”。
安全审计需要高召回率扫描、调用图或数据流、专用规则、威胁模型和人工复核。

如果没有这些能力却宣称可以做安全分析，会带来危险的假阴性。

### 当日验收

`docs/retrieval-scope.md` 已明确：

* 检索范围与当前学习目标、路线任务和薄弱点的关系；
* 允许的 README、docs、Python、测试和配置文件范围；
* 现有和 V0.8 建议的大小、文件数和上下文预算；
* 仓库隔离、模块隔离和不可信文本边界；
* 明确不做全仓架构扫描和安全分析；
* 10 个可用于项目面试的问答。

8 月 28 日计划验收标准已满足。

### 核心认识

限定范围检索不是一个简化版的通用 RAG，
而是为学习任务定制的证据管道。
它的核心设计问题不是“用哪个向量数据库”，
而是“什么内容有权进入当前学习模块，为什么，最多多少，何时停止”。
