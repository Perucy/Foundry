from foundry.data_pipeline.fetchers.disasters import DisasterService
from foundry.data_pipeline.fetchers.geocoding import GeocodingService
from foundry.data_pipeline.fetchers.elevation import ElevationService
from foundry.data_pipeline.fetchers.climate import ClimateService
from pprint import pprint

def test_comprehensive_disaster_profile_dar():
    """Test complete disaster profile for Dar es Salaam"""
    print("\n" + "="*70)
    print("COMPREHENSIVE DISASTER RISK ASSESSMENT")
    print("="*70)
    
    # Gather all required data
    geocoder = GeocodingService()
    elevation_svc = ElevationService()
    climate_svc = ClimateService()
    disaster_svc = DisasterService()
    
    # Get city data
    geo = geocoder.geocode("Dar es Salaam, Tanzania")
    print(f"City: {geo.formatted_address}")
    print(f"Coordinates: {geo.lat}, {geo.lon}\n")
    
    # Get elevation grid
    elevation_grid = elevation_svc.get_elevation_grid(geo.bounds, grid_size=3)
    
    # Get climate profile
    climate = climate_svc.get_climate_profile(geo.lat, geo.lon, years=10)
    
    # Get comprehensive disaster profile
    profile = disaster_svc.get_disaster_profile(
        lat=geo.lat,
        lon=geo.lon,
        elevation_grid=elevation_grid,
        climate_profile=climate,
        city_bounds=geo.bounds
    )
    
    # Display results
    print("EARTHQUAKE RISK:")
    print(f"  Risk level: {profile.earthquake.risk_level.upper()}")
    print(f"  Historical events (100yr): {profile.earthquake.events_last_100yr}")
    print(f"  Maximum magnitude: {profile.earthquake.max_magnitude}")
    print(f"  Average magnitude: {profile.earthquake.avg_magnitude}")
    print(f"  Nearest event: {profile.earthquake.nearest_event_km} km")
    
    print(f"\nTSUNAMI RISK:")
    print(f"  Risk level: {profile.tsunami.risk_level.upper()}")
    print(f"  Coastal city: {'Yes' if profile.tsunami.coastal_city else 'No'}")
    print(f"  Events within 500km: {profile.tsunami.events_within_500km}")
    
    print(f"\nTROPICAL CYCLONE RISK:")
    print(f"  Risk level: {profile.cyclone.risk_level.upper()}")
    print(f"  Events (50yr): {profile.cyclone.events_50yr}")
    print(f"  Frequency: {profile.cyclone.frequency_per_decade} per decade")
    print(f"  Max category: {profile.cyclone.max_category}")
    print(f"  Avg wind speed: {profile.cyclone.avg_wind_speed_kmh} km/h")
    
    print(f"\nFLOOD RISK:")
    print(f"  Risk level: {profile.flood.risk_level.upper()}")
    print(f"  Low elevation areas: {profile.flood.low_elevation_percent}%")
    print(f"  Annual rainfall: {profile.flood.annual_rainfall_mm}mm")
    print(f"  Wet season intensity: {profile.flood.wet_season_intensity}x")
    print(f"  Drainage capacity: {profile.flood.drainage_capacity}")
    
    print(f"\nDROUGHT RISK:")
    print(f"  Risk level: {profile.drought.risk_level.upper()}")
    print(f"  Water deficit: {profile.drought.water_deficit_mm:+.1f}mm")
    print(f"  Dry season: {profile.drought.dry_season_months} months")
    
    print(f"\nLANDSLIDE RISK:")
    print(f"  Risk level: {profile.landslide.risk_level.upper()}")
    print(f"  Steep terrain: {profile.landslide.steep_terrain_percent}%")
    print(f"  High rainfall: {'Yes' if profile.landslide.high_rainfall else 'No'}")
    
    print(f"\n{'='*70}")
    print(f"OVERALL DISASTER RISK SCORE: {profile.overall_risk_score}/10")
    print("="*70)
    
    # Assertions
    assert profile.overall_risk_score >= 0
    assert profile.overall_risk_score <= 10
    assert profile.tsunami.coastal_city  # Dar es Salaam is coastal


def test_disaster_profile_kathmandu():
    """Test disaster profile for Kathmandu (contrasting risk profile)"""
    print("\n" + "="*70)
    print("DISASTER RISK - KATHMANDU (High Earthquake Risk)")
    print("="*70)
    
    geocoder = GeocodingService()
    elevation_svc = ElevationService()
    climate_svc = ClimateService()
    disaster_svc = DisasterService()
    
    geo = geocoder.geocode("Kathmandu, Nepal")
    print(f"City: {geo.formatted_address}\n")
    
    elevation_grid = elevation_svc.get_elevation_grid(geo.bounds, grid_size=3)
    climate = climate_svc.get_climate_profile(geo.lat, geo.lon, years=10)
    
    profile = disaster_svc.get_disaster_profile(
        lat=geo.lat,
        lon=geo.lon,
        elevation_grid=elevation_grid,
        climate_profile=climate,
        city_bounds=geo.bounds
    )
    
    print(f"Earthquake risk: {profile.earthquake.risk_level.upper()}")
    print(f"  Events (100yr): {profile.earthquake.events_last_100yr}")
    print(f"  Max magnitude: {profile.earthquake.max_magnitude}")
    
    print(f"\nTsunami risk: {profile.tsunami.risk_level.upper()}")
    print(f"  Coastal: {'Yes' if profile.tsunami.coastal_city else 'No'}")
    
    print(f"\nFlood risk: {profile.flood.risk_level.upper()}")
    print(f"\nLandslide risk: {profile.landslide.risk_level.upper()}")
    print(f"  Steep terrain: {profile.landslide.steep_terrain_percent}%")
    
    print(f"\nOverall risk score: {profile.overall_risk_score}/10")
    print("="*70)
    
    # Kathmandu is NOT coastal, HIGH earthquake risk
    assert not profile.tsunami.coastal_city
    assert profile.earthquake.events_last_100yr > 0  # Nepal has earthquakes


def test_disaster_comparison():
    """Compare disaster profiles of different cities"""
    print("\n" + "="*70)
    print("DISASTER RISK COMPARISON")
    print("="*70)
    
    geocoder = GeocodingService()
    elevation_svc = ElevationService()
    climate_svc = ClimateService()
    disaster_svc = DisasterService()
    
    cities = [
        "Dar es Salaam, Tanzania",
        "Kathmandu, Nepal"
    ]
    
    results = []
    
    for city_name in cities:
        geo = geocoder.geocode(city_name)
        elevation_grid = elevation_svc.get_elevation_grid(geo.bounds, grid_size=3)
        climate = climate_svc.get_climate_profile(geo.lat, geo.lon, years=10)
        profile = disaster_svc.get_disaster_profile(
            geo.lat, geo.lon, elevation_grid, climate, geo.bounds
        )
        
        results.append({
            'city': city_name,
            'overall': profile.overall_risk_score,
            'earthquake': profile.earthquake.risk_level,
            'tsunami': profile.tsunami.risk_level,
            'flood': profile.flood.risk_level,
            'cyclone': profile.cyclone.risk_level,
        })
    
    print(f"\n{'City':<30} {'Overall':<10} {'Earthquake':<12} {'Tsunami':<12} {'Flood':<12} {'Cyclone':<12}")
    print("-" * 90)
    
    for r in results:
        print(f"{r['city']:<30} {r['overall']:<10.1f} {r['earthquake']:<12} {r['tsunami']:<12} {r['flood']:<12} {r['cyclone']:<12}")
    
    print("="*70)