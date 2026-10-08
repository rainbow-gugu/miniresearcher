# 改进记录

项目：**MiniResearcher** — 基于 LangGraph 的多智能体研究助手
阶段：第一阶段「打通全流程」
日期：2026-10-08

> 本文记录一次系统的缺陷排查与修复。每条都遵循 **现象 → 根因 → 修法 → 实测效果**。
> 所有结论均来自**实跑验证**，不是静态代码审查的推测——这一点很重要，
> 因为其中至少两个缺陷（#1、#4）从代码表面完全看不出问题。

---

## 总览

| # | 缺陷 | 级别 | 状态 |
|---|---|---|---|
| 0 | 仓库基线：模板误删、无依赖清单、生成物入库 | 工程 | ✅ |
| 1 | 搜索工具格式化分支是死代码，返回原始 dict | P0 | ✅ |
| 2 | 闲聊分支打印空白报告 | P0 | ✅ |
| 3 | 进度打印形同虚设（只显示消息类名） | P0 | ✅ |
| 4 | 子 Agent 拿不到总目标与前序研究结果 | **P0 根因** | ✅ |
| 5 | planner 重复研究循环，成本翻倍 | P1 | ✅ |

**修复前的实际表现**：用户提问「元数据标签前置过滤和后置的区别和优缺点」，
系统跑了 11 个步骤（其中 6 个是重复劳动），最终产出一份**关于 Python vs JavaScript**
的报告，终端上**看不到任何研究内容**。

---

## 0. 仓库基线清理

**现象**
- `.env.example` 处于 staged deletion（已被暂存删除），而 README 却要求 `cp .env.example .env`
- 没有 `requirements.txt`；README 用一长串**无版本号**的 `pip install`
- `.idea/` 未忽略
- Agent 生成的 `final_report.md`、`comparison_data.json` 被误提交进仓库

**根因**
`.gitignore` **只对「未被跟踪」的文件生效**。文件一旦 `git add` 过，忽略规则对它永久失效。
`playground.py` 就是典型：`.gitignore` 里明明写着它，但 `git status` 里照样出现。

**修法**

```bash
git checkout HEAD -- .env.example            # 恢复被误删的模板
git rm --cached playground.py                # 只从仓库摘出，磁盘文件保留
git rm "final_report.md" "language_comparison.md" ...   # 生成物直接删除
./venv/bin/pip freeze > requirements.txt     # 锁定依赖
```

**实测效果**
- 工作区干净（`git status --short` 为空）
- `git check-ignore -v playground.py` → `.gitignore:20:playground.py`（忽略规则重新生效）
- `requirements.txt` 锁定 **66 个依赖**（`langgraph==1.2.14`、`langchain==1.4.3` 等）

---

## 1. 搜索工具：格式化分支是死代码

**现象**
研究员收到的搜索结果是**一大坨 Python 字典字面量**，而不是可读的 `[1] 标题 / 链接 / 内容`。

**根因**
[`tools/search.py`](tools/search.py) 用 `isinstance(results, list)` 判断返回类型，
但 `TavilySearch._run()` 的签名是 `-> Dict[str, Any]`，实际返回：

```python
{"query": ..., "follow_up_questions": None, "answer": None,
 "images": [], "results": [{"title": ..., "url": ..., "content": ..., "score": ...}]}
```

**`isinstance(dict, list)` 永远为 `False`**，所以那个精心写的格式化分支**从未执行过**，
永远走最后一行 `return str(results)`。

**实测证据**：单次搜索返回 **7998 字符**，开头是 `{'query': 'LangGraph 是什么', 'follow_up_questions': None, ...}`

**修法**：改为从 `response["results"]` 取列表。

**实测效果**
- 输出从 **7998 → 5913 字符**（-26%），且格式变成人类/LLM 都易读的 `[1] 标题 / 链接 / 内容`
- ⚠️ **副产物（已记录为后续优化项）**：新的格式化函数只放行 `title/url/content` 三个字段，
  把 `score`（相关性打分）丢掉了。研究员因此不知道哪条结果最相关。
  ——这说明「改数据加工代码」时必须问一句：**我这刀切掉了什么？**

---

## 2. 闲聊分支打印空白报告

**现象**
问「什么是 LangGraph？」，LLM 明明给出了完整正确的回答，终端却打印一片空白。

