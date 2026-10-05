# Fuel Route Optimizer API

A production-ready Django REST Framework service that computes the optimal driving route between any two locations within the USA, pinpoints cost-effective fuel stops based on vehicle constraints (500-mile maximum range, 10 MPG fuel economy), calculates total fuel expenses, and generates an interactive map visualization.

## Key Highlights & Performance Optimizations

### 1. Strictly Minimal External API Calls

* Makes exactly **one routing request** to the Open Source Routing Machine (OSRM) driving API to extract the full driving geometry, total distance, and step coordinates.
* Geocoding of start and finish points is resolved using OpenStreetMap Nominatim.

### 2. Ultra-Fast Sub-Second Spatial Indexing

* Pre-geocoded fuel stops (~7,000+ national locations) are held in memory and indexed using `scipy.spatial.cKDTree`.
* Candidate station searches along route polylines execute in sub-10 milliseconds via fast spatial radius filtering.

### 3. Fuel Optimization Logic

* Vehicle maximum range: **500 miles**
* Fuel efficiency: **10 miles per gallon (MPG)**
* Implements a forward-looking windowing algorithm that scans reachable fuel stations along the route corridor prior to empty-tank limits.
* Greedily selects the lowest retail fuel price (`$/gal`) to minimize overall journey fuel expenditure.

---

## Tech Stack & Dependencies

* **Framework:** Python 3.x, Django 5.x / 6.x, Django REST Framework
* **Spatial & Math Computing:** `scipy`, `numpy`, `pandas`, `geopy`
* **Mapping & Routing:** OSRM (Open Source Routing Machine), Folium, Esri World Street Map Tiles

---

## Project Structure

```text
fuel-route-api/
├── api/
│   ├── map_generator.py           # Folium map builder (route polyline & station markers)
│   ├── services.py                # OSRM routing, KDTree spatial query, and fuel optimizer
│   ├── urls.py                    # App route definitions
│   └── views.py                   # API controller (handles JSON and Map view formats)
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── fuel_prices_with_coordinates.csv # Geocoded fuel station dataset
├── manage.py
├── requirements.txt
└── README.md
```

---

