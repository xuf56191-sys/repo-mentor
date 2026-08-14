# Case R1-A — RepoMentor 目录树扫描流程

## Target

理解 RepoMentor 的目录树扫描流程。

## Tool Calling

Round 1:

- `get_repo_tree`
- `rank_target_files`

Round 2:

- `read_repo_file`
- `read_repo_file`
- `read_repo_file`
- `read_repo_file`

Total Tool Calls:

`6`

## Ranked Files

1. `src/repo_mentor/repository_tree.py` - score=`9.0`
2. `src/repo_mentor/repository_service.py` - score=`7.0`
3. `tests/test_repository_ranker.py` - score=`5.5`
4. `tests/test_repository_tools.py` - score=`5.5`
5. `data/demo_repo/tree.txt` - score=`5.0`
6. `src/repo_mentor/repository_ranker.py` - score=`5.0`
7. `src/repo_mentor/repository_reader.py` - score=`5.0`
8. `src/repo_mentor/repository_tools.py` - score=`5.0`

## Files Actually Read

1. src/repo_mentor/repository_tree.py
- 7864 chars
2. src/repo_mentor/repository_service.py
 - 3479 chars
3.src/repo_mentor/repository_safeguards.py
- 11352 chars

模型还请求：

4. src/repo_mentor/repository_tools.py
原始结果约 9250 chars
因总字符预算超限，没有进入模型上下文

## Evidence Budget

max_files = 4
max_chars = 30000

最终状态：

used_files = 3 / 4
used_chars = 22695 / 30000
stopped = True

停止原因：

字符数超限：
已用 22695/30000，
本次试图读取 9250 个字符

这次实验说明 EvidenceBudget 已经真正参与 Tool Calling 控制，而不是只作为未使用的配置存在。

当第四个文件会使总字符数达到：

22695 + 9250 = 31945

超过：

30000

时，系统拒绝将该文件正文继续提供给模型，并停止后续自由 Tool Calling。

## Final Answer Evidence

模型最终基于实际进入上下文的：

repository_tree.py
repository_service.py
repository_safeguards.py

进行了总结。

回答覆盖了目标中的主要内容：

仓库路径规范化；
路径存在性和目录校验；
仓库可访问性检查；
默认忽略规则；
.env 特殊忽略逻辑；
最大扫描深度；
最大文件数量；
递归目录遍历；
权限和文件系统异常处理；
符号链接处理；
目录树文本生成；
TreeBuildResult 结果组装。

模型同时明确指出：

repository_tools.py 因预算超限未能进入模型上下文，如果需要继续理解 Tool 层如何调用 build_tree()，仍需读取该文件。

因此模型没有把未获得的 repository_tools.py 内容冒充为已经读取的真实证据。

## Manual Review

### Groundedness:`✅`

本次使用的主要证据文件均来自真实仓库路径：

- src/repo_mentor/repository_tree.py
- src/repo_mentor/repository_service.py
- src/repo_mentor/repository_safeguards.py

最终回答主要依据实际 read_repo_file 返回的仓库源码。

对于因为预算超限而没有进入模型上下文的：

src/repo_mentor/repository_tools.py

模型没有声称已经知道其具体实现，而是明确标记为证据缺口。

这符合 RepoMentor 的原则：

路径存在
≠
内容已经确认

人工复核时仍应打开 repository_tree.py 和 repository_service.py，确认回答中引用的 build_tree()、_walk_directory()、should_ignore()、validate_repository_path() 等函数真实存在。

### Relevance:`✅`

评价：核心文件高度相关，但存在明显噪声。

排序结果前两位：

`repository_tree.py`
`repository_service.py`

_与当前“目录树扫描流程”目标高度相关，说明 Ranker 能够优先识别真正关键的源码。

但是 Top-N 中还出现：

`tests/test_repository_ranker.py`
`tests/test_repository_tools.py`
`data/demo_repo/tree.txt`
`repository_ranker.py`
`repository_reader.py`
`repository_tools.py`

其中部分文件和当前目标的直接关系较弱。

