import folium

def generate_route_map(coordinates, stops, start_location, finish_location):
    m = folium.Map(
        location=[coordinates[0][1], coordinates[0][0]],
        zoom_start=5,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, HERE, Garmin, USGS, Intermap, INCREMENT P, NRCan, Esri Japan, METI, Esri China (Hong Kong), Esri Korea, Esri (Thailand), NGCC, (c) OpenStreetMap contributors, and the GIS User Community"
    )

    route_points = [(lat, lon) for lon, lat in coordinates]
    folium.PolyLine(route_points, color="#0052CC", weight=5, opacity=0.85).add_to(m)

    folium.Marker(
        location=route_points[0],
        popup=f"Start: {start_location}",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)

    folium.Marker(
        location=route_points[-1],
        popup=f"Finish: {finish_location}",
        icon=folium.Icon(color="black", icon="stop")
    ).add_to(m)

    for i, s in enumerate(stops, start=1):
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 13px; line-height: 1.4;">
            <b>Stop #{i}: {s['truckstop_name']}</b><br>
            <b>Address:</b> {s['address']}, {s['city']}, {s['state']}<br>
            <b>Price:</b> ${s['retail_price']:.3f} / gal<br>
            <b>Gallons:</b> {s['gallons']} gal<br>
            <b>Cost:</b> ${s['cost']:.2f}<br>
            <b>Route Mile:</b> {s['mile_marker']} mi
        </div>
        """
        folium.Marker(
            location=[s["latitude"], s["longitude"]],
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(color="red", icon="tint")
        ).add_to(m)

    m.fit_bounds([route_points[0], route_points[-1]])
    return m._repr_html_()