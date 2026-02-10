"""
Test OpenStreetMap service
"""

from foundry.data_pipeline.fetchers.openstreetmap import OpenStreetMapService


def test_dar_es_salaam_infrastructure():
    """Test getting existing infrastructure for Dar es Salaam"""
    
    osm_svc = OpenStreetMapService()
    
    # Dar es Salaam city center coordinates
    lat, lon = -6.8165054, 39.2894367
    
    print("\n" + "="*70)
    print("OPENSTREETMAP DATA - Dar es Salaam")
    print("="*70)
    print(f"Center: {lat}, {lon}")
    print("\nFetching existing infrastructure (2km radius)...")
    print("This may take 30-60 seconds...")
    
    # Get OSM data (2km radius)
    osm_data = osm_svc.get_area_data(lat, lon, radius_km=2.0)
    
    print("\n✅ EXISTING INFRASTRUCTURE:")
    print(f"   Total buildings: {osm_data.total_buildings}")
    print(f"   Total roads: {osm_data.total_roads}")
    print(f"   Total amenities: {osm_data.total_infrastructure}")
    
    # Get summary
    summary = osm_svc.get_summary(osm_data)
    
    if summary["building_types"]:
        print("\n📊 BUILDING BREAKDOWN:")
        for btype, count in sorted(summary["building_types"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {btype}: {count}")
    
    if summary["road_types"]:
        print("\n🛣️  ROAD BREAKDOWN:")
        for rtype, count in sorted(summary["road_types"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {rtype}: {count}")
    
    if summary["infrastructure_types"]:
        print("\n🏥 INFRASTRUCTURE BREAKDOWN:")
        for itype, count in sorted(summary["infrastructure_types"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {itype}: {count}")
    
    # Show some examples
    if osm_data.buildings:
        print("\n📍 SAMPLE BUILDINGS:")
        for building in osm_data.buildings[:3]:
            name = building.name or "Unnamed"
            print(f"   - {name} ({building.building_type})")
    
    if osm_data.infrastructure:
        print("\n📍 SAMPLE AMENITIES:")
        for infra in osm_data.infrastructure[:3]:
            name = infra.name or "Unnamed"
            print(f"   - {name} ({infra.amenity_type})")
    
    print("\n" + "="*70)
    
    # Verify we got some data
    assert osm_data.total_buildings > 0 or osm_data.total_roads > 0, "Should find some infrastructure"


def test_kathmandu_infrastructure():
    """Test getting existing infrastructure for Kathmandu"""
    
    osm_svc = OpenStreetMapService()
    
    # Kathmandu coordinates
    lat, lon = 27.7172, 85.3240
    
    print("\n" + "="*70)
    print("OPENSTREETMAP DATA - Kathmandu")
    print("="*70)
    print(f"Center: {lat}, {lon}")
    print("Fetching data (1.5km radius)...")
    
    osm_data = osm_svc.get_area_data(lat, lon, radius_km=1.5)
    summary = osm_svc.get_summary(osm_data)
    
    print(f"\n✅ Buildings: {osm_data.total_buildings}")
    print(f"✅ Roads: {osm_data.total_roads}")
    print(f"✅ Amenities: {osm_data.total_infrastructure}")
    
    print("\n" + "="*70)


# if __name__ == "__main__":
#     test_dar_es_salaam_infrastructure()
#     test_kathmandu_infrastructure()