特别是在第二轮 Tool Calling 中，模型读取了：

repository_safeguards.py

该文件主要负责 Tool 日志、重试、预算和安全保护，并不是理解：

路径校验
→ 目录遍历
→ 忽略规则
→ 目录树生成

所必需的核心证据。

因此本 Case 的核心目标相关文件识别正确，但仍存在额外弱相关文件进入读取阶段的问题。

### Sufficiency：✅

评价：现有核心证据足够回答目标。

虽然 repository_tools.py 因字符预算限制没有进入模型上下文，但当前目标是：

理解从仓库路径输入到目录树生成的完整流程。

实际读取的：

repository_service.py
+
repository_tree.py

已经覆盖：

路径规范化
↓
路径校验
↓
忽略规则
↓
递归遍历
↓
深度 / 文件数量限制
↓
目录树生成
↓
结果组装

因此对于当前目标而言，核心证据已经充分。

如果目标进一步变为：

理解 RepoMentor 的 get_repo_tree Tool 如何封装并调用目录树构建功能

那么 repository_tools.py 才会成为必要证据。

所以本次证据对于当前目标是充分的。

### Economy:` ⚠️`

评价：成功控制了范围，但存在一次明显的不必要读取。

第一轮：

get_repo_tree
+
rank_target_files

属于合理的证据定位行为。

第二轮真正必要的主要文件是：

repository_tree.py
repository_service.py

但模型额外读取：

repository_safeguards.py

消耗了：

11352 chars

这次额外读取占用了大量 EvidenceBudget。

因此当模型随后准备读取：

repository_tools.py

时：

22695 + 9250
= 31945
> 30000

触发了字符预算限制。

这说明当前 safeguards 能够有效阻止继续扩大上下文，但也暴露出 Tool Selection 的经济性问题：

模型虽然找到了正确核心证据，
但仍然会选择与当前目标关系较弱的大文件，
从而浪费有限的证据预算。

因此 Economy 评为：

⚠️

而不是 ✅。

## Problems Found

`Initial integration exposed inconsistent return fields in
run_target_tool_calling(); some early-return branches omitted
the EvidenceBudget object. The return contract was unified
before continuing the six-case evaluation.`

Problem 1 — Ranked Files 存在弱相关候选

虽然 repository_tree.py 和 repository_service.py 正确位于前两名，但后续 Top-N 中混入了多个与目录树扫描流程关系较弱的文件。

说明当前目标文件排序能够找到核心文件，但 Top-N 后半部分仍存在一定噪声。

Problem 2 — 模型读取了非必要的 repository_safeguards.py

repository_safeguards.py 与 Tool 执行安全有关，但并不是理解目录树构建流程所必需的核心源码。

该文件体积为：

11352 chars

占用了较大比例的字符预算。

这属于一次：

合理背景文件
但非当前目标必要证据

的读取。

Problem 3 — 非必要读取导致后续预算提前耗尽

由于已经读取 repository_safeguards.py，导致后续：

repository_tools.py

无法进入模型上下文。

这说明当前预算机制本身工作正常，但模型的证据选择顺序仍有优化空间。

后续可以考虑优化：

Tool description；
System Prompt；
ranker 的目标相关性权重；

让模型优先读取最直接服务目标的文件，再考虑辅助文件。

本 Case 暂不立即修改代码，应继续完成其他 5 个 Case，观察这一问题是否具有跨目标或跨仓库的共性。

## Conclusion

Pass with Issues
结论说明

本 Case 证明 RepoMentor V0.4 已经能够：

在真实仓库中生成目录结构；
根据具体目标找到高度相关的核心文件；
使用真实源码作为最终回答证据；
在多轮 Tool Calling 中逐步获取证据；
在字符预算超限时阻止继续扩大模型上下文；
在证据不足或文件未读取时明确说明证据缺口。

同时实验暴露出：

Top-N 后半部分存在弱相关候选；
模型可能读取合理但非必要的大文件；
非必要读取会浪费 EvidenceBudget，并影响后续真正需要的证据读取。

