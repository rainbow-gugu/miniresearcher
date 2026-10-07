"""把所有节点和边组装成完整的工作流图。"""
from langgraph.graph import StateGraph, START, END
from state import State
from nodes import (
    coordinator_node,
    planner_node,
    research_team_node,
    researcher_node,
    coder_node,
    reporter_node,
)


def build_graph():
    builder = StateGraph(State)

    # 注册节点
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("planner", planner_node)
    builder.add_node("research_team", research_team_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("coder", coder_node)
    builder.add_node("reporter", reporter_node)

    # 注册边
    builder.add_edge(START, "coordinator")
    builder.add_edge("reporter", END)

    return builder.compile()


graph = build_graph()
