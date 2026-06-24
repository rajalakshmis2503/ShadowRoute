"""
parser.py - GPX File Parser Module
Extracts GPS coordinates, timestamps, and metadata from GPX files.
"""

import gpxpy
import gpxpy.gpx
import pandas as pd
from datetime import datetime
from typing import Optional


def parse_gpx_file(file_path_or_bytes) -> dict:
    """
    Parse a GPX file and return structured data.
    
    Args:
        file_path_or_bytes: File path string or bytes-like object (from Streamlit uploader)
    
    Returns:
        dict with keys: name, points (DataFrame), start_point, end_point,
                        total_distance_km, duration_minutes, start_time
    """
    # Handle both file paths and bytes objects (Streamlit uploads)
    if isinstance(file_path_or_bytes, (str, bytes)):
        if isinstance(file_path_or_bytes, str):
            with open(file_path_or_bytes, 'r') as f:
                gpx = gpxpy.parse(f)
        else:
            import io
            gpx = gpxpy.parse(io.BytesIO(file_path_or_bytes))
    else:
        # Streamlit UploadedFile or file-like object
        gpx = gpxpy.parse(file_path_or_bytes)

    records = []
    track_name = "Unknown Route"

    for track in gpx.tracks:
        if track.name:
            track_name = track.name
        for segment in track.segments:
            for point in segment.points:
                records.append({
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "elevation": point.elevation,
                    "time": point.time,
                    # Extract hour for routine analysis
                    "hour": point.time.hour if point.time else None,
                    "weekday": point.time.weekday() if point.time else None,
                    "date": point.time.date() if point.time else None,
                })

    if not records:
        return None

    df = pd.DataFrame(records)

    # Calculate total distance using the gpxpy built-in
    total_distance = 0.0
    for track in gpx.tracks:
        total_distance += track.length_2d() or 0.0
    total_distance_km = total_distance / 1000.0

    # Duration
    start_time = df["time"].iloc[0] if not df["time"].isnull().all() else None
    end_time = df["time"].iloc[-1] if not df["time"].isnull().all() else None
    duration_minutes = None
    if start_time and end_time:
        duration_minutes = (end_time - start_time).total_seconds() / 60.0

    return {
        "name": track_name,
        "points": df,
        "start_point": (df["latitude"].iloc[0], df["longitude"].iloc[0]),
        "end_point": (df["latitude"].iloc[-1], df["longitude"].iloc[-1]),
        "total_distance_km": round(total_distance_km, 2),
        "duration_minutes": round(duration_minutes, 1) if duration_minutes else None,
        "start_time": start_time,
        "point_count": len(df),
    }


def parse_multiple_gpx(file_list) -> list[dict]:
    """
    Parse a list of GPX files.
    
    Args:
        file_list: List of file paths or Streamlit UploadedFile objects
    
    Returns:
        List of parsed route dicts (None entries skipped)
    """
    parsed = []
    for f in file_list:
        result = parse_gpx_file(f)
        if result:
            parsed.append(result)
    return parsed
