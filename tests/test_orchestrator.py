from foundry.data_pipeline.orchestrator import DataOrchestrator
import json

def test_orchestrator_dar():
    """Test complete data pipeline for Dar es Salaam"""
    orchestrator = DataOrchestrator()
    
    profile = orchestrator.get_city_profile(
        "Dar es Salaam, Tanzania",
        climate_years=10,
        elevation_grid_size=3,  # Smaller grid for faster testing
        osm_radius_km=2.0  # NEW!
    )
    
    print("\n" + "="*70)
    print("COMPLETE CITY PROFILE")
    print("="*70)
    print(f"City: {profile.formatted_address}")
    print(f"Coordinates: {profile.coordinates['latitude']}, {profile.coordinates['longitude']}")
    print(f"Generated: {profile.generated_at}")
    
    print(f"\nTERRAIN:")
    print(f"  Classification: {profile.terrain['terrain_classification']}")
    print(f"  Elevation range: {profile.terrain['elevation_stats']['min_meters']}-{profile.terrain['elevation_stats']['max_meters']}m")
    print(f"  Average: {profile.terrain['elevation_stats']['avg_meters']}m")
    
    print(f"\nCLIMATE:")
    print(f"  Temperature: {profile.climate['temperature']['annual_avg_c']}°C")
    print(f"  Rainfall: {profile.climate['precipitation']['annual_mm']}mm/yr")
    print(f"  Wind: {profile.climate['wind']['avg_speed_kmh']} km/h ({profile.climate['wind']['dominant_direction_cardinal']})")
    print(f"  Water deficit: {profile.climate['water_balance']['water_deficit_mm']:.0f}mm")
    
    print(f"\nSOIL:")  # NEW!
    print(f"  Type: {profile.soil['texture']['usda_class']}")
    print(f"  Foundation: {profile.soil['foundation_assessment']['recommended_foundation']}")
    print(f"  Data source: {profile.soil['data_source']}")
    
    print(f"\nDISASTERS:")
    print(f"  Overall risk: {profile.disasters['overall_risk_score']}/10 ({profile.disasters['risk_summary']})")
    print(f"  Earthquake: {profile.disasters['earthquake']['risk_level']}")
    print(f"  Tsunami: {profile.disasters['tsunami']['risk_level']}")
    print(f"  Flood: {profile.disasters['flood']['risk_level']}")
    print(f"  Drought: {profile.disasters['drought']['risk_level']}")
    
    print(f"\nINFRASTRUCTURE:")  # NEW!
    print(f"  Buildings: {profile.infrastructure['summary']['total_buildings']}")
    print(f"  Roads: {profile.infrastructure['summary']['total_roads']}")
    print(f"  Amenities: {profile.infrastructure['summary']['total_amenities']}")
    
    print("="*70)
    
    # Assertions
    assert profile.city_name == "Dar es Salaam, Tanzania"
    assert profile.coordinates['latitude'] < 0  # Southern hemisphere
    assert profile.disasters['overall_risk_score'] > 0
    assert "infrastructure" in profile._asdict()  # NEW!


def test_orchestrator_json_output():
    """Test JSON export functionality"""
    orchestrator = DataOrchestrator()
    
    json_output = orchestrator.get_city_profile_json(
        "Dar es Salaam, Tanzania",
        climate_years=10,
        elevation_grid_size=3,
        osm_radius_km=2.0  # NEW!
    )
    
    # Parse JSON to verify it's valid
    data = json.loads(json_output)
    
    print("\n" + "="*70)
    print("JSON OUTPUT SAMPLE")
    print("="*70)
    print(json_output[:1000] + "...")  # Print first 1000 chars
    print("="*70)
    
    assert "city_name" in data
    assert "terrain" in data
    assert "climate" in data
    assert "soil" in data  # NEW!
    assert "disasters" in data
    assert "infrastructure" in data  # NEW!


