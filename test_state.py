import asyncio
from langchain_core.messages import HumanMessage
from graph import graph

async def main():
    q = "Python和JavaScript的主要区别是什么？"
    final = await graph.ainvoke({"messages": [HumanMessage(content=q)]})

    plan = final.get("current_plan")
    print("=== 各步骤状态 ===")
    if plan:
        for i, s in enumerate(plan.steps, 1):
            print(f"  {i}. [{s.step_type}] {s.title} -> {s.status}")
    obs = final.get("observations", [])
    print(f"\n=== observations 共 {len(obs)} 条 ===")
    # 检查是否有完全重复的条目
    unique = len(set(obs))
    print(f"去重后 {unique} 条", "✓ 无重复" if unique == len(obs) else "✗ 存在重复!")
    print(f"\n报告长度: {len(final.get('final_report', ''))} 字符")

asyncio.run(main())