因此该 Case 总体通过，但存在证据经济性和工具选择效率问题，需要结合后续 R1-B、R2-A、R2-B、R3-A、R3-B 进一步判断是否属于共性问题。

# Case R1-B — RepoMentor 仓库工具如何被测试

## Target

理解 RepoMentor 的仓库工具 如何被测试

## Tool Calling

Round 1:

- `get_repo_tree`
- `get_onboarding_docs`

Round 2:

- `rank_target_files`
- `read_repo_file`
- `read_repo_file`

Total Tool Calls:

`5`

## Ranked Files

1. `tests/test_repository_ranker.py` - score=`11.0`
2. `tests/test_repository_tools.py` - score=`11.0`
3. `tests/test_target_tool_calling.py` - score=`11.0`
4. `src/repo_mentor/repository_tools.py` - score=`9.0`
5. `tests/test_repository_safeguards.py` - score=`8.0`
6. `pytest.ini` - score=`7.0`
7. `src/repo_mentor/repository_reader.py` - score=`7.0`
8. `src/repo_mentor/repository_ranker.py` - score=`5.0`

## Files Actually Read

1. src/repo_mentor/repository_tools.py
- 9250 chars
2. tests/test_repository_tools.py
 - 4051 chars




## Evidence Budget

max_files = 4
max_chars = 30000

最终状态：

used_files = 3 / 4
used_chars = 21289 / 30000
stopped = False

## Manual Review
Groundedness：✅
Relevance：✅
Sufficiency：✅
Economy：⚠️
### Groundedness：✅

**评价：通过。**

本次最终回答建立在实际读取的仓库文件之上。

模型通过 `read_repo_file` 实际读取了：

- `src/repo_mentor/repository_tools.py`
- `tests/test_repository_tools.py`

其中：

```text
repository_tools.py
→ 9250 chars

test_repository_tools.py
→ 4051 chars
```
### Relevance:`✅`

评价：通过，但 Ranked Files 中仍存在一定排序噪声。

当前目标是：

理解 RepoMentor 的仓库工具如何被测试，并找到核心 Tool 实现文件和对应测试文件。

模型最终实际选择并读取：

src/repo_mentor/repository_tools.py
tests/test_repository_tools.py

这两个文件与目标具有非常直接的对应关系：

repository_tools.py
→ Repository Tools 核心实现

test_repository_tools.py
→ Repository Tools 直接测试

因此真正进入模型上下文的核心证据具有较高目标相关性。

同时，本 Case 也说明目标变化后证据选择发生了明显变化。

### Sufficiency：✅

评价：现有核心证据足够回答目标。

当前目标要求回答两个主要问题：

Repository Tools 的核心实现在哪里、包含哪些能力；
测试文件如何验证这些 Tool 的主要行为。

实际读取的：

src/repo_mentor/repository_tools.py

能够提供 Tool 实现层证据。

实际读取的：

tests/test_repository_tools.py

能够提供直接的测试行为证据。

### Economy:` ⚠️`

评价：总体受控，但第一轮存在一次较明显的非必要证据读取。

本 Case 总共进行了：

5 次 Tool Call
2 个 Tool Calling Round

实际流程为：

Round 1
├── get_repo_tree
└── get_onboarding_docs

Round 2
├── rank_target_files
├── read repository_tools.py
└── read test_repository_tools.py

其中：

get_repo_tree

用于获得仓库整体结构，可以帮助模型判断实现文件和测试目录的位置，因此属于合理的仓库定位行为。

第二轮：

rank_target_files
read repository_tools.py
read test_repository_tools.py

也都直接服务于当前目标。

主要经济性问题出现在：

get_onboarding_docs
→ README.md
→ 7988 chars

当前目标已经非常具体：

找到 Repository Tools 的核心实现和对应测试。

对于这个目标而言，README 并不是完成分析所必需的核心证据。

此次 README 读取直接消耗：

1 / 4 files
7988 / 30000 chars

约占总字符预算的四分之一。

最终预算为：

used_files = 3 / 4
used_chars = 21289 / 30000
stopped = False

