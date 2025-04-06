from typing import List, Dict, Tuple

def filter_with_rejection_reason(requirements: dict, products: List[dict]) -> Tuple[List[dict], List[dict]]:
    matched = []
    rejected = []

    for p in products:
        reasons = []

        if requirements.get("impedance") is not None and p.get("impedance") is not None:
            tol = requirements.get("impedance_tolerance", 0.25)
            if abs(p["impedance"] - requirements["impedance"]) > tol * requirements["impedance"]:
                reasons.append("阻抗不符合")

        if requirements.get("current") is not None and p.get("current") is not None:
            if p["current"] < requirements["current"]:
                reasons.append("電流不足")

        if requirements.get("dcr") is not None and p.get("dcr") is not None:
            if p["dcr"] > requirements["dcr"]:
                reasons.append("DCR 過高")

        if requirements.get("temp_min") is not None and p.get("temp_min") is not None:
            if p["temp_min"] > requirements["temp_min"]:
                reasons.append("最低溫度不符")

        if requirements.get("temp_max") is not None and p.get("temp_max") is not None:
            if p["temp_max"] < requirements["temp_max"]:
                reasons.append("最高溫度不符")

        if requirements.get("size") is not None and p.get("size") != requirements["size"]:
            reasons.append("尺寸不符")

        if reasons:
            p_with_reason = p.copy()
            p_with_reason["rejected_reason"] = "、".join(reasons)
            rejected.append(p_with_reason)
        else:
            matched.append(p)

    return matched, rejected

def sort_candidates(products: List[dict], priority: str = "current") -> List[dict]:
    if priority == "dcr":
        return sorted(products, key=lambda p: p.get("dcr", float("inf")))
    elif priority == "current":
        return sorted(products, key=lambda p: -p.get("current", 0))
    else:
        return products
