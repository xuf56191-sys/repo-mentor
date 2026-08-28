# 记录做RepoMentor项目遇到的代码

项目介绍：「RepoMentor 是一个面向开源新人的自适应仓库学习 Agent。它解决的核心问题是：新手面对陌生仓库，不知道为了完成一个具体目标，下一步该读什么、学什么——普通仓库分析报告很难变成可执行的学习计划。输入是学习者画像、目标任务和仓库路径，输出是一份有真实源码证据支持的学习路线。

技术上，我用 LangGraph 搭了一套自适应工作流：共享状态管理、四个单一职责的节点，加上条件路由——证据不足时会自动请求澄清或补读，而不是硬编。整套系统有 52 个自动化测试，并且在三个真实仓库上做过验证。

我把『证据可信度』当成第一原则——所有推荐必须能追溯到真实源码，路径存在不等于内容已确认，模型宁可承认不知道，也不编造。」

## 一、JSON的一些功能

| 函数                       | 作用                                |
| -------------------------- | ----------------------------------- |
| `json.loads(字符串)`       | JSON 字符串 → Python dict/list      |
| `json.dumps(python对象)`   | Python dict/list → JSON 字符串      |
| `json.load(文件对象)`      | 读文件，文件里的 JSON → Python 对象 |
| `json.dump(python对象, f)` | Python 对象 → 写入到文件            |

`roadmap.model_dump(mode="json")` 其中`mode="json"`：把里面特殊类型自动转换成适合 JSON 输出的类型：比如日期、UUID，会转成字符串；普通 str/int 保持原样。

## 二、`pathlib.Path` 的这些功能：

`profile_name = profile_path.stem` 

`.stem` 是 Pathlib 的属性**，作用：拿到**文件名，去掉后缀。

`Path(...)` :把字符串转换成路径对象；

`path.expanduser()`: 展开用户目录，例如 ~；

`path.resolve()`: 转换成绝对路径；

`Path.relative_to(other)`: 计算**相对路径**，把绝对路径转成相对于某个根目录的路径。

`path.exists()`: 判断路径是否存在；
`path.is_dir()`: 判断路径是不是文件夹；
`.is_absolute()`:判断是不是绝对路径
`path.iterdir()`: 尝试访问文件夹；
`path.name`: 获取文件夹名称。
`Path.iterdir()`: 遍历文件夹下所有直接子项（文件 + 子文件夹），不递归深层
`Path.is_dir()`: 返回 True/False：判断这个路径是不是文件夹
`Path.is_file()`: 返回 True/False：判断这个路径是不是普通文件
`Path.is_symlink()`: 判断是不是软链接（符号链接）
`sorted()`: 对可迭代对象排序。` .iterdir() `返回的是生成器，本身无序，一般包一层`sorted()`做按文件名排序

`Path.stat()`:获取文件 / 文件夹的系统元信息（操作系统记录的信息）返回`os.stat_result` 对象，常用字段：

- `st.st_size`：**文件字节大小**（单位字节 bytes），判断文件是否为空
- `st.st_mtime`：最后修改时间戳
- `st.st_ctime`：创建时间

`Path.read_bytes()`:以二进制 bytes 形式读取整个文件内容,`.read_text()`：直接读成字符串 str，需要指定编码。`.read_bytes()`：读原始二进制 bytes，不做编码解析

`bytes.decode(encoding="utf‑8")`: 把**二进制 bytes → 转成字符串 str**

`read_bytes()`拿到的是二进制，想要变成人类可读文本，就要 decode 解码


三、dataclasses的作用

`dataclass` 是 Python 内置装饰器，用来快速写**存数据的类**，不用手写一堆 `__init__`、`__repr__`、`__eq__`。

和 Pydantic `BaseModel` 很像，但有区别。

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
    email: str | None = None

# 直接实例化
u = User(name="张三", age=24)
print(u.name)
print(u)   # 自动生成好看的打印 __repr__
u2 = User(name="张三", age=24)
print(u == u2) # 自动支持相等判断 __eq__
```

不加`@dataclass`你要手写：

```python
class User:
    def __init__(self,name:str,age:int,email:str|None=None):
        self.name = name
        self.age = age
        self.email = email
    def __repr__(self):
        ...
    def __eq__(self,other):
        ...
