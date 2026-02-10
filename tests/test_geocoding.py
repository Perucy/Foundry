from foundry.config.settings import settings
from foundry.data_pipeline.fetchers.geocoding import GeocodingService

def test_geocoding_service():
    geocoding_service = GeocodingService()
    coordinates = geocoding_service.geocode("Ukonga, Dar es Salaam, Tanzania")
    print(type(coordinates))
    print(coordinates)

if __name__ == "__main__":
    test_geocoding_service()