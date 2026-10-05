import os
import math
import numpy as np
import pandas as pd
import requests
from geopy.geocoders import Nominatim
from scipy.spatial import cKDTree

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fuel_prices_with_coordinates.csv")
stations_df = pd.read_csv(DATA_PATH)

station_coords = np.radians(stations_df[["latitude", "longitude"]].values)
station_tree = cKDTree(station_coords)

EARTH_RADIUS_MILES = 3958.8
MAX_RANGE_MILES = 500.0
MPG = 10.0


def geocode_location(address: str):
    geolocator = Nominatim(user_agent="spotter_fuel_planner_app")
    location = geolocator.geocode(f"{address}, USA", timeout=10)
    if not location:
        raise ValueError(f"Could not find coordinates for: {address}")
    return location.latitude, location.longitude


def get_route(start_coord, end_coord):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_coord[1]},{start_coord[0]};{end_coord[1]},{end_coord[0]}?overview=full&geometries=geojson"
    resp = requests.get(url, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError("Failed to retrieve route from OSRM service.")
    
    data = resp.json()
    if not data.get("routes"):
        raise ValueError("No route found between points.")
    
    route = data["routes"][0]
    total_distance_miles = route["distance"] / 1609.344
    coordinates = route["geometry"]["coordinates"]
    return coordinates, total_distance_miles


def haversine_miles(lat1, lon1, lat2, lon2):
    r = EARTH_RADIUS_MILES
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * r * math.asin(math.sqrt(a))


def find_fuel_stops(coordinates, total_distance):
    cum_dist = [0.0]
    for i in range(1, len(coordinates)):
        lon1, lat1 = coordinates[i - 1]
        lon2, lat2 = coordinates[i]
        d = haversine_miles(lat1, lon1, lat2, lon2)
        cum_dist.append(cum_dist[-1] + d)

    sample_targets = np.arange(0, total_distance, 25.0)
    sampled_indices = [np.searchsorted(cum_dist, t) for t in sample_targets]
    sampled_coords = [coordinates[min(idx, len(coordinates) - 1)] for idx in sampled_indices]

    query_rad = np.radians([[lat, lon] for lon, lat in sampled_coords])
    
    radius_rad = 10.0 / EARTH_RADIUS_MILES
    nearby_indices = set()
    for indices in station_tree.query_ball_point(query_rad, radius_rad):
        nearby_indices.update(indices)

    if not nearby_indices:
        radius_rad = 25.0 / EARTH_RADIUS_MILES
        for indices in station_tree.query_ball_point(query_rad, radius_rad):
            nearby_indices.update(indices)

    candidate_stations = stations_df.iloc[list(nearby_indices)].copy()
    if candidate_stations.empty:
        return [], 0.0

    cand_rad = np.radians(candidate_stations[["latitude", "longitude"]].values)
    _, nearest_sample_idx = cKDTree(query_rad).query(cand_rad)
    candidate_stations["route_mile"] = [sample_targets[idx] for idx in nearest_sample_idx]
    candidate_stations = candidate_stations.sort_values(by="route_mile").reset_index(drop=True)

    stops = []
    current_fuel_reach = MAX_RANGE_MILES
    last_stop_mile = 0.0

    while current_fuel_reach < total_distance:
        valid = candidate_stations[
            (candidate_stations["route_mile"] > last_stop_mile + 10) &
            (candidate_stations["route_mile"] <= current_fuel_reach - 30)
        ]

        if valid.empty:
            valid = candidate_stations[
                (candidate_stations["route_mile"] > last_stop_mile) &
                (candidate_stations["route_mile"] <= current_fuel_reach)
            ]

        if valid.empty:
            fallback = candidate_stations[candidate_stations["route_mile"] > last_stop_mile]
            if fallback.empty:
                break
            best_stop = fallback.iloc[0]
        else:
            best_stop = valid.sort_values(by="Retail Price").iloc[0]

        leg_distance = best_stop["route_mile"] - last_stop_mile
        gallons_needed = leg_distance / MPG
        fuel_cost = gallons_needed * best_stop["Retail Price"]

        stops.append({
            "truckstop_name": best_stop["Truckstop Name"],
            "address": best_stop["Address"],
            "city": best_stop["City"],
            "state": best_stop["State"],
            "latitude": float(best_stop["latitude"]),
            "longitude": float(best_stop["longitude"]),
            "retail_price": round(float(best_stop["Retail Price"]), 3),
            "mile_marker": round(float(best_stop["route_mile"]), 1),
            "gallons": round(gallons_needed, 2),
            "cost": round(fuel_cost, 2)
        })

        last_stop_mile = best_stop["route_mile"]
        current_fuel_reach = last_stop_mile + MAX_RANGE_MILES

    final_leg_distance = total_distance - last_stop_mile
    final_gallons = final_leg_distance / MPG
    final_price = stops[-1]["retail_price"] if stops else float(candidate_stations["Retail Price"].mean())
    final_cost = final_gallons * final_price

    total_money_spent = sum(s["cost"] for s in stops) + round(final_cost, 2)

    return stops, round(total_money_spent, 2)