虽然没有触发预算限制，也没有影响后续核心文件读取，但如果仓库源码更大，这种提前读取 onboarding 文档的行为可能挤占真正重要源码和测试文件的证据预算。

因此本 Case 表明：

EvidenceBudget 能够保持总体范围受控

但：

模型仍存在“先读取一个合理但非必要文档”的行为

这与 R1-A 中出现的非必要文件读取现象具有一定相似性，值得继续观察后续 R2、R3 Case 是否也存在类似模式。

## Problems Found

`无`
## Conclusion

`PASS`

# Case R2-A — ItsDangerous 的数据签名与恢复流程

## Target

理解 ItsDangerous 的数据签名与恢复流程

## Tool Calling

Round 1:

- `get_repo_tree`
- `get_onboarding_docs`

Round 2:

- `rank_target_files`

Total Tool Calls:

`3`

## Ranked Files

1. docs/_static/itsdangerous-name.svg score=5.0
2. tests/test_itsdangerous/__init__.py score=2.5
3. tests/test_itsdangerous/test_encoding.py score=2.5
4. tests/test_itsdangerous/test_serializer.py score=2.5
5. tests/test_itsdangerous/test_signer.py score=2.5
6. tests/test_itsdangerous/test_timed.py score=2.5
7. tests/test_itsdangerous/test_url_safe.py score=2.5
8. docs/_static/itsdangerous-icon.svg score=2.0


## Evidence Budget

max_files = 4
max_chars = 30000

最终状态：

used_files = 3 / 4
used_chars = 7907/30000
stopped = False

## Manual Review

### Groundedness：⚠️

**评价：部分通过，但缺少核心源码级证据。**

本次运行获取了三类真实仓库证据：

- `get_repo_tree` 返回了真实仓库目录结构；
- `get_onboarding_docs` 实际读取了：
  - `README.md`
  - `pyproject.toml`
  - `docs/index.rst`
- `rank_target_files` 返回了基于真实仓库文件生成的候选列表。

因此，模型最终指出：

- `src/itsdangerous/signer.py`
- `src/itsdangerous/serializer.py`
- `src/itsdangerous/encoding.py`
- `src/itsdangerous/url_safe.py`
- `src/itsdangerous/timed.py`

等文件真实存在，这部分有仓库树作为依据。

但是，本 Case 没有执行任何：

```text
read_repo_file
```
### Relevance:`❌`

评价：不通过，目标相关文件排序明显失败。

当前目标是：

理解 RepoMentor 的仓库工具如何被测试，并找到核心 Tool 实现文件和对应测试文件。

模型最终实际选择并读取：

src/repo_mentor/repository_tools.py
tests/test_repository_tools.py

这两个文件与目标具有非常直接的对应关系：

repository_tools.py
→ Repository Tools 核心实现

test_repository_tools.py
→ Repository Tools 直接测试

因此真正进入模型上下文的核心证据具有较高目标相关性。

同时，本 Case 也说明目标变化后证据选择发生了明显变化。

### Sufficiency：❌

当前 expected outcome 是：

能够指出数据签名与反序列化验证相关的核心文件，并说明主要实现之间的关系。

本次实际上完成了第一部分的一部分：

从目录树和文档中识别出可能的核心文件

例如：

signer.py
serializer.py
encoding.py
url_safe.py
timed.py

但是没有完成最关键的第二部分：

读取真实核心源码
↓
确认函数 / 类
↓
确认调用关系
↓
用源码证据解释签名与恢复流程

整个 Case 中：

read_repo_file 调用次数 = 0

因此最终模型给出的：

Python对象
→ serializer.py
→ signer.py
→ encoding.py
→ token

更接近：

基于仓库结构和文档做出的高层推断

而不是：

经过核心源码验证后的实现关系

模型最终也明确承认：

如果需要深入理解实现关系，下一步应读取 signer.py 和 serializer.py 的源码内容。

这句话实际上已经说明：

当前证据还没有达到目标完成条件

### Economy:` ⚠️`

评价：Tool 调用数量不多，但有限证据预算的分配效率不理想。

