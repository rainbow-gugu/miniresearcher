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
    response = _search.invoke({"query": query})

    # TavilySearch 实际返回 {"query":..., "results":[...], "images":[...]}
    items = response.get("results", []) if isinstance(response, dict) else response

    formatted = []
    for i, r in enumerate(items, 1):
        formatted.append(
            f"[{i}] {r.get('title', '')}\n链接: {r.get('url', '')}\n内容: {r.get('content', '')}"
        )
    return "\n\n".join(formatted) if formatted else f"未找到与「{query}」相关的结果"
