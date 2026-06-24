"""
recommendations.py - Privacy Recommendations Generator
Produces actionable privacy advice based on analysis findings.
"""


def generate_recommendations(
    home_result: dict,
    repeated_result: dict,
    routine_result: dict,
    frequent_locations: list,
    risk_score: dict,
) -> list[dict]:
    """
    Generate targeted privacy recommendations.

    Returns:
        List of recommendation dicts with: title, description, priority, icon
    """
    recs = []
    risk_level = risk_score.get("risk_level", "Low")

    # --- Home location exposure ---
    if home_result.get("detected"):
        conf = home_result.get("confidence", 0)
        if conf >= 70:
            recs.append({
                "title": "Enable Privacy Zones",
                "description": (
                    f"Your home location was detected with {conf}% confidence from route start/end points. "
                    "Enable privacy zones (available in Strava, Garmin Connect, and Wahoo) to hide the first "
                    "and last 200–500 metres of every activity before sharing."
                ),
                "priority": "Critical",
                "icon": "🏠",
            })
        else:
            recs.append({
                "title": "Consider Privacy Zones",
                "description": (
                    "Your probable home location was identified from route patterns. "
                    "Setting a privacy zone of at least 300 metres around your home prevents "
                    "third parties from pinpointing your residence."
                ),
                "priority": "High",
                "icon": "🏠",
            })

    # --- Repeated routes ---
    if repeated_result.get("repeated_count", 0) >= 3:
        recs.append({
            "title": "Vary Your Routes",
            "description": (
                f"{repeated_result['repeated_count']} repeated route instances were detected. "
                "Running or cycling the same path at predictable times creates exploitable patterns. "
                "Alternate between at least three different routes and occasionally reverse your direction."
            ),
            "priority": "High",
            "icon": "🔄",
        })

    # --- Routine patterns ---
    if routine_result.get("routine_level") in ("Medium", "High"):
        patterns = routine_result.get("patterns", [])
        pattern_str = "; ".join(patterns[:2]) if patterns else "regular timing patterns"
        recs.append({
            "title": "Randomise Activity Timing",
            "description": (
                f"Strong temporal patterns were detected ({pattern_str}). "
                "Predictable timing combined with a known route allows physical surveillance. "
                "Vary your start times by at least 30–60 minutes and mix workout days."
            ),
            "priority": "Medium",
            "icon": "⏰",
        })

    # --- Frequent locations ---
    if len(frequent_locations) >= 3:
        recs.append({
            "title": "Restrict Visibility of Frequented Areas",
            "description": (
                f"{len(frequent_locations)} frequently visited location clusters were identified from your GPS data. "
                "Review your platform's segment privacy settings and avoid recording routes that directly pass "
                "sensitive locations such as workplaces, medical facilities, or schools."
            ),
            "priority": "Medium",
            "icon": "📍",
        })

    # --- General recommendations ---
    recs.append({
        "title": "Audit Public Activity Sharing",
        "description": (
            "Review which activities are set to public on your fitness platform. "
            "Consider setting past activities to followers-only or private, particularly those "
            "starting or ending near your home."
        ),
        "priority": "Medium",
        "icon": "👁️",
    })

    if risk_level == "High":
        recs.append({
            "title": "Disable Live Tracking Features",
            "description": (
                "With a High risk score, live tracking features (Strava Beacon, Garmin LiveTrack) "
                "may expose your real-time location to a wider audience than intended. "
                "Limit sharing to verified contacts only."
            ),
            "priority": "High",
            "icon": "📡",
        })

    recs.append({
        "title": "Review Third-Party App Access",
        "description": (
            "Fitness platforms often permit third-party apps to access your full GPS history. "
            "Audit connected apps in your account settings and revoke access for any you no longer use."
        ),
        "priority": "Low",
        "icon": "🔗",
    })

    # Sort by priority
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    recs.sort(key=lambda r: priority_order.get(r["priority"], 99))

    return recs
