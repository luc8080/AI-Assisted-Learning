from component_plugins.plugin_base import ComponentPluginBase
from typing import Dict


class PluginFerriteBead(ComponentPluginBase):
    @property
    def category(self) -> str:
        return "Ferrite Bead"

    @property
    def prompt_template(self) -> str:
        return """
你是一位磁珠產品顧問。你將收到使用者需求與一批候選產品資料，請從中推薦最合適的 2~3 筆，並說明推薦理由。

請回傳以下格式（JSON 陣列）：
[
  {
    "part_number": "HFZ3216-601T",
    "vendor": "Tai-Tech",
    "reason": "符合 10A 電流需求，且 DCR 僅 0.02Ω，效率最佳",
    "specs": {
      "impedance": 600,
      "current": 10000,
      "dcr": 0.02,
      "temp_min": -40,
      "temp_max": 100,
      "size": "3216"
    }
  }
]
        """

    @property
    def key_metrics(self) -> list[str]:
        return ["impedance", "current", "dcr", "temp_min", "temp_max"]

    def match_score(self, product: Dict, req: Dict) -> float:
        score = 0
        total = 0

        def check(k, op):
            nonlocal score, total
            if req.get(k) is not None and product.get(k) is not None:
                total += 1
                if op(product[k], req[k]):
                    score += 1

        check("impedance", lambda p, r: abs(p - r) <= r * req.get("impedance_tolerance", 0.25))
        check("current", lambda p, r: p >= r)
        check("dcr", lambda p, r: p <= r)
        check("temp_min", lambda p, r: p <= r)
        check("temp_max", lambda p, r: p >= r)

        return round(score / total * 100, 2) if total else 0.0