```

## 四、`try...except`语法

## `try … except OSError as error:`

捕获操作系统层面的错误：

可能触发 OSError 的情况：

1. 路径格式非法
2. 路径不存在
3. 权限不足，无法访问
4. 磁盘错误

`raise RepositoryPathError(...) from error`

- 把底层原始的 `OSError`，包装成你自己业务自定义异常 `RepositoryPathError`
- `from error`：**保留原始异常堆栈**，调试的时候既能看到你抛出的提示，也能看到底层系统真正报错原因。
- 如果不写 `from error`：只会看到你抛出的异常，丢失原始报错栈，不方便排查 bug。

## 五、`一些from...import`作用

1. `from __future__ import annotations`:
核心作用:
开启**延迟注解求值（postponed evaluation of annotations）**
简单说：**写类型注解的时候，类还没定义完成，也不会报错**。

2. `from typing import Any`:
Any：代表任意类型。
变量标记成Any，意味着可以是字符串、字典、对象、数字随便什么类型，类型检查不做限制。

3. `from langchain.tools import tool`
@tool 是LangChain 的装饰器，用来把普通 Python 函数包装成 Agent 可以调用的工具（Function‑Calling 工具）。

4. `from pydantic import BaseModel, ConfigDict, Field`:
这一套是做数据模型、参数校验，在 Agent 工具里非常常用：
- BaseModel：Pydantic 基础模型类，定义工具入参、结构化输出的数据模板。
- Field：给字段加规则（最小长度、描述文本、默认值，大模型读取的说明）。
- ConfigDict：模型配置，LangChain 工具、with_structured_output会用到，控制别名、额外字段是否允许等。

## 六、日志等级
日志级别不仅仅是文字标签，它们更像是“故障响应等级”和“数据开关”。在生产环境中，错误的级别定高了会导致告警轰炸（狼来了），定低了会导致问题被淹没。

日志分级标准（DEBUG < INFO < WARN < ERROR < FATAL）
1. DEBUG（调试）

    一句话定义：开发人员专属的“显微镜”。

    特征：记录最细粒度的系统运行信息，比如变量值、入参出参、中间状态。

    开关：生产环境默认关闭。如果打开，日志量会瞬间暴涨，且可能包含敏感信息（如用户Token、SQL参数）。

    对应场景：你提到的“打印模型传入的详细参数”。这类日志只在本地或测试环境排查疑难杂症时开启，上线后必须关掉。

2. INFO（信息）

    一句话定义：系统的“心电图”。

    特征：记录核心业务流程的关键节点和正常结果。它代表“系统按预期工作”。

    开关：生产环境默认开启，且长期保留。它用来回答“系统在干什么？”（如服务启动、请求开始、调用成功）。

    对应场景：“开始执行”和“正常执行完成”。这些是追踪业务流转的标记，只要业务正常，就该打 INFO，方便做监控大盘和链路追踪。

3. WARN（警告）

    一句话定义：系统的“黄灯”。

    特征：发生了非预期但可恢复的异常情况。系统自身有容错机制，业务最终没受损，但意味着存在隐患或降级处理。

    行动：通常不触发紧急告警，但需要运维或开发定期关注趋势。如果 WARN 频率突然飙升，预示着即将变成 ERROR。

    对应场景：“第一次失败准备重试”和“预算耗尽拒绝读取”。前者是临时故障通过重试自救；后者是触发了限流保护机制防止系统崩溃，虽然拒绝了，但保护了核心引擎，所以属于警告而非崩溃。

4. ERROR（错误）

    一句话定义：系统的“红灯”。

    特征：发生了不可恢复的错误，导致本次请求或功能彻底失败。业务受到了实质性影响（比如用户下单失败、支付中断）。

    行动：通常触发即时告警，需要人工立即介入排查。

    对应场景：“重试后依然失败”。容错机制耗尽了，最终结果失败了，这就是典型的业务功能性报错，必须立即处理。

5. FATAL（致命/严重）

    一句话定义：系统的“心脏骤停”。

    特征：发生了导致整个应用程序进程崩溃、无法继续服务的灾难性问题。比如核心依赖（数据库连接池）彻底断连，或内存溢出导致 JVM 退出。

    行动：最高级别告警，通常意味着需要立刻重启服务或回滚版本。

💡 实战口诀：如何给新场景定级？

如果你以后拿不准，可以问自己三个问题来快速定级：

    这行日志是给我（开发）临时看内部变量的吗？ → 是 = DEBUG

    这件事正常吗？ → 正常 = INFO（不管它多频繁）

    如果不正常，系统自己“兜住”了吗？

        自己兜住了（重试、降级、熔断） → WARN（虚惊一场，但值得留痕）

        没兜住，用户直接看到报错/失败 → ERROR（赶紧修）

特别注意：很多新人会把所有 try-catch 都打 ERROR，这是不对的。如果 catch 里做了重试并成功了，这应该打 WARN，而不是 ERROR。ERROR 必须对应“最终失败”。

`isinstance(object, classinfo)`:
- object：你要检查的那个对象（变量）。

- classinfo：你想要匹配的类型（可以是单个类型，也可以是多个类型组成的元组）。

- 返回值：匹配返回 True，否则返回 False。