from tools.search import web_search_tool
from tools.python_repl import python_repl_tool

print("=" * 50)
print("测试搜索工具")
print("=" * 50)
print(web_search_tool.invoke({"query": "什么是多智能体系统"})[:500])

print()
print("=" * 50)
print("测试 Python 工具")
print("=" * 50)
print(python_repl_tool.invoke({"code": "print(1+1)\nfor i in range(3): print(i)"}))
