"""全局状态定义：所有图节点共享这个 State。"""
from typing import Annotated, Optional, Literal
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from operator import add

class Step(BaseModel):
    """单个研究步骤。"""
    title: str = Field(description="步骤标题")
    description: str = Field(description="这个步骤具体要收集什么数据")
    step_type:Literal["research","processing"] = Field(description="research（搜索网页）或 processing（执行代码）")
    status: Literal["pending", "running", "done", "failed"] = Field(
        default="pending", description="执行状态"
    )
    execution_res: Optional[str] = Field(default=None, description="步骤执行结果，None 表示未执行")


class Plan(BaseModel):
    """研究计划。"""
    thought: str = Field(description="规划思路")
    title: str = Field(description="研究任务标题")
    has_enough_context: bool = Field(default=False, description="现有信息是否已足够写报告")
    steps: list[Step] = Field(default_factory=list, description="研究步骤列表")


class State(MessagesState):
    """
    MessagesState是LangGraph内置的状态类，自带messages列表
    多 Agent 系统的全局状态。
    继承 MessagesState，自带 messages 字段（对话历史）。
    """
    current_plan: Optional[Plan] = None       # 当前研究计划
    observations: Annotated[list[str], add] = Field(default_factory=list)  # 累加语义
    plan_iterations: int = 0                  # 规划迭代次数（防止死循环）
    final_report: str = ""                    # 最终报告
