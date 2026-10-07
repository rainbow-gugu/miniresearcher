"""图的所有节点：协调员、规划师、调度器、研究员、工程师、报告员。"""
import json
from typing import Annotated, Literal
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.types import Command

from llm import get_llm
from state import State, Plan, Step
from agents import researcher, coder
from prompts import COORDINATOR, PLANNER, REPORTER


# 协调员用这个工具来"信号化"：我要启动研究流程
@tool
def handoff_to_planner(
    reason: Annotated[str, "为什么需要启动研究"]
):
    """当用户的问题需要深度研究时调用，把任务交给规划师。"""
    return


def coordinator_node(state: State) -> Command[Literal["planner", "__end__"]]:
    """协调员：判断用户是闲聊还是需要研究。"""
    user_message = state["messages"][-1].content

    # 绑定 handoff 工具，让 LLM 自己决定要不要研究
    llm = get_llm().bind_tools([handoff_to_planner])
    response = llm.invoke(COORDINATOR.format(user_message=user_message))

    # LLM 调用了 handoff 工具 → 去规划师；否则 → 直接结束（闲聊）
    if response.tool_calls:
        return Command(goto="planner")
    return Command(
        update={"messages": [response]},
        goto="__end__",
    )


def planner_node(state: State) -> Command[Literal["research_team", "reporter"]]:
    """规划师：把问题拆成研究步骤。"""
    user_message = state["messages"][0].content
    observations = "\n\n".join(state.get("observations", [])) or "（暂无）"

    # 防止死循环：超过 3 轮规划就强制写报告
    plan_iterations = state.get("plan_iterations", 0)
    if plan_iterations >= 3:
        plan = state.get("current_plan")
        if plan:
            return Command(goto="reporter")

    # 用结构化输出，强制 LLM 返回符合 Plan schema 的 JSON
    llm = get_llm().with_structured_output(Plan, method="function_calling")
    plan = llm.invoke(PLANNER.format(
        user_message=user_message,
        observations=observations,
    ))

    # 信息够了 → 直接报告；不够 → 去研究团队执行步骤
    goto = "reporter" if plan.has_enough_context or not plan.steps else "research_team"

    return Command(
        update={
            "current_plan": plan,
            "plan_iterations": plan_iterations + 1,
        },
        goto=goto,
    )


def research_team_node(state: State) -> Command[Literal["researcher", "coder", "planner"]]:
    """调度器：找下一个未执行的步骤，分发给对应 Agent。"""
    plan = state.get("current_plan")

    if not plan or not plan.steps:
        return Command(goto="planner")

    # 没有待执行步骤了（全部 done，或含 failed）→ 回到规划师判断/重规划
    pending_steps = [s for s in plan.steps if s.status == "pending"]
    if not pending_steps:
        return Command(goto="planner")

    # 取第一个待执行的步骤
    next_step = pending_steps[0]

    # 按类型分发
    if next_step.step_type == "processing":
        return Command(goto="coder")
    return Command(goto="researcher")


async def _run_agent_step(state: State, agent, agent_name: str):
    """通用逻辑：让 Agent 执行当前步骤，把结果写回计划。"""
    plan = state.get("current_plan")
    next_step = next(s for s in plan.steps if s.status == "pending")

    # 标记为执行中
    next_step.status = "running"

    # 构造给 Agent 的任务描述
    task = f"步骤标题：{next_step.title}\n具体要求：{next_step.description}"

    try:
        result = await agent.ainvoke({"messages": [HumanMessage(content=task)]})
        # Agent 的最终回答
        answer = result["messages"][-1].content
        # 标记完成并写回结果
        next_step.status = "done"
        next_step.execution_res = answer
    except Exception as e:
        # 标记失败，错误信息也作为结果，方便规划师据此调整
        answer = f"步骤执行失败: {repr(e)}"
        next_step.status = "failed"
        next_step.execution_res = answer

    return Command(
        update={
            "observations": [answer],  # 只返回新增，add reducer 自动与旧列表拼接
            "current_plan": plan,
        },
        goto="research_team",
    )


async def researcher_node(state: State) -> Command[Literal["research_team"]]:
    """研究员节点：执行搜索类步骤。"""
    return await _run_agent_step(state, researcher, "researcher")


async def coder_node(state: State) -> Command[Literal["research_team"]]:
    """工程师节点：执行代码分析类步骤。"""
    return await _run_agent_step(state, coder, "coder")


def reporter_node(state: State):
    """报告员：整合所有研究结果，生成最终报告。"""
    plan = state.get("current_plan")
    observations = "\n\n".join(state.get("observations", []))

    llm = get_llm()
    response = llm.invoke(REPORTER.format(
        title=plan.title if plan else "研究报告",
        thought=plan.thought if plan else "",
        observations=observations,
    ))

    return {"final_report": response.content}
