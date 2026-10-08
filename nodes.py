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
        update={
            "messages": [response],
            "final_report":response.content,
        },
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


def research_team_node(state: State) -> Command[Literal["researcher", "coder", "planner", "reporter"]]:
    """调度器：找下一个未执行的步骤，分发给对应 Agent。"""
    plan = state.get("current_plan")

    if not plan or not plan.steps:
        return Command(goto="planner")

    # 还有待执行的步骤 → 取第一个，按类型分发
    pending_steps = [s for s in plan.steps if s.status == "pending"]
    if pending_steps:
        next_step = pending_steps[0]
        if next_step.step_type == "processing":
            return Command(goto="coder")
        return Command(goto="researcher")

    # 没有待执行步骤了，要区分两种情况：
    failed_steps = [s for s in plan.steps if s.status == "failed"]
    if failed_steps:
        # 有步骤失败 → 回规划师，让它决定换个路子还是放弃
        return Command(goto="planner")

    # 全部成功 → 直接去写报告。
    # 这里绝对不能回 planner：planner 会重建一份全新的 pending 计划，
    # 导致同样的研究被重复做一遍（实测重复了 6 个步骤、成本翻倍）。
    return Command(goto="reporter")


async def _run_agent_step(state: State, agent, agent_name: str):
    """通用逻辑：让 Agent 执行当前步骤，把结果写回计划。"""
    plan = state.get("current_plan")
    next_step = next(s for s in plan.steps if s.status == "pending")

    # 标记为执行中
    next_step.status = "running"

    # 构造给 Agent 的任务描述。
    # 关键：必须把「总目标」和「前序步骤已获得的资料」一起喂进去，
    # 否则子 Agent 不知道上下文，会瞎猜，甚至去磁盘翻出上个任务的遗留文件当成果。
    previous = "\n\n".join(state.get("observations", []))
    context = previous if previous.strip() else "（这是第一步，暂无已有资料）"

    task = (
        f"【总目标】{plan.title}\n"
        f"【当前步骤】{next_step.title}\n"
        f"【具体要求】{next_step.description}\n"
        f"\n【前序步骤已获得的资料】\n{context}"
    )

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
