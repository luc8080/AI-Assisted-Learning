import json

# === 簡易知識查詢工具（查詢教材資料） ===
def load_knowledge_data(filepath="教材庫/材論資料庫.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def lookup_knowledge(query, data=None):
    if data is None:
        data = load_knowledge_data()
    results = []
    for item in data:
        text = json.dumps(item, ensure_ascii=False)
        if query in text:
            results.append(item)
    return results[:3]  # 限制最多回傳 3 筆

# === Tool 包裝（可供 Agent 呼叫） ===
def knowledge_tool(query):
    hits = lookup_knowledge(query)
    if not hits:
        return "找不到相關教材資料。"
    return "\n\n".join([
        f"【{h.get('type', '教材')}】{h.get('title') or h.get('term')}\n{h.get('content') or h.get('definition')}" for h in hits
    ])