**根因**
- `coordinator_node` 的闲聊分支只把回答写进 `messages`：
  `update={"messages": [response]}`
- 而 [`main.py`](main.py) 读的是 `final_report`
- **两条分支把答案放在了两个不同的抽屉里，main.py 只翻其中一个。**

**实测证据**：`final_report` 长度 `0`，而 `messages[-1]` 里有 147 字符的完整回答。

**修法**
在**图内部**补全状态（coordinator 同时写 `final_report`），让 `main.py` 保持"哑终端"。

**为什么这样改**

> **架构原则：状态的完整性由「图」负责，展示的美观由「main.py」负责。**
>
> 如果改成在 main.py 里兜底（`if not report: report = messages[-1].content`），
> 就等于让展示层知道"图里有几条分支、每条把答案放哪"。以后加第三条分支还得再改 main.py。

**实测效果**：`final_report` 长度 **147**，正常显示。

---

## 3. 进度打印形同虚设

**现象**
跑一次完整研究流程（约 3 分钟、17 个节点），终端**只打印两行**：

```
  ... HumanMessage 处理中
  ... AIMessage 处理中
```

**根因**
`stream_mode="values"` 只返回**完整状态快照**，不告诉你这是哪个节点产生的。
代码只好用 `messages[-1]` 的类名冒充进度——而消息类名（`HumanMessage`/`AIMessage`）
跟"正在跑哪个节点"**毫无关系**。

**实测证据**（用一个不花钱的最小对照图跑出来的）：

```
=== stream_mode="values" ===
   得到: {'log': ['alpha 跑完']}          ← 没有节点名
=== stream_mode=["updates","values"] ===
   得到: ('updates', {'alpha': {...}})    ← 节点名就在 key 上
```

**修法**：同时订阅两种流。`updates` 用来报进度，`values` 用来取最终状态。

**实测效果**：能看到完整节点序列，且每个研究步骤的标题都会显示：

```
  ▶ coordinator
  ▶ planner
  ▶ research_team
  ▶ researcher
      ✓ 厘清前置过滤与后置过滤的概念定义与典型流程
```

---

## 4. 子 Agent 拿不到上下文（根因级缺陷）

**现象**
系统跑了很多步骤、看起来"很忙"，但各步骤之间**没有任何协作**；
用户始终拿不到一份回答自己问题的报告。

**根因**
[`nodes.py`](nodes.py) 的 `_run_agent_step` 只给子 Agent 喂了两行文字：

```python
task = f"步骤标题：{next_step.title}\n具体要求：{next_step.description}"
```

而 `state["observations"]` 里攒着前序所有步骤的研究成果——**一行都没传进去**。

**实测证据**（用一个假 Agent 把它收到的内容原样打印）：

```
========== 子 Agent 实际收到的全部内容 ==========
步骤标题：收集两种方案的优缺点
具体要求：找性能对比数据
================================================
```

**后果链（这才是最严重的部分）**

```
子 Agent 只收到 2 行字，不知道总目标、看不到已查到的资料
        │
        ▼
它手里有 PythonREPL，能自由读写当前目录
        │  → 去磁盘上找资料
        ▼
翻到上一个任务遗留的 comparison_data.json
        │
        ▼
把它当成自己的研究成果 → 写出关于 Python/JS 的报告 ❌
```

**直接证据**：用户问的是**元数据过滤**，但产出的 `final_report.md` 标题是
「Python 和 JavaScript 的主要区别是什么？」，且文件里自述：

> **数据来源**：`comparison_data.json`（前序步骤产出，含 7 个对比维度）

——它把**上一个任务的垃圾文件**当成了"前序步骤产出"。

**修法**
把「总目标 + 当前步骤 + 具体要求 + 前序已获得的资料」一起喂进去。

**实测效果**：验收输出四块齐全：

```
【总目标】元数据标签前置过滤 vs 后置过滤
【当前步骤】收集两种方案的优缺点
【具体要求】找性能对比数据

【前序步骤已获得的资料】
【第1步结果】前置过滤在向量检索前裁剪候选集，召回率下降但延迟更低……
```

**隔离测试（证明检索本身没问题）**
把研究员**单独拉出来跑一步**，它做了 **10 次检索**（2+3+3+2），
交出 20 个真实来源（Qdrant / Pinecone / Weaviate / Milvus / arXiv）和完整基准数据。
**所以从来不是"检索不全"，而是管道把成果丢了。**

