print("=== 5.1 列表 ===")
blocks = []                          # 空列表
blocks.append("第一段")               # 尾部塞一个
blocks.append("第二段")
print("内容:", blocks)
print("长度:", len(blocks), "| 第一个:", blocks[0], "| 最后一个:", blocks[-1])


print("=== 5.2 字典：[] vs .get() —— 最重要 ===")
r = {"title": "标题", "url": "http://example.com"}
print("正常取值 r['title'] =", r["title"])

try:
    r["content"]                     # content 这个键不存在
except KeyError as e:
    print("💥 用 [] 取不存在的键 → KeyError 直接崩:", e)

print("用 .get('content')       →", r.get("content"))
print("用 .get('content', '')   →", repr(r.get("content", "")))
print("↑ 不崩，返回默认值。这就是为什么代码里到处是 .get()")


print("=== 5.3 f-string 和转义符 ===")
title, i = "AI 芯片", 0
print(f"f-string 版: [{i + 1}] {title}")
print("加号拼接版: [" + str(i + 1) + "] " + title)
print(f"转义符: 第一行\n第二行\t← Tab 缩进")


print("=== 5.4 join：字符串当胶水 ===")
parts = ["A", "B", "C"]
print("双换行 join →", repr("\n\n".join(parts)))
print("短横线 join →", "-".join(parts))
print("顿号 join   →", "、".join(["苹果", "香蕉", "橘子"]))