from component_plugins.plugin_registry import get_plugin_by_category

# 關鍵字 ➜ 對應產品類別（Plugin）
APPLICATION_CATEGORY_MAP = {
    "濾波": "Ferrite Bead",
    "抗雜訊": "Ferrite Bead",
    "電源": "Ferrite Bead",
    "抑制雜訊": "Ferrite Bead",
    "儲能": "Capacitor",
    "退耦": "Capacitor",
    "調頻": "Inductor",
    "濾高頻": "EMI Suppression Filter",
    "信號濾波": "Balun Filter",
    "網路": "Lan Transformer"
    # 可依專案擴充
}

def auto_detect_category(application: str) -> str | None:
    """根據應用文字自動推論 Plugin 類別"""
    for keyword, category in APPLICATION_CATEGORY_MAP.items():
        if keyword in application:
            return category
    return None

def get_plugin_by_application(application: str):
    """根據用途應用文字，自動找出對應 Plugin"""
    category = auto_detect_category(application or "")
    if category:
        return get_plugin_by_category(category), category
    return None, None
