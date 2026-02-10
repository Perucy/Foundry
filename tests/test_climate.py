from foundry.data_pipeline.fetchers.climate import ClimateService
from foundry.data_pipeline.fetchers.geocoding import GeocodingService
from pprint import pprint

def test_comprehensive_climate_dar():
    """Test comprehensive climate profile for Dar es Salaam"""
    geocoder = GeocodingService()
    climate = ClimateService()
    
    geo = geocoder.geocode("Dar es Salaam, Tanzania")
    profile = climate.get_climate_profile(geo.lat, geo.lon, years=10)
    
    print("\n" + "="*60)
    print("COMPREHENSIVE CLIMATE PROFILE")
    print("="*60)
    print(f"City: {geo.formatted_address}\n")
    
    print("TEMPERATURE:")
    print(f"  Average: {profile.annual_temp_avg_c}°C")
    print(f"  Range: {profile.annual_temp_min_c}°C to {profile.annual_temp_max_c}°C")
    print(f"  Hottest: {profile.hottest_month}, Coldest: {profile.coldest_month}")
    
    print(f"\nRAINFALL:")
    print(f"  Annual: {profile.annual_rainfall_mm}mm")
    print(f"  Wettest: {profile.wettest_month} ({profile.rainfall_by_month[profile.wettest_month]}mm)")
    print(f"  Driest: {profile.driest_month} ({profile.rainfall_by_month[profile.driest_month]}mm)")
    
    print(f"\nWIND:")
    print(f"  Average speed: {profile.wind.avg_speed_kmh} km/h")
    print(f"  Max gust: {profile.wind.max_gust_kmh} km/h")
    print(f"  Dominant direction: {profile.wind.dominant_direction_degrees}° (0°=N, 90°=E, 180°=S, 270°=W)")
    
    print(f"\nSOLAR RADIATION:")
    print(f"  Annual total: {profile.solar.annual_radiation_sum_mj_m2} MJ/m²")
    print(f"  Daily average: {profile.solar.avg_daily_radiation_wm2} W/m²")
    
    print(f"\nHUMIDITY:")
    print(f"  Average: {profile.humidity.avg_relative_humidity_percent}%")
    print(f"  Range: {profile.humidity.min_relative_humidity_percent}% - {profile.humidity.max_relative_humidity_percent}%")
    
    print(f"\nSOIL:")
    print(f"  Surface moisture (0-7cm): {profile.soil.avg_moisture_0_7cm} m³/m³")
    print(f"  Deep moisture (7-100cm): {profile.soil.avg_moisture_7_100cm} m³/m³")
    print(f"  Surface temperature: {profile.soil.avg_temp_0_7cm_c}°C")
    
    print(f"\nWATER MANAGEMENT:")
    print(f"  Annual evapotranspiration: {profile.annual_et0_mm}mm")
    print(f"  Water balance: {profile.annual_rainfall_mm - profile.annual_et0_mm:+.1f}mm")
    print("="*60)
    
    # Assertions
    assert 20 <= profile.annual_temp_avg_c <= 30
    assert profile.annual_rainfall_mm > 500
    assert profile.humidity.avg_relative_humidity_percent > 60  # Coastal