证据预算的使用存在明显问题。

get_onboarding_docs 一次读取了：

README.md
pyproject.toml
docs/index.rst

共：

3 files
7907 chars

使 EvidenceBudget 立即变成：

used_files = 3 / 4

也就是说，在真正定位核心源码之前，4 个文件的预算已经使用了 3 个。

即使后续 Tool Calling 继续进行，也只剩：

1 个文件

可以进入模型上下文。

而当前目标实际上至少希望进一步验证：

signer.py
+
serializer.py

两个核心文件。

因此这里暴露出一个重要问题：

字符预算还很充足
但文件数量预算已经被 onboarding 文档提前占用

同时，当前 max_rounds = 2 也使问题更加明显：

Round 1
获取目录树 + onboarding

Round 2
进行 rank_target_files

↓
达到最大 Tool Calling 轮次

没有 Round 3
↓
无法继续 read_repo_file

因此，本次失败不仅仅来自 Ranker。

还暴露出了当前 Tool Calling 工作流的一个结构性限制：

“先了解仓库 → 再排序 → 再读源码”
实际上可能需要至少 3 轮决策

而当前：

max_rounds = 2

在部分外部仓库上可能不足。

所以本 Case 的 Economy 问题不是“调用太多”，而是：

有限 Tool Round
+
有限文件预算
没有优先分配给最关键源码证据

因此评为：

⚠️
## Problems Found

`无`
## Conclusion

`Fail`

# Case R2-B — 理解 ItsDangerous 的序列化功能如何被测试

## Target

理解 ItsDangerous 的序列化功能如何被测试

## Tool Calling

Round 1:

- `get_repo_tree`
- `get_onboarding_docs`

Round 2:

- `rank_target_files`

Total Tool Calls:

`3`

## Ranked Files

1. docs/_static/itsdangerous-name.svg score=5.0
2. tests/test_itsdangerous/__init__.py score=2.5
3. tests/test_itsdangerous/test_encoding.py score=2.5
4. tests/test_itsdangerous/test_serializer.py score=2.5
5. tests/test_itsdangerous/test_signer.py score=2.5
6. tests/test_itsdangerous/test_timed.py score=2.5
7. tests/test_itsdangerous/test_url_safe.py score=2.5
8. docs/_static/itsdangerous-icon.svg score=2.0


## Evidence Budget

max_files = 4
max_chars = 30000

最终状态：

used_files = 3 / 4
used_chars = 7907/30000
stopped = False

## Manual Review

### Groundedness：⚠️

**评价：部分通过，但没有获得源码和测试正文级证据。**

本 Case 实际执行并获得了以下真实仓库证据：

- `get_repo_tree`：获得真实仓库目录结构；
- `get_onboarding_docs`：实际读取：
  - `README.md`
  - `pyproject.toml`
  - `docs/index.rst`
- `rank_target_files`：基于真实仓库文件生成候选排序。

因此，最终回答中提到的：

- `src/itsdangerous/serializer.py`
- `src/itsdangerous/signer.py`
- `tests/test_itsdangerous/test_serializer.py`
- `tests/test_itsdangerous/test_signer.py`

都能够从真实仓库目录或候选文件中确认其路径存在。

但是，本次运行没有真正执行任何：

```text
read_repo_file
```
### Relevance:`⚠️`

评价：测试文件相关性有所改善，但核心实现文件仍然没有进入排序结果。



### Sufficiency：❌

评价：没有达到当前目标所需的证据充分性。

### Economy:` ⚠️`

评价：调用次数不多，但 Tool Round 和 EvidenceBudget 的分配仍然不合理。

## Problems Found

### Problem 1 — 测试文件识别明显优于核心实现文件识别

当目标明确包含“如何被测试”后，Ranker 能够将：

- `test_serializer.py`
- `test_signer.py`
- `test_encoding.py`

等测试文件排入 Top-N。

但对应的：

- `src/itsdangerous/serializer.py`
- `src/itsdangerous/signer.py`

仍没有进入 Top 8。

