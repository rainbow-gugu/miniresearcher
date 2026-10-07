"""LLM 工厂：统一创建 DeepSeek 模型实例，带缓存。"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# 缓存，同类型 LLM 只创建一次
_llm_cache = {}


def get_llm(llm_type: str = "basic") -> ChatOpenAI:
    """
    获取 LLM 实例。
    所有 Agent 默认用 basic 模型；以后可以扩展 reasoning 等类型。
    """
    if llm_type in _llm_cache:
        return _llm_cache[llm_type]

    # DeepSeek 兼容 OpenAI API 格式，只需改 base_url
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=0.3,
    )

    _llm_cache[llm_type] = llm
    return llm
