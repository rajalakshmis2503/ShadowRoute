"""
risk_calculator.py - Privacy Exposure Score Calculator
Computes a 0-100 score based on home detection, route repetition, routines, and location clusters.
"""


def calculate_privacy_score(
    home_result: dict,
    repeated_result: dict,
    routine_result: dict,
    frequent_locations: list,
    total_routes: int,
) -> dict:
    """
    Calculate overall Privacy Exposure Score.

    Scoring weights:
        Home Exposure        40 points
        Repeated Routes      25 points
        Routine Detection    20 points
        Frequent Locations   15 points

    Risk levels:
        0-30   Low
        31-60  Medium
        61-100 High
    
    Returns:
        dict with: total_score, risk_level, breakdown (dict), risk_color
    """
    breakdown = {
        "home_exposure": 0,
        "repeated_routes": 0,
        "routine_detection": 0,
        "frequent_locations": 0,
    }

    # --- Home Exposure (0-40) ---
    if home_result.get("detected"):
        confidence = home_result.get("confidence", 0)
        # Scale: 50% confidence -> 20pts, 90%+ -> 40pts
        breakdown["home_exposure"] = min(int(confidence / 100 * 40), 40)

    # --- Repeated Routes (0-25) ---
    if total_routes > 0:
        repeated = repeated_result.get("repeated_count", 0)
        ratio = repeated / total_routes
        breakdown["repeated_routes"] = min(int(ratio * 25), 25)

    # --- Routine Detection (0-20) ---
    routine_level = routine_result.get("routine_level", "Low")
    routine_map = {"Low": 0, "Medium": 10, "High": 20, "Unknown": 0}
    breakdown["routine_detection"] = routine_map.get(routine_level, 0)

    # --- Frequent Locations (0-15) ---
    n_locations = len(frequent_locations)
    # 1 cluster -> 5pts, 3 clusters -> 10pts, 5+ clusters -> 15pts
    breakdown["frequent_locations"] = min(n_locations * 3, 15)

    total = sum(breakdown.values())
    total = min(max(total, 0), 100)

    if total <= 30:
        risk_level = "Low"
        risk_color = "#22c55e"
        risk_emoji = "🟢"
    elif total <= 60:
        risk_level = "Medium"
        risk_color = "#f59e0b"
        risk_emoji = "🟡"
    else:
        risk_level = "High"
        risk_color = "#ef4444"
        risk_emoji = "🔴"

    return {
        "total_score": total,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "risk_emoji": risk_emoji,
        "breakdown": breakdown,
    }