这说明当前 Ranker 对测试路径或“test”相关目标具有较强偏好，但在同一目标下关联“实现文件 + 对应测试文件”的能力仍然不足。

---

### Problem 2 — `max_rounds=2` 无法支持“发现 → 排序 → 阅读”三阶段流程

本 Case 实际出现：

```text
Round 1:
get_repo_tree
get_onboarding_docs

Round 2:
rank_target_files
```
### Problem 3 — Final Answer 出现伪 Tool Call 文本
### Problem 4 — Onboarding Tool 提前占用大部分文件预算


`无`
## Conclusion

`Fail`



# Case R3-A — 理解 Pipfile 的配置解析核心流程

## Target

理解 Pipfile 的配置解析核心流程

## Tool Calling

Round 1:

- `get_repo_tree`
- `get_onboarding_docs`

Round 2:

- `rank_target_files`

Total Tool Calls:

`3`

## Ranked Files

1. requirements.txt score=7.0
2. examples/Pipfile score=5.0
3. examples/Pipfile.lock score=5.0
4. README.rst score=2.5
5. examples/setup.py score=2.0
6. pipfile/__about__.py score=2.0
7. pipfile/__init__.py score=2.0
8. pipfile/api.py score=2.0


## Evidence Budget

max_files = 4
max_chars = 30000

最终状态：

used_files = 3 / 4
used_chars = 21747/30000
stopped = False


## Manual Review

### Groundedness：⚠️

**评价：部分通过，但仍缺少核心源码正文证据。**

本次运行真实获得了以下仓库证据：

- `get_repo_tree`：获得 Pipfile 仓库的真实目录结构；
- `get_onboarding_docs`：实际读取了：
  - `README.rst`
  - `requirements.txt`
  - `docs/index.rst`
- `rank_target_files`：基于真实仓库文件生成了候选文件排序。

因此，最终回答中指出：

```text
pipfile/api.py
pipfile/__init__.py
pipfile/__about__.py
```
### Relevance:`⚠️`

评价：核心文件最终进入候选，但排序质量明显较差。

### Sufficiency：❌

评价：没有取得完成“核心解析流程理解”所需的源码证据。

### Economy:` ⚠️`

评价：Tool 调用数量较少，但有限预算和轮次被低优先级证据大量占用。

## Problems Found

- Problem 1 — 核心实现文件能够被发现，但排序优先级过低
- Problem 2 — 外部仓库再次出现“两轮不足”
- Problem 3 — onboarding 文档消耗过多 EvidenceBudget
- Problem 4 — Ranker 对核心源码的排序问题跨不同仓库布局存在

## Conclusion

`Fail`

# Case R3-B — 理解 Pipfile 解析功能如何被测试

## Target

理解 Pipfile 解析功能如何被测试

## Tool Calling

Round 1:

- `get_repo_tree`
- `get_onboarding_docs`

Round 2:

- `rank_target_files`

Total Tool Calls:

`3`

## Ranked Files

1. requirements.txt score=7.0
2. tests/__init__.py score=6.0
3. tests/test_parser.py score=6.0
4. examples/Pipfile score=5.0
5. examples/Pipfile.lock score=5.0
6. examples/setup.py score=2.0
7. pipfile/__about__.py score=2.0
8. pipfile/__init__.py score=2.0

## Evidence Budget

max_files = 4
max_chars = 30000

最终状态：

used_files = 3 / 4
used_chars = 21747/30000
stopped = False


## Manual Review

### Groundedness：⚠️

**评价：部分通过，但缺少实现文件和测试文件的正文级证据。**

本次运行真实获取了以下仓库证据：

- `get_repo_tree`：获得 Pipfile 仓库真实目录结构；
- `get_onboarding_docs`：实际读取：
  - `README.rst`
  - `requirements.txt`
  - `docs/index.rst`
- `rank_target_files`：基于真实仓库文件生成目标相关候选排序。

因此最终回答指出以下文件真实存在：

- `pipfile/api.py`
- `tests/test_parser.py`
- `examples/Pipfile`
- `examples/Pipfile.lock`

