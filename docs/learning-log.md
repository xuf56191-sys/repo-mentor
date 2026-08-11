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


