import googlemaps
from datetime import datetime
import requests
from foundry.config.settings import settings
from typing import NamedTuple, Optional

class GeocodeResult(NamedTuple):
    lat: float
    lon: float
    formatted_address: str
    place_id: str
    bounds: dict
    location_type: str

class GeocodingService:
    """ Geocoding service (city name, address, etc to coordinates )"""

    def __init__(self, provider: str= "google"):
        self.provider = provider
        self.api_key = settings.google_api_key
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    def geocode(self, location_name: str) -> GeocodeResult:
        params = {
            "address": location_name,
            "key": self.api_key
        }

        response = requests.get(self.base_url, params=params)
        response.raise_for_status()

        data = response.json()

        if data["status"] != "OK":
            raise ValueError(f"Geocoding failed: {data['status']}")
        

        result = data["results"][0]
        geometry = result["geometry"]
        
        return GeocodeResult(
            lat=geometry["location"]["lat"],
            lon=geometry["location"]["lng"],
            formatted_address=result["formatted_address"],
            place_id=result["place_id"],
            bounds=geometry.get("bounds", {}),  # Some locations might not have bounds
            location_type=geometry["location_type"]
        )
    
        # alternative using googlemaps library
        # gmaps = googlemaps.Client(key=self.api_key)

        # geocode an address
        # geocode_result = gmaps.geocode(location_name)

        # print(geocode_result)



