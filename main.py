"""MiniResearcher 入口：命令行输入问题，多 Agent 协作生成研究报告。"""
import asyncio
from langchain_core.messages import HumanMessage
from graph import graph


async def run(question: str):
    print("\n" + "=" * 60)
    print(f"研究问题：{question}")
    print("=" * 60)

    inputs = {"messages": [HumanMessage(content=question)]}
    final_state = None

    # 流式执行：只执行一次，实时观察节点动作，最后一次快照即最终状态
    async for event in graph.astream(inputs, stream_mode="values"):
        final_state = event
        # 从 messages 最后一条判断当前进度
        last = event["messages"][-1]
        name = getattr(last, "name", None) or last.__class__.__name__
        print(f"  ... {name} 处理中")

    return final_state.get("final_report", "") if final_state else ""


def main():
    print("=" * 60)
    print("  MiniResearcher — 多智能体研究助手")
    print("=" * 60)
    question = input("\n请输入你的研究问题：\n> ")

    if not question.strip():
        print("问题不能为空")
        return

    report = asyncio.run(run(question))

    print("\n")
    print("=" * 60)
    print("  最终研究报告")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    main()
