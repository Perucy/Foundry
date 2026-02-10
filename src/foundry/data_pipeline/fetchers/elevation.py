from typing import NamedTuple
import requests

class ElevationResult(NamedTuple):
    """ Elevation and terrain data for a location """
    elevation_meters: float
    latitude: float
    longitude: float

class ElevationService:
    """ Open-Elevation API service for terrain data """
    def __init__(self):
        self.base_url = "https://api.open-elevation.com/api/v1/lookup"

    def get_elevation(self, lat: float, lon: float) -> ElevationResult:
        params = {
            "locations": f"{lat},{lon}"
        }

        response = requests.get(self.base_url, params=params)
        response.raise_for_status()

        data = response.json()
        result = data["results"][0]

        return ElevationResult(
            elevation_meters=result["elevation"],
            latitude=result["latitude"],
            longitude=result["longitude"]
        )
    
    def get_elevation_grid(self, bounds: dict, grid_size: int = 5) -> list[ElevationResult]:
        if not bounds:
            raise ValueError("Bounds required for grid sampling")
        
        ne = bounds["northeast"]
        sw = bounds["southwest"]

        # Create grid of lat/lon points
        lat_step = (ne["lat"] - sw["lat"]) / (grid_size - 1)
        lon_step = (ne["lng"] - sw["lng"]) / (grid_size - 1)
        
        locations = []
        for i in range(grid_size):
            for j in range(grid_size):
                lat = sw["lat"] + (i * lat_step)
                lon = sw["lng"] + (j * lon_step)
                locations.append(f"{lat},{lon}")
        
        # Open-Elevation supports batch requests
        params = {
            "locations": "|".join(locations)
        }
        
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        return [
            ElevationResult(
                elevation_meters=r["elevation"],
                latitude=r["latitude"],
                longitude=r["longitude"]
            )
            for r in data["results"]
        ]