其中 `tests/test_parser.py` 还真实出现在 `rank_target_files` 的候选结果中。

但是，本次没有执行任何：

```text
read_repo_file
```
### Relevance:`⚠️`

评价：成功识别直接相关测试文件，但没有同时识别对应核心实现文件。

### Sufficiency：❌

评价：当前证据不足以回答“测试如何验证解析行为”。

### Economy:` ⚠️`

评价：Tool 数量不多，但证据预算和 Tool Calling 轮次的使用效率仍然较低。

## Problems Found

- Problem 1 — 能找到测试文件，但无法同时关联核心实现
- Problem 2 — 非核心文件排名仍然较高
- Problem 3 — 两轮 Tool Calling 再次阻止真实源码读取
- Problem 4 — Onboarding 文档再次占用 3 / 4 文件预算

## Conclusion

`Fail`

---

# 修复后复验（2026-08-15）

## 背景

针对上述六个 Case 暴露的问题，完成以下修复：

- Tool Calling 默认轮次 2 → 3（`target_tool_calling.py`），
  支持「发现 → 排序 → 读源码」三阶段；
- `get_onboarding_docs` 整份资料按 1 个文件计入证据预算
  （`repository_safeguards.py`）；
- Ranker 补充中文概念映射
  （签名、序列化、反序列化、解析、验证、恢复、数据），
  核心 Python 源码文件 +2.0，
  过滤 `.svg` 等资源文件，
  非源码文件的 README 引用降权为 +1.0
  （`repository_ranker.py`）；
- `v04_evaluation.py` 新增三仓库 × 六目标排序演示
  （`run_three_repo_ranking_demo`，不需要 LLM）。

修复后重新运行六个 Case 的完整 Tool Calling（LLM），结果如下。

## 复验结果总览

| Case | 旧结论 | 新结论 | 关键变化 |
| --- | --- | --- | --- |
| R1-A | Pass with Issues | Pass with Issues | 与旧报告基本一致 |
| R1-B | PASS | PASS | 与旧报告一致 |
| R2-A | Fail | Pass | read_repo_file 3 次，核心文件第 1、2 名 |
| R2-B | Fail | Fail（明显改善） | 实现文件已读，测试文件被字符预算拦截 |
| R3-A | Fail | Pass | api.py 等 3 个文件真实读取 |
| R3-B | Fail | Pass | api.py + test_parser.py 读取 |

## Case 逐项复验

### R1-A — 理解 RepoMentor 的目录树扫描流程：Pass with Issues

- Tool 调用：`get_repo_tree` → `rank_target_files` →
  read `repository_tree.py`（7864 字符）→
  read `repository_service.py`（3479 字符）→
  read `repository_safeguards.py`（11467 字符）；
- Budget：3/4 files，22810/30000 chars，stopped=False；
- 最终回答覆盖路径校验、忽略规则、递归遍历、深度/文件数限制、
  结果组装，引用的函数均真实存在；
- 与旧报告相同的问题：仍读取了弱相关的 `repository_safeguards.py`，
  Economy ⚠️。

### R1-B — 理解 RepoMentor 的仓库工具如何被测试：PASS

- Tool 调用：`get_repo_tree` → `rank_target_files` →
  read `repository_tools.py`（9250 字符）→
  read `tests/test_repository_tools.py`（4051 字符）；
- Budget：2/4 files，13301/30000 chars，stopped=False；
- 回答准确描述 4 个 Tool 与测试文件的 6 个测试，全部真实。

### R2-A — 理解 ItsDangerous 的数据签名与恢复流程：Fail → Pass

- 排序结果：`serializer.py`（8.0）、`signer.py`（8.0）分列第 1、2 名
  （旧报告为 svg logo 排第一，核心文件不在 Top-8）；
- Tool 调用：`get_repo_tree` → `rank_target_files` →
  read `signer.py`（9913 字符）→
  read `serializer.py`（15967 字符）→
  read `encoding.py`（1463 字符）；
