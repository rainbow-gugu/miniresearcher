# MiniResearcher — 多智能体协作研究助手

基于 LangGraph 构建的多 Agent 深度研究系统。输入一个研究问题，系统自动完成任务规划、多源信息检索、代码分析与报告生成。

## 架构

系统采用 **Plan-and-Execute（计划-执行）模式**，通过 LangGraph 的 `StateGraph` 编排五类角色：

```
用户问题
   ↓
Coordinator（协调员）判断是否需要研究
   ↓
Planner（规划师）拆解研究步骤
   ↓
ResearchTeam（调度器）按步骤类型分发  ← 循环
   ├─ Researcher（研究员）：网页搜索
   └─ Coder（工程师）：Python 代码分析
   ↓
Reporter（报告员）整合结果生成报告
```

## 技术栈

- **LangGraph**：多 Agent 状态图编排（节点、动态边、循环）
- **ReAct Agent**：推理-行动循环，自动工具调用
- **DeepSeek**：底层大模型（兼容 OpenAI API 协议）
- **Tavily**：网页搜索
- **Pydantic**：结构化输出与状态定义

## 快速开始

```bash
# 1. 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install langgraph langchain langchain-openai langchain-community langchain-experimental langchain-tavily tavily-python python-dotenv

# 2. 配置密钥
cp .env.example .env
# 编辑 .env 填入 DeepSeek 和 Tavily 的 API Key

# 3. 运行
python main.py
```

## 项目结构

```
├── main.py        # 入口，命令行交互
├── graph.py       # 状态图构建
├── nodes.py       # 所有节点逻辑
├── agents.py      # 研究员 / 工程师 ReAct Agent
├── state.py       # 全局状态与 Plan/Step 定义
├── llm.py         # LLM 工厂
├── prompts.py     # Prompt 模板
└── tools/
    ├── search.py      # Tavily 搜索工具
    └── python_repl.py # Python 执行工具
```
