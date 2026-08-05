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