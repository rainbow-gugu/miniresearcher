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

    # 同时订阅两种流：
    #   updates → 每次节点执行完，告诉你「刚才是哪个节点跑了」
    #   values  → 当前完整状态快照，用它取最终结果
    async for mode, chunk in graph.astream(inputs, stream_mode=["updates", "values"]):
        if mode == "values":
            final_state = chunk
            continue

        # mode == "updates" 时，chunk 形如 {"节点名": 该节点返回的 update}

        for node_name, update in chunk.items():
            print(f"  ▶ {node_name}")
            if node_name in ("researcher", "coder") and isinstance(update, dict):
                plan = update.get("current_plan")
                if plan and plan.steps:
                    done = [s for s in plan.steps if s.status == "done"]
                    if done:
                        print(f"      ✓ {done[-1].title}")
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
