# === 檔案路徑：rule_recommender.py
# === 功能說明：
# 根據使用者需求條件，篩選結構化產品清單，排除不符合條件者，並排序推薦清單。
# === 最後更新：2025-04-13

def filter_with_rejection_reason(products: list[dict], requirements: dict) -> list[dict]:
    filtered = []

    for p in products:
        reason = []

        try:
            if "impedance" in requirements and p.get("impedance") is not None:
                try:
                    imp = float(p["impedance"])
                    req = float(requirements["impedance"])
                    tolerance = requirements.get("impedance_tolerance", 0.25)
                    if abs(imp - req) > tolerance * req:
                        reason.append("阻抗不符")
                except Exception:
                    reason.append("阻抗格式錯誤")

            if "current" in requirements and p.get("current") is not None:
                try:
                    if float(p["current"]) < float(requirements["current"]):
                        reason.append("額定電流不足")
                except Exception:
                    reason.append("電流格式錯誤")

            if "dcr" in requirements and p.get("dcr") is not None:
                try:
                    if float(p["dcr"]) > float(requirements["dcr"]):
                        reason.append("DCR 過高")
                except Exception:
                    reason.append("DCR 格式錯誤")

            if reason:
                continue
            filtered.append(p)

        except Exception as e:
            print(f"[篩選錯誤] {e}")
            continue

    return filtered

def sort_candidates(products: list[dict], requirements: dict) -> list[dict]:
    def score(p):
        s = 0
        try:
            if "current" in requirements and p.get("current") is not None:
                s += float(p["current"])
            if "impedance" in requirements and p.get("impedance") is not None:
                s += -abs(float(p["impedance"]) - float(requirements["impedance"]))
            if "dcr" in requirements and p.get("dcr") is not None:
                s -= float(p["dcr"])
        except:
            pass
        return s

    return sorted(products, key=score, reverse=True)
