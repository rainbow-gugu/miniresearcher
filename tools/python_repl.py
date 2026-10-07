"""Python 代码执行工具：供工程师 Agent 做数据分析和计算。"""
from typing import Annotated
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

# PythonREPL 内部用一个独立的命名空间执行代码
_repl = PythonREPL()


@tool
def python_repl_tool(
    code: Annotated[str, "要执行的 Python 代码。想看输出必须用 print()"]
) -> str:
    """执行 Python 代码做数据分析、计算、图表处理。需要数值计算或数据处理时使用。"""
    try:
        result = _repl.run(code)
        if not result.strip():
            result = "(代码执行成功，无输出。记得用 print() 打印结果)"
        return f"执行成功:\n```python\n{code}\n```\n输出:\n{result}"
    except BaseException as e:
        return f"执行出错:\n```python\n{code}\n```\n错误: {repr(e)}"