def test_orchestrator_kathmandu():
    """Test orchestrator with Kathmandu (contrasting profile)"""
    orchestrator = DataOrchestrator()
    
    profile = orchestrator.get_city_profile(
        "Kathmandu, Nepal",
        climate_years=10,
        elevation_grid_size=3,
        osm_radius_km=1.5  # NEW!
    )
    
    print("\n" + "="*70)
    print(f"CITY: {profile.formatted_address}")
    print("="*70)
    print(f"Terrain: {profile.terrain['terrain_classification']}")
    print(f"Earthquake risk: {profile.disasters['earthquake']['risk_level']}")
    print(f"  Events (100yr): {profile.disasters['earthquake']['total_events_100yr']}")
    print(f"Overall risk: {profile.disasters['overall_risk_score']}/10")
    print(f"Infrastructure: {profile.infrastructure['summary']['total_buildings']} buildings")  # NEW!
    print("="*70)
    
    # Kathmandu should be mountainous/hilly
    assert profile.terrain['terrain_classification'] in ['hilly', 'mountainous']


def test_orchestrator_complete_with_soil():
    """Test complete orchestrator with all data including soil"""
    orchestrator = DataOrchestrator()
    
    profile = orchestrator.get_city_profile(
        "Dar es Salaam, Tanzania",
        climate_years=10,
        elevation_grid_size=3,
        osm_radius_km=2.0  # NEW!
    )
    
    print("\n" + "="*70)
    print("COMPLETE CITY PROFILE (ALL 6 DATA SOURCES)")  # UPDATED!
    print("="*70)
    print(f"City: {profile.formatted_address}\n")
    
    print("SOIL COMPOSITION:")
    print(f"  Texture: {profile.soil['texture']['usda_class']}")
    print(f"  Clay: {profile.soil['texture']['clay_percent']}%")
    print(f"  Sand: {profile.soil['texture']['sand_percent']}%")
    print(f"  Silt: {profile.soil['texture']['silt_percent']}%")
    print(f"  pH: {profile.soil['physical_properties']['ph']}")
    print(f"  Bearing capacity: {profile.soil['foundation_assessment']['bearing_capacity']}")
    print(f"  Foundation: {profile.soil['foundation_assessment']['recommended_foundation']}")
    print(f"  Data source: {profile.soil['data_source']}")  # NEW!
    
    print("\n" + "="*70)
    
    # Assertions
    assert "soil" in profile._asdict()
    assert "texture" in profile.soil
    assert "foundation_assessment" in profile.soil
    assert "infrastructure" in profile._asdict()  # NEW!


def test_infrastructure_details():  # NEW TEST!
    """Test detailed infrastructure data from OpenStreetMap"""
    orchestrator = DataOrchestrator()
    
    profile = orchestrator.get_city_profile(
        "Dar es Salaam, Tanzania",
        climate_years=10,
        elevation_grid_size=3,
        osm_radius_km=2.0
    )
    
    print("\n" + "="*70)
    print("INFRASTRUCTURE DETAILS (OpenStreetMap)")
    print("="*70)
    
    infra = profile.infrastructure
    
    print(f"\nSUMMARY:")
    print(f"  Total buildings: {infra['summary']['total_buildings']}")
    print(f"  Total roads: {infra['summary']['total_roads']}")
    print(f"  Total amenities: {infra['summary']['total_amenities']}")
    
    if infra['building_types']:
        print(f"\nTOP BUILDING TYPES:")
        for btype, count in list(infra['building_types'].items())[:5]:
            print(f"  {btype}: {count}")
    
    if infra['amenity_types']:
        print(f"\nTOP AMENITIES:")
        for atype, count in list(infra['amenity_types'].items())[:5]:
            print(f"  {atype}: {count}")
    
    if infra['sample_buildings']:
        print(f"\nSAMPLE BUILDINGS:")
        for building in infra['sample_buildings'][:3]:
            print(f"  - {building['name']} ({building['type']})")
    
    print("\n" + "="*70)
    
    # Assertions
    assert 'summary' in infra
    assert 'building_types' in infra
    assert 'road_types' in infra
    assert 'amenity_types' in infra
    assert 'sample_buildings' in infra
    assert 'sample_amenities' in infra