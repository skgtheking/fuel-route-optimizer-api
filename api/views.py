from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

from .services import geocode_location, get_route, find_fuel_stops
from .map_generator import generate_route_map

class OptimalFuelRouteView(APIView):
    def get(self, request):
        start = request.query_params.get("start")
        finish = request.query_params.get("finish")
        view_type = request.query_params.get("view", "json").lower()

        if not start or not finish:
            return Response(
                {"error": "Both 'start' and 'finish' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_coords = geocode_location(start)
            finish_coords = geocode_location(finish)
            coordinates, total_distance = get_route(start_coords, finish_coords)
            stops, total_cost = find_fuel_stops(coordinates, total_distance)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if view_type == "map":
            html_content = generate_route_map(coordinates, stops, start, finish)
            return HttpResponse(html_content, content_type="text/html")

        route_geojson = {
            "type": "LineString",
            "coordinates": coordinates
        }

        return Response({
            "start": start,
            "finish": finish,
            "total_distance_miles": round(total_distance, 2),
            "total_fuel_cost": round(total_cost, 2),
            "fuel_stops_count": len(stops),
            "fuel_stops": stops,
            "route_geojson": route_geojson,
            "map_view_url": f"{request.build_absolute_uri(request.path)}?start={start}&finish={finish}&view=map"
        }, status=status.HTTP_200_OK)