"""
route_analyzer.py - Repeated Route & Routine Pattern Detection
Detects similar routes, time-based routines, and frequent location clusters.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from collections import Counter
from typing import Optional


EARTH_RADIUS_KM = 6371.0
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _route_fingerprint(route: dict, n_bins: int = 8) -> Optional[np.ndarray]:
    """
    Create a compact spatial fingerprint for a route by sampling n evenly-spaced
    points and encoding their lat/lon as a flattened vector.
    """
    points = route.get("points")
    if points is None or len(points) < 2:
        return None
    indices = np.linspace(0, len(points) - 1, n_bins, dtype=int)
    sampled = points.iloc[indices][["latitude", "longitude"]].values
    return sampled.flatten()


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def detect_repeated_routes(routes: list[dict], similarity_threshold: float = 0.9998) -> dict:
    """
    Identify repeated routes by comparing spatial fingerprints.
    
    Returns:
        dict with: repeated_count, repeated_groups (list of route name lists),
                   max_repetitions, most_repeated_name
    """
    if len(routes) < 2:
        return {"repeated_count": 0, "repeated_groups": [], "max_repetitions": 0}

    fingerprints = [(i, _route_fingerprint(r)) for i, r in enumerate(routes)]
    fingerprints = [(i, fp) for i, fp in fingerprints if fp is not None]

    groups = []
    used = set()

    for i, (idx_a, fp_a) in enumerate(fingerprints):
        if idx_a in used:
            continue
        group = [idx_a]
        for j, (idx_b, fp_b) in enumerate(fingerprints):
            if i == j or idx_b in used:
                continue
            if len(fp_a) == len(fp_b):
                sim = _cosine_similarity(fp_a, fp_b)
                if sim >= similarity_threshold:
                    group.append(idx_b)
        if len(group) > 1:
            for g in group:
                used.add(g)
            groups.append([routes[idx]["name"] for idx in group])

    repeated_count = sum(len(g) for g in groups)
    max_rep = max((len(g) for g in groups), default=0)
    most_repeated = groups[0][0] if groups else None

    return {
        "repeated_count": repeated_count,
        "repeated_groups": groups,
        "max_repetitions": max_rep,
        "most_repeated_name": most_repeated,
    }


def detect_routines(routes: list[dict]) -> dict:
    """
    Analyze timestamps to detect time-based movement patterns.
    
    Returns:
        dict with: routine_level, patterns (list), peak_hour, dominant_weekday
    """
    hours = []
    weekdays = []
    dates = []

    for r in routes:
        st = r.get("start_time")
        if st:
            hours.append(st.hour)
            weekdays.append(st.weekday())
            dates.append(st.date())

    if not hours:
        return {"routine_level": "Unknown", "patterns": [], "peak_hour": None}

    patterns = []

    # --- Hour analysis ---
    hour_counts = Counter(hours)
    peak_hour, peak_count = hour_counts.most_common(1)[0]
    hour_ratio = peak_count / len(hours)
    if hour_ratio >= 0.6:
        suffix = "AM" if peak_hour < 12 else "PM"
        h12 = peak_hour if peak_hour <= 12 else peak_hour - 12
        h12 = h12 or 12
        patterns.append(f"Consistent activity at {h12}:00 {suffix} ({int(hour_ratio*100)}% of sessions)")

    # --- Weekday analysis ---
    if weekdays:
        wd_counts = Counter(weekdays)
        peak_wd, peak_wd_count = wd_counts.most_common(1)[0]
        wd_ratio = peak_wd_count / len(weekdays)
        if wd_ratio >= 0.35:
            patterns.append(f"Most active on {WEEKDAY_NAMES[peak_wd]} ({peak_wd_count} sessions)")

    # --- Frequency analysis ---
    if len(dates) >= 3:
        unique_dates = sorted(set(dates))
        gaps = [(unique_dates[i+1] - unique_dates[i]).days for i in range(len(unique_dates)-1)]
        avg_gap = np.mean(gaps)
        if avg_gap <= 2.0:
            patterns.append(f"High frequency activity: avg {avg_gap:.1f} days between sessions")
        elif avg_gap <= 4.0:
            patterns.append(f"Regular activity: avg {avg_gap:.1f} days between sessions")

    # --- Routine level ---
    score = len(patterns)
    if score == 0:
        routine_level = "Low"
    elif score == 1:
        routine_level = "Medium"
    else:
        routine_level = "High"

    return {
        "routine_level": routine_level,
        "patterns": patterns,
        "peak_hour": peak_hour,
        "dominant_weekday": WEEKDAY_NAMES[max(Counter(weekdays), key=Counter(weekdays).get)] if weekdays else None,
    }


def detect_frequent_locations(routes: list[dict], radius_m: float = 200.0, min_visits: int = 2) -> list[dict]:
    """
    Cluster ALL GPS points to find frequently visited locations.
    
    Returns:
        List of location cluster dicts with: label, latitude, longitude, visit_count
    """
    all_coords = []
    for r in routes:
        pts = r.get("points")
        if pts is not None:
            all_coords.extend(pts[["latitude", "longitude"]].values.tolist())

    if len(all_coords) < min_visits:
        return []

    coords = np.array(all_coords)
    coords_rad = np.radians(coords)
    eps_rad = (radius_m / 1000.0) / EARTH_RADIUS_KM

    db = DBSCAN(eps=eps_rad, min_samples=min_visits, algorithm="ball_tree", metric="haversine")
    labels = db.fit_predict(coords_rad)

    label_counts = Counter(l for l in labels if l >= 0)
    clusters = []
    for label, count in label_counts.most_common(6):  # top 6 locations
        idxs = np.where(labels == label)[0]
        pts = coords[idxs]
        clusters.append({
            "label": f"Location Cluster {label + 1}",
            "latitude": float(np.mean(pts[:, 0])),
            "longitude": float(np.mean(pts[:, 1])),
            "visit_count": count,
        })

    return clusters