---

## 5. planner 重复研究循环

**现象**
一次运行里 `▶ planner` 出现了**两次**，11 个执行步骤中有 6 个是重复劳动：

| 第一轮 | 第二轮（重复） |
|---|---|
| 厘清前置过滤与后置过滤的**概念定义**与典型流程 | **统一术语边界与概念定义** |
| 调研主流系统对两种过滤方式的**支持与实现机制** | 梳理两种过滤的**标准执行流程与实现机制** |
| 收集两种过滤方式的**优缺点与性能对比**资料 | **汇总召回率、延迟、吞吐的实测对比数据** |
| 建模分析过滤**选择率对召回率与延迟的影响** | 分析**过滤选择性（selectivity）对策略优劣的影响** |
| 整合资料**撰写对比报告** | 构建**优缺点对比矩阵与选型决策树** |

**根因**
[`nodes.py`](nodes.py) 的 `research_team_node` 在所有步骤完成后**无条件**回到 `planner`：

```python
    if not pending_steps:
        return Command(goto="planner")   # ← 问题在这
```

而 `planner` 每次都会**重建一份全新的计划**——新计划的步骤状态全是 `pending`，
于是**同样的研究被完整地重做一遍**。

**修法**
区分「全部成功」和「有步骤失败」两种情况：

```python
    failed_steps = [s for s in plan.steps if s.status == "failed"]
    if failed_steps:
        return Command(goto="planner")   # 只有失败时才值得重规划

    return Command(goto="reporter")      # 全成功 → 直接交卷
```

**实测效果**（免费验证，看图的拓扑即可）：

```
	research_team -.-> reporter;      ← 新增的直通边
	research_team -.-> planner;       ← 保留，仅在有失败步骤时走
```

---

## 未完成事项（下一阶段）

| # | 待修项 | 说明 |
|---|---|---|
| 6 | 端到端实跑 | 拿到第一份真实报告 |
| 7 | 让中间研究结果可见 | `observations` 目前只进状态、从不打印（"漏斗①"） |
| 8 | 控制上下文长度 | 第 4 关的修法会让后序步骤读到全部前序资料，上下文线性增长 |
| 9 | 状态深拷贝 + `StopIteration` | 节点内原地修改 state 是 LangGraph 反模式；`next(...)` 无默认值会崩 |
| 10 | 输出隔离 | Agent 用 PythonREPL 直接往仓库根目录写文件，需沙箱化 + 统一输出到 `outputs/` |
| 11 | 失败步骤重试 | 目前 `failed` 步骤永不重试 |
| 12 | 依赖现代化 | `langgraph.prebuilt.create_react_agent` 已弃用（V1.0 起），应迁移到 `langchain.agents.create_agent`；`langchain-experimental` 已 sunset |
| 13 | 测试规范化 | `test_state.py` / `test_tools.py` 在 import 时就真跑（会烧 API 额度），应改成真正的 pytest |
| 14 | 可观测性与持久化 | 全项目零 `logging`；无 checkpointer，无法中断/恢复/人工介入 |

---

## 如何复现今天的验证

```bash
cd /Users/rabbitwhy/miniresearcher
source venv/bin/activate

# 1. 搜索工具格式是否正确（应输出 [1] 标题 / 链接 / 内容，且无 {'query': 花括号）
python -c "
from tools.search import web_search_tool
out = web_search_tool.invoke({'query': 'LangGraph 是什么'})
print(len(out)); print(out[:200])
"

# 2. 子 Agent 是否拿到上下文（免费，不调 API）
python -c "
import asyncio
from langchain_core.messages import AIMessage
from state import Plan, Step
from nodes import _run_agent_step
class Echo:
    async def ainvoke(self, p):
        print(p['messages'][0].content)
        return {'messages': [AIMessage(content='ok')]}
s = {'messages': [], 'current_plan': Plan(thought='t', title='总目标示例',
     steps=[Step(title='步骤示例', description='要求示例', step_type='research')]),
     'observations': ['前序资料示例']}
asyncio.run(_run_agent_step(s, Echo(), 'researcher'))
"

# 3. 图的拓扑（应出现 research_team -.-> reporter）
python -c "
from graph import graph
print(graph.get_graph().draw_mermaid())
"

# 4. 完整流程
python main.py
```
