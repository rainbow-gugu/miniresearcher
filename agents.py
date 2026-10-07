"""Agent 定义：研究员和工程师，都是 ReAct Agent，只是工具不同。"""
from langgraph.prebuilt import create_react_agent
from llm import get_llm
from tools.search import web_search_tool
from tools.python_repl import python_repl_tool

# 研究员：能搜索网页
researcher = create_react_agent(
    name="researcher",
    model=get_llm(),
    tools=[web_search_tool],
    prompt="你是一名专业研究员。根据任务要求搜索互联网，收集准确、全面的信息。"
           "请在回答末尾列出所有信息来源的链接。",
)

# 工程师：能执行 Python 代码
coder = create_react_agent(
    name="coder",
    model=get_llm(),
    tools=[python_repl_tool],
    prompt="你是一名数据工程师。通过编写并执行 Python 代码完成数据分析、计算和验证。"
           "代码出错就根据报错修改重试，直到得到结果。",
)
