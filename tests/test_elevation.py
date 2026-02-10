from foundry.config.settings import settings
from foundry.data_pipeline.fetchers.elevation import ElevationService
from foundry.data_pipeline.fetchers.geocoding import GeocodingService
from pprint import pprint

def test_elevation_single_point():
    elevation_service = ElevationService()
    result = elevation_service.get_elevation(-6.8165054, 39.2894367)

    print("\n=== Single Point Elevation ===")
    pprint(result._asdict())
    
    # Dar es Salaam is coastal, should be low elevation
    assert 0 <= result.elevation_meters <= 100

def test_elevation_grid():
    """Test elevation grid across entire city"""
    geocoder = GeocodingService()
    elevation = ElevationService()
    
    # Get city bounds
    geo_result = geocoder.geocode("Dar es Salaam, Tanzania")
    
    # Sample 3x3 grid (9 points)
    grid = elevation.get_elevation_grid(geo_result.bounds, grid_size=3)
    
    print("\n=== Elevation Grid ===")
    print(f"City: {geo_result.formatted_address}")
    print(f"Points sampled: {len(grid)}")
    print(f"Elevation range: {min(g.elevation_meters for g in grid):.1f}m - {max(g.elevation_meters for g in grid):.1f}m")
    print(f"Average elevation: {sum(g.elevation_meters for g in grid) / len(grid):.1f}m")
    
    print("\nGrid details:")
    for i, point in enumerate(grid):
        print(f"  Point {i+1}: {point.elevation_meters:.1f}m at ({point.latitude:.4f}, {point.longitude:.4f})")
    
    assert len(grid) == 9