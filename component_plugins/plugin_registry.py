from component_plugins.plugin_ferrite_bead import PluginFerriteBead
from component_plugins.plugin_base import ComponentPluginBase

# 所有已註冊 Plugin 清單
_PLUGIN_REGISTRY: dict[str, ComponentPluginBase] = {
    "Ferrite Bead": PluginFerriteBead(),
    # 未來可新增： "Capacitor": PluginCapacitor(), ...
}


def get_plugin_by_category(category: str) -> ComponentPluginBase | None:
    """根據產品類別名稱取得對應的 Plugin"""
    return _PLUGIN_REGISTRY.get(category)
