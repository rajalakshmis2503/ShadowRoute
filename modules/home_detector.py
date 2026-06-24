"""
home_detector.py - Probable Home Location Detection
Uses DBSCAN clustering on route start/end points to identify likely residence.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from collections import Counter
from typing import Optional


# Earth radius in km for Haversine-based epsilon
EARTH_RADIUS_KM = 6371.0


def _to_radians(coords: np.ndarray) -> np.ndarray:
    return np.radians(coords)


def detect_home(routes: list[dict], radius_m: float = 150.0, min_samples: int = 2) -> dict:
    """
    Identify the most probable home location from route starting points.
    
    Logic:
      - Collect all start points (and end points, since many runs return home).
      - Apply DBSCAN with haversine metric.
      - The largest cluster centroid is flagged as probable home.
    
    Args:
        routes: List of parsed route dicts from parser.py
        radius_m: Maximum distance (metres) to form a cluster
        min_samples: Minimum routes in cluster to qualify
    
    Returns:
        dict with: detected (bool), latitude, longitude, confidence, cluster_size
    """
    if not routes:
        return {"detected": False}

    # Gather start + end points
    endpoints = []
    for r in routes:
        if r.get("start_point"):
            endpoints.append(r["start_point"])
        if r.get("end_point"):
            endpoints.append(r["end_point"])

    if len(endpoints) < 2:
        return {"detected": False}

    coords = np.array(endpoints)
    coords_rad = _to_radians(coords)

    # epsilon in radians from metres
    epsilon_rad = (radius_m / 1000.0) / EARTH_RADIUS_KM

    db = DBSCAN(eps=epsilon_rad, min_samples=min_samples, algorithm="ball_tree", metric="haversine")
    labels = db.fit_predict(coords_rad)

    if max(labels) < 0:
        # No clusters found
        return {"detected": False}

    # Find the largest non-noise cluster
    label_counts = Counter(l for l in labels if l >= 0)
    dominant_label = label_counts.most_common(1)[0][0]
    cluster_indices = np.where(labels == dominant_label)[0]
    cluster_points = coords[cluster_indices]

    centroid_lat = float(np.mean(cluster_points[:, 0]))
    centroid_lon = float(np.mean(cluster_points[:, 1]))

    cluster_size = len(cluster_indices)
    total_endpoints = len(endpoints)

    # Confidence: ratio of endpoints in home cluster vs total
    confidence = round(min(cluster_size / total_endpoints * 100, 99), 1)

    return {
        "detected": True,
        "latitude": centroid_lat,
        "longitude": centroid_lon,
        "confidence": confidence,
        "cluster_size": cluster_size,
        "total_endpoints": total_endpoints,
    }
