"""
map_visualizer.py - Interactive Route Map Generator
Renders all routes, home location, and frequent location clusters using Folium.
"""

import folium
from folium.plugins import MarkerCluster
import numpy as np


# Colour palette for routes (cycles for many routes)
ROUTE_COLOURS = [
    "#6366f1", "#f59e0b", "#10b981", "#ef4444",
    "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16",
]


def build_map(
    routes: list[dict],
    home_result: dict,
    frequent_locations: list,
) -> folium.Map:
    """
    Build an interactive Folium map with:
      - All GPS route polylines
      - Start (green) and end (red) markers per route
      - Probable home marker (if detected)
      - Frequent location cluster markers

    Returns:
        folium.Map object
    """
    # Determine map centre from all route start points
    all_lats, all_lons = [], []
    for r in routes:
        pts = r.get("points")
        if pts is not None:
            all_lats.extend(pts["latitude"].tolist())
            all_lons.extend(pts["longitude"].tolist())

    if all_lats:
        centre = (np.mean(all_lats), np.mean(all_lons))
    else:
        centre = (51.5074, -0.1278)  # Default: London

    m = folium.Map(
        location=centre,
        zoom_start=14,
        tiles="CartoDB dark_matter",
        prefer_canvas=True,
    )

    # --- Draw routes ---
    for i, route in enumerate(routes):
        pts = route.get("points")
        if pts is None or len(pts) < 2:
            continue

        colour = ROUTE_COLOURS[i % len(ROUTE_COLOURS)]
        coords = list(zip(pts["latitude"], pts["longitude"]))

        folium.PolyLine(
            locations=coords,
            color=colour,
            weight=3,
            opacity=0.85,
            tooltip=route.get("name", f"Route {i+1}"),
        ).add_to(m)

        # Start marker
        start = route["start_point"]
        folium.CircleMarker(
            location=start,
            radius=6,
            color="#22c55e",
            fill=True,
            fill_color="#22c55e",
            fill_opacity=0.9,
            tooltip=f"Start: {route.get('name', '')}",
        ).add_to(m)

        # End marker
        end = route["end_point"]
        folium.CircleMarker(
            location=end,
            radius=6,
            color="#ef4444",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.9,
            tooltip=f"End: {route.get('name', '')}",
        ).add_to(m)

    # --- Home location marker ---
    if home_result.get("detected"):
        home_lat = home_result["latitude"]
        home_lon = home_result["longitude"]
        conf = home_result.get("confidence", 0)

        folium.Marker(
            location=(home_lat, home_lon),
            popup=folium.Popup(
                f"<b>⚠️ Probable Home Location</b><br>Confidence: {conf}%<br>"
                f"Detected from {home_result.get('cluster_size', '?')} endpoint(s)",
                max_width=220,
            ),
            tooltip=f"Probable Home ({conf}% confidence)",
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(m)

        # Privacy zone circle (300m)
        folium.Circle(
            location=(home_lat, home_lon),
            radius=300,
            color="#ef4444",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.08,
            tooltip="Recommended privacy zone (300m)",
            dash_array="6",
        ).add_to(m)

    # --- Frequent location markers ---
    for loc in frequent_locations:
        folium.CircleMarker(
            location=(loc["latitude"], loc["longitude"]),
            radius=10,
            color="#f59e0b",
            fill=True,
            fill_color="#f59e0b",
            fill_opacity=0.5,
            tooltip=f"{loc['label']} — {loc['visit_count']} visits",
            popup=folium.Popup(
                f"<b>{loc['label']}</b><br>Estimated visits: {loc['visit_count']}",
                max_width=180,
            ),
        ).add_to(m)

    # --- Legend ---
    legend_html = """
    <div style="
        position: fixed; bottom: 30px; left: 30px;
        background: rgba(15,15,25,0.88);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 10px;
        padding: 12px 16px;
        font-family: monospace;
        font-size: 12px;
        color: #e5e7eb;
        z-index: 9999;
        line-height: 1.8;
    ">
        <b style="color:#6366f1">ShadowRoute Map Legend</b><br>
        <span style="color:#22c55e">●</span> Route start<br>
        <span style="color:#ef4444">●</span> Route end / Home detection<br>
        <span style="color:#f59e0b">●</span> Frequent location cluster<br>
        <span style="color:#6366f1">─</span> Route path
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def map_to_html(m: folium.Map) -> str:
    """Return the map as an HTML string for embedding in Streamlit."""
    return m._repr_html_()
