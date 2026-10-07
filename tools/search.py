"""网页搜索工具：封装 Tavily，供研究员 Agent 调用。"""
import os
import functools
from typing import Annotated
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

load_dotenv()

# 创建 Tavily 搜索器，配置返回结果数量
_search = TavilySearch(
    max_results=5,
    api_key=os.getenv("TAVILY_API_KEY"),
)


@tool
def web_search_tool(
    query: Annotated[str, "要搜索的关键词或问题"]
) -> str:
    """搜索互联网获取最新信息、事实、数据。当你需要查找资料、了解背景、收集信息时使用。"""
    results = _search.invoke({"query": query})

    # Tavily 返回的是 list[dict]，整理成易读的文本
    if isinstance(results, list):
        formatted = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")
            formatted.append(f"[{i}] {title}\n链接: {url}\n内容: {content}")
        return "\n\n".join(formatted)
    return str(results)
