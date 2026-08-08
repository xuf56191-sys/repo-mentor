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