- Budget：3/4 files，27343/30000 chars，stopped=False；
- 回答 grounded：`Signer.sign/unsign`、`Serializer.dumps/loads`、
  `HMACAlgorithm`、secret_keys 轮换、fallback_signers、
  `BadSignature`/`BadPayload` 均真实存在。

### R2-B — 理解 ItsDangerous 的序列化功能如何被测试：Fail（明显改善）

- 第 2 轮模型一次性请求 4 个文件：
  `serializer.py`（15967）+ `signer.py`（9913）= 25880/30000；
  `test_serializer.py`（7022）触发字符超限被拦截，
  `test_signer.py` 未执行；
- Budget：stopped=True（字符数超限），2/4 files，25880/30000 chars；
- 最终回答基于已读实现文件给出「测试覆盖预期」，
  并**明确标注为基于实现推断**，没有把未读测试内容冒充为证据
  （Groundedness ✅）；
- 但目标是「如何被测试」，测试文件没有进入上下文，
  Sufficiency ❌，因此整体仍为 Fail；
- 根因：对「如何被测试」类目标应先读体积更小的测试文件，
  当前模型先读两个大实现文件，占满字符预算。

### R3-A — 理解 Pipfile 的配置解析核心流程：Fail → Pass

- 排序结果：`test_parser.py`（4.5）第 1，
  `pipfile/api.py`（4.0）进入第 2-4 名
  （旧报告 api.py 排第 8、requirements.txt 排第 1）；
- Tool 调用：`get_repo_tree` → `rank_target_files` →
  read `api.py`（5754 字符）→
  read `__init__.py`（420 字符）→
  read `test_parser.py`（1782 字符）；
- Budget：3/4 files，7956/30000 chars，stopped=False；
- 回答 grounded：`PipfileParser.parse()`、
  `inject_environment_variables()`、
  `Pipfile.load/find/hash/lock/assert_requirements()` 均真实存在。

### R3-B — 理解 Pipfile 解析功能如何被测试：Fail → Pass

- Tool 调用：`get_repo_tree`（未调用 `rank_target_files`）→
  read `api.py`（5754 字符）→
  read `test_parser.py`（1782 字符）；
- Budget：2/4 files，7536/30000 chars，stopped=False；
- 回答 grounded：`TestEnvVarInsertion` 及两个测试方法名真实存在，
  并准确指出「测试仅覆盖环境变量注入，`parse()` 主流程未被测试」。

## Groundedness 人工核对

对照真实源码逐条验证模型回答中的关键断言：

| Case | 模型断言 | 真实源码位置 | 核对 |
| --- | --- | --- | --- |
| R1-A | `should_ignore` 特判 `.env.example` 保留 | `repository_tree.py` | ✅ |
| R1-A | `build_tree` / `_walk_directory` / `TreeBuildResult` | `repository_tree.py` | ✅ |
| R2-A | `Signer.sign/unsign/verify_signature/validate` | `signer.py` | ✅ |
| R2-A | `HMACAlgorithm` / `NoneAlgorithm` / `SigningAlgorithm` | `signer.py` | ✅ |
| R2-A | `Serializer.dumps/loads/load_payload/loads_unsafe/iter_unsigners` | `serializer.py` | ✅ |
| R3-A/B | `TestEnvVarInsertion` + 两个测试方法名 | `test_parser.py` | ✅ |
| R3-B | 测试仅覆盖环境变量注入 | `test_parser.py` | ✅ |

所有声称「已读取」的内容都真实、可追溯，没有编造。

## R2-B 残留问题与计划修复

- 排序修复已经生效（模型选择的 4 个文件全部正确），
  失败原因是证据预算分配顺序；
- 计划修复：
  - `max_evidence_chars` 30_000 → 40_000
    （`v04_evaluation.py` run_case）；
  - 系统提示词增加「如何被测试」类目标优先读取测试文件的规则。

## 结论

六个 Case 中五个通过（R1-A、R1-B、R2-A、R3-A、R3-B），
R2-B 从「完全没有读取源码」改善为「实现文件已读、
测试文件被预算拦截」，仍需要针对预算与读取顺序做进一步调整。