## Installation & Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<YOUR_USERNAME>/fuel-route-api.git
cd fuel-route-api
```

### 2. Create and Activate a Virtual Environment

#### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migrations & Start Development Server

```bash
python manage.py migrate
python manage.py runserver
```

The application will be available at:

```text
http://127.0.0.1:8000/
```

---

## API Documentation

### Route Optimization Endpoint

**Endpoint:**

```http
GET /api/route/
```

### Query Parameters

| Parameter | Type   | Required | Description                                                                                |
| --------- | ------ | -------- | ------------------------------------------------------------------------------------------ |
| `start`   | string | Yes      | Starting city or address within the USA.                                                   |
| `finish`  | string | Yes      | Destination city or address within the USA.                                                |
| `view`    | string | No       | Response mode. Defaults to `json`. Set to `map` to render an interactive HTML Leaflet map. |

### Example Parameters

```text
start=New York, NY
finish=Los Angeles, CA
view=json
```

---

## Example 1: JSON API Request

### HTTP

```http
GET /api/route/?start=New%20York,%20NY&finish=Los%20Angeles,%20CA HTTP/1.1
Host: 127.0.0.1:8000
```

### cURL

```bash
curl "http://127.0.0.1:8000/api/route/?start=New%20York,%20NY&finish=Los%20Angeles,%20CA"
```

### Sample Response

**Status: `200 OK`**

```json
{
  "start": "New York, NY",
  "finish": "Los Angeles, CA",
  "total_distance_miles": 2794.02,
  "total_fuel_cost": 888.52,
  "fuel_stops_count": 11,
  "fuel_stops": [
    {
      "truckstop_name": "MOBIL",
      "address": "US-46",
      "city": "Columbia",
      "state": "NJ",
      "latitude": 40.926,
      "longitude": -75.0945,
      "retail_price": 3.079,
      "mile_marker": 75.0,
      "gallons": 7.5,
      "cost": 23.09
    },
    {
      "truckstop_name": "TURNPIKE MARKET EXPRESS",
      "address": "SR-5",
      "city": "Newton Falls",
      "state": "OH",
      "latitude": 41.1889,
      "longitude": -80.9711,
      "retail_price": 3.259,
      "mile_marker": 400.0,
      "gallons": 32.5,
      "cost": 105.92
    }
  ],
  "route_geojson": {
    "type": "LineString",
    "coordinates": [
      [-74.006, 40.7128],
      [-74.015, 40.7152]
    ]
  },
  "map_view_url": "http://127.0.0.1:8000/api/route/?start=New%20York,%20NY&finish=Los%20Angeles,%20CA&view=map"
}
```

---

## Example 2: Interactive Map Visualization

To view the interactive route map, open:

```text
http://127.0.0.1:8000/api/route/?start=New%20York,%20NY&finish=Los%20Angeles,%20CA&view=map
```

The map provides the following visualizations:

* 🟢 **Green Marker:** Starting location
* ⚫ **Black Marker:** Finish destination
* 🔵 **Blue Polyline:** Exact OSRM road driving route
* 🔴 **Red Fuel Pins:** Optimal fuel stations selected by the optimization algorithm

Clicking a fuel station marker displays an inspection popup containing:

* Station name
* Address and location
* Fuel price (`$/gal`)
* Required gallons pumped
* Cost of the individual fuel stop

---

## How the Optimization Works

The service uses a constrained greedy fuel-selection strategy.

1. The start and destination locations are geocoded using **OpenStreetMap Nominatim**.
2. A single request is sent to **OSRM** to calculate the complete driving route.
3. The returned route geometry is converted into a sequence of geographic coordinates.
4. Fuel stations are indexed using **SciPy's `cKDTree`** spatial index.
5. Stations near the route corridor are retrieved using fast spatial radius queries.
6. The route is converted into cumulative mileage markers.
7. At each point where refueling is required, the algorithm examines stations reachable within the vehicle's remaining range.
8. The lowest-priced suitable station within the forward-looking window is selected.
9. The process continues until the destination is reachable.
10. Total gallons purchased and total fuel expenditure are calculated.
11. The final route and selected fuel stops are returned as JSON or rendered as an interactive Folium map.

### Vehicle Constraints

| Constraint            |            Value |
| --------------------- | ---------------: |
| Maximum driving range |        500 miles |
| Fuel economy          |           10 MPG |
| Maximum fuel capacity |       50 gallons |
| Fuel consumption      | 0.1 gallons/mile |

---

## Performance

The application is designed to minimize expensive external operations while keeping route and fuel-stop calculations fast.

### External Requests

* **OSRM:** One routing request per route
* **Nominatim:** Geocoding for start and destination
* Fuel station searches are performed locally against the pre-geocoded dataset.

### Spatial Search

The fuel station dataset contains approximately **7,000+ locations**.

Instead of scanning every station for every route segment, the service uses:

```python
scipy.spatial.cKDTree
```

This allows nearby fuel stations to be located using efficient spatial queries.

---

## Response Modes

The API supports two response modes.

### JSON

The default response mode provides structured route and optimization data:

```text
GET /api/route/?start=New%20York,%20NY&finish=Los%20Angeles,%20CA
```

### Interactive Map

Set `view=map` to render the route as an interactive Leaflet/Folium map:

```text
GET /api/route/?start=New%20York,%20NY&finish=Los%20Angeles,%20CA&view=map
```

---

## Technologies

| Technology              | Purpose                         |
| ----------------------- | ------------------------------- |
| Python                  | Core application language       |
| Django                  | Web framework                   |
| Django REST Framework   | REST API                        |
| NumPy                   | Numerical computations          |
| SciPy                   | KDTree spatial indexing         |
| Pandas                  | Fuel station dataset processing |
| GeoPy                   | Geocoding utilities             |
| OSRM                    | Road routing                    |
| OpenStreetMap Nominatim | Address geocoding               |
| Folium                  | Interactive map generation      |
| Leaflet                 | Interactive map rendering       |
| Esri World Street Map   | Map tiles                       |

---

## Project Structure

```text
fuel-route-api/
│
├── api/
│   ├── map_generator.py
│   ├── services.py
│   ├── urls.py
│   └── views.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── fuel_prices_with_coordinates.csv
├── manage.py
├── requirements.txt
└── README.md
```

---

## Notes

This project is designed for routing and fuel-cost optimization within the United States.

The accuracy of the final fuel-stop recommendations depends on:

* The accuracy and freshness of the fuel station dataset.
* Current retail fuel prices contained in the dataset.
* OSRM routing results.
* Nominatim geocoding accuracy.
* The assumption of a **500-mile maximum vehicle range**.
* The assumption of **10 MPG fuel economy**.

The optimization operates on the available fuel station data and does not make live requests to individual fuel stations during route calculation.
