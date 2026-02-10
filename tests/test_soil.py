"""
Test regional soil service - WORKS OFFLINE
"""

from foundry.data_pipeline.fetchers.soil import SoilService


def test_dar_es_salaam():
    """Test Dar es Salaam typical soil"""
    soil_svc = SoilService()
    
    # Dar es Salaam coordinates
    soil = soil_svc.get_soil_composition(-6.8165054, 39.2894367)
    
    print("\n" + "="*70)
    print("DAR ES SALAAM - Regional Typical Soil Profile")
    print("="*70)
    
    print(f"\n✅ SOIL TEXTURE:")
    print(f"   Clay: {soil.clay_percent}%")
    print(f"   Sand: {soil.sand_percent}%")
    print(f"   Silt: {soil.silt_percent}%")
    print(f"   Total: {soil.clay_percent + soil.sand_percent + soil.silt_percent}%")
    print(f"   Classification: {soil.usda_classification}")
    
    print(f"\n✅ PHYSICAL PROPERTIES:")
    print(f"   Bulk density: {soil.bulk_density_kg_dm3} kg/dm³")
    print(f"   pH: {soil.ph_h2o}")
    print(f"   Organic carbon: {soil.organic_carbon_g_kg} g/kg")
    
    print(f"\n✅ FOUNDATION ASSESSMENT:")
    print(f"   Bearing capacity: {soil.bearing_capacity_category.upper()}")
    print(f"   Recommended foundation: {soil.foundation_recommendation}")
    print(f"   Drainage rating: {soil.drainage_rating}")
    
    print(f"\n📊 Data source: {soil.data_source}")
    print("="*70)
    
    # Verify valid data
    assert soil.clay_percent > 0
    assert soil.sand_percent > 0
    assert soil.silt_percent > 0
    assert abs((soil.clay_percent + soil.sand_percent + soil.silt_percent) - 100) < 1


def test_kathmandu():
    """Test Kathmandu typical soil"""
    soil_svc = SoilService()
    
    # Kathmandu coordinates
    soil = soil_svc.get_soil_composition(27.7172, 85.3240)
    
    print("\n" + "="*70)
    print("KATHMANDU - Regional Typical Soil Profile")
    print("="*70)
    
    print(f"\n✅ SOIL TEXTURE:")
    print(f"   Clay: {soil.clay_percent}%")
    print(f"   Sand: {soil.sand_percent}%")
    print(f"   Silt: {soil.silt_percent}%")
    print(f"   Classification: {soil.usda_classification}")
    
    print(f"\n✅ FOUNDATION:")
    print(f"   {soil.foundation_recommendation}")
    
    print(f"\n📊 Data source: {soil.data_source}")
    print("="*70)
    
    assert soil.clay_percent > 0


# if __name__ == "__main__":
#     test_dar_es_salaam()
#     test_kathmandu()