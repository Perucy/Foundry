from typing import NamedTuple
import json
from datetime import datetime

from foundry.data_pipeline.fetchers.geocoding import GeocodingService, GeocodeResult
from foundry.data_pipeline.fetchers.elevation import ElevationService, ElevationResult
from foundry.data_pipeline.fetchers.climate import ClimateService, ClimateProfile
from foundry.data_pipeline.fetchers.disasters import DisasterService, ComprehensiveDisasterProfile
from foundry.data_pipeline.fetchers.soil import SoilService, SoilComposition  # UPDATED!
from foundry.data_pipeline.fetchers.openstreetmap import OpenStreetMapService, OSMData  # NEW!


class CityProfile(NamedTuple):
    """Complete city profile for urban planning"""
    # Metadata
    city_name: str
    formatted_address: str
    coordinates: dict[str, float]
    bounds: dict
    place_id: str
    generated_at: str
    
    # Terrain
    terrain: dict
    
    # Climate
    climate: dict
    
    # Soil
    soil: dict
    
    # Disasters
    disasters: dict
    
    # Existing Infrastructure  # NEW!
    infrastructure: dict


class DataOrchestrator:
    """
    Orchestrates all data fetching services to create comprehensive city profiles
    """
    
    def __init__(self):
        self.geocoder = GeocodingService()
        self.elevation = ElevationService()
        self.climate = ClimateService()
        self.soil = SoilService()  # UPDATED to use regional!
        self.disasters = DisasterService()
        self.osm = OpenStreetMapService()  # NEW!
    
    def get_city_profile(
        self, 
        city_name: str,
        climate_years: int = 10,
        elevation_grid_size: int = 5,
        osm_radius_km: float = 2.0  # NEW!
    ) -> CityProfile:
        """
        Get complete city profile for urban planning
        """
        print(f"🌍 Gathering data for: {city_name}")
        
        # Step 1: Geocoding
        print("  📍 Geocoding...")
        geo = self.geocoder.geocode(city_name)
        
        # Step 2: Elevation
        print(f"  ⛰️  Analyzing terrain ({elevation_grid_size}x{elevation_grid_size} grid)...")
        elevation_grid = self.elevation.get_elevation_grid(
            geo.bounds, 
            grid_size=elevation_grid_size
        )
        
        # Step 3: Climate
        print(f"  🌤️  Analyzing climate ({climate_years}-year history)...")
        climate_profile = self.climate.get_climate_profile(
            geo.lat, 
            geo.lon, 
            years=climate_years
        )
        
        # Step 4: Soil Composition
        print("  🏗️  Analyzing soil composition...")
        soil_composition = self.soil.get_soil_composition(geo.lat, geo.lon)
        
        # Step 5: Disasters
        print("  🌋 Assessing disaster risks...")
        disaster_profile = self.disasters.get_disaster_profile(
            lat=geo.lat,
            lon=geo.lon,
            elevation_grid=elevation_grid,
            climate_profile=climate_profile,
            city_bounds=geo.bounds
        )
        
        # Step 6: Existing Infrastructure (OpenStreetMap)  # NEW!
        print(f"  🏙️  Fetching existing infrastructure ({osm_radius_km}km radius)...")
        osm_data = self.osm.get_area_data(geo.lat, geo.lon, radius_km=osm_radius_km)
        
        print("  ✅ Data gathering complete!\n")
        
        # Compile everything
        return CityProfile(
            city_name=city_name,
            formatted_address=geo.formatted_address,
            coordinates={
                "latitude": geo.lat,
                "longitude": geo.lon
            },
            bounds=geo.bounds,
            place_id=geo.place_id,
            generated_at=datetime.now().isoformat(),
            terrain=self._format_terrain_data(elevation_grid),
            climate=self._format_climate_data(climate_profile),
            soil=self._format_soil_data(soil_composition),
            disasters=self._format_disaster_data(disaster_profile),
            infrastructure=self._format_infrastructure_data(osm_data)  # NEW!
        )
    
    def get_city_profile_json(
        self,
        city_name: str,
        climate_years: int = 10,
        elevation_grid_size: int = 5,
        osm_radius_km: float = 2.0,  # NEW!
        indent: int = 2
    ) -> str:
        """Get city profile as formatted JSON string"""
        profile = self.get_city_profile(
            city_name, 
            climate_years, 
            elevation_grid_size,
            osm_radius_km  # NEW!
        )
        return json.dumps(profile._asdict(), indent=indent, default=str)
    
    def _format_terrain_data(self, elevation_grid: list[ElevationResult]) -> dict:
        """Format elevation data for output"""
        elevations = [e.elevation_meters for e in elevation_grid]
        
        return {
            "elevation_stats": {
                "min_meters": round(min(elevations), 1),
                "max_meters": round(max(elevations), 1),
                "avg_meters": round(sum(elevations) / len(elevations), 1),
                "range_meters": round(max(elevations) - min(elevations), 1)
            },
            "grid_points": len(elevation_grid),
            "terrain_classification": self._classify_terrain(elevations),
            "elevation_grid": [
                {
                    "lat": e.latitude,
                    "lon": e.longitude,
                    "elevation_m": e.elevation_meters
                }
                for e in elevation_grid
            ]
        }
    
    def _classify_terrain(self, elevations: list[float]) -> str:
        """Classify terrain based on elevation range"""
        elev_range = max(elevations) - min(elevations)
        
        if elev_range < 50:
            return "flat"
        elif elev_range < 150:
            return "gently_rolling"
        elif elev_range < 300:
            return "hilly"
        else:
            return "mountainous"
    
    def _format_climate_data(self, climate: ClimateProfile) -> dict:
        """Format climate data for output"""
        return {
            "temperature": {
                "annual_avg_c": climate.annual_temp_avg_c,
                "annual_max_c": climate.annual_temp_max_c,
                "annual_min_c": climate.annual_temp_min_c,
                "hottest_month": climate.hottest_month,
                "coldest_month": climate.coldest_month
            },
            "precipitation": {
                "annual_mm": climate.annual_rainfall_mm,
                "wettest_month": climate.wettest_month,
                "driest_month": climate.driest_month,
                "monthly_averages_mm": climate.rainfall_by_month
            },
            "wind": {
                "avg_speed_kmh": climate.wind.avg_speed_kmh,
                "max_gust_kmh": climate.wind.max_gust_kmh,
                "dominant_direction_degrees": climate.wind.dominant_direction_degrees,
                "dominant_direction_cardinal": self._degrees_to_cardinal(
                    climate.wind.dominant_direction_degrees
                )
            },
            "solar": {
                "annual_radiation_mj_m2": climate.solar.annual_radiation_sum_mj_m2,
                "avg_daily_radiation_wm2": climate.solar.avg_daily_radiation_wm2
            },
            "humidity": {
                "avg_percent": climate.humidity.avg_relative_humidity_percent,
                "max_percent": climate.humidity.max_relative_humidity_percent,
                "min_percent": climate.humidity.min_relative_humidity_percent
            },
            "soil_moisture": {
                "surface_moisture_m3_m3": climate.soil.avg_moisture_0_7cm,
                "deep_moisture_m3_m3": climate.soil.avg_moisture_7_100cm,
                "surface_temp_c": climate.soil.avg_temp_0_7cm_c
            },
            "water_balance": {
                "annual_evapotranspiration_mm": climate.annual_et0_mm,
                "water_deficit_mm": climate.annual_rainfall_mm - climate.annual_et0_mm
            }
        }
    
    def _format_soil_data(self, soil: SoilComposition) -> dict:
        """Format soil composition data for output"""
        return {
            "texture": {
                "clay_percent": soil.clay_percent,
                "sand_percent": soil.sand_percent,
                "silt_percent": soil.silt_percent,
                "classification": soil.soil_texture_class,
                "usda_class": soil.usda_classification
            },
            "physical_properties": {
                "bulk_density_kg_dm3": soil.bulk_density_kg_dm3,
                "ph": soil.ph_h2o,
                "organic_carbon_g_kg": soil.organic_carbon_g_kg
            },
            "foundation_assessment": {
                "bearing_capacity": soil.bearing_capacity_category,
                "recommended_foundation": soil.foundation_recommendation,
                "drainage_rating": soil.drainage_rating
            },
            "data_source": soil.data_source  # NEW! Shows if regional or API
        }
    
    def _format_infrastructure_data(self, osm_data: OSMData) -> dict:  # NEW!
        """Format OpenStreetMap infrastructure data for output"""
        summary = self.osm.get_summary(osm_data)
        
        # Sample buildings for context
        sample_buildings = []
        for building in osm_data.buildings[:10]:
            sample_buildings.append({
                "name": building.name or "Unnamed",
                "type": building.building_type,
                "levels": building.levels,
                "coordinates": {"lat": building.lat, "lon": building.lon}
            })
        
        # Sample infrastructure for context
        sample_amenities = []
        for infra in osm_data.infrastructure[:10]:
            sample_amenities.append({
                "name": infra.name or "Unnamed",
                "type": infra.amenity_type,
                "coordinates": {"lat": infra.lat, "lon": infra.lon}
            })
        
        return {
            "summary": {
                "total_buildings": osm_data.total_buildings,
                "total_roads": osm_data.total_roads,
                "total_amenities": osm_data.total_infrastructure
            },
            "building_types": summary["building_types"],
            "road_types": summary["road_types"],
            "amenity_types": summary["infrastructure_types"],
            "sample_buildings": sample_buildings,
            "sample_amenities": sample_amenities,
            "area_bounds": summary["area_bounds"]
        }
    
    def _format_disaster_data(self, disasters: ComprehensiveDisasterProfile) -> dict:
        """Format disaster data for output"""
        return {
            "overall_risk_score": disasters.overall_risk_score,
            "risk_summary": self._get_risk_summary(disasters.overall_risk_score),
            "earthquake": {
                "risk_level": disasters.earthquake.risk_level,
                "total_events_100yr": disasters.earthquake.events_last_100yr,
                "max_magnitude": disasters.earthquake.max_magnitude,
                "avg_magnitude": disasters.earthquake.avg_magnitude,
                "nearest_event_km": disasters.earthquake.nearest_event_km
            },
            "tsunami": {
                "risk_level": disasters.tsunami.risk_level,
                "coastal_city": disasters.tsunami.coastal_city,
                "events_within_500km": disasters.tsunami.events_within_500km
            },
            "tropical_cyclone": {
                "risk_level": disasters.cyclone.risk_level,
                "events_50yr": disasters.cyclone.events_50yr,
                "frequency_per_decade": disasters.cyclone.frequency_per_decade,
                "max_category": disasters.cyclone.max_category,
                "avg_wind_speed_kmh": disasters.cyclone.avg_wind_speed_kmh
            },
            "flood": {
                "risk_level": disasters.flood.risk_level,
                "low_elevation_percent": disasters.flood.low_elevation_percent,
                "annual_rainfall_mm": disasters.flood.annual_rainfall_mm,
                "wet_season_intensity": disasters.flood.wet_season_intensity,
                "drainage_capacity": disasters.flood.drainage_capacity
            },
            "drought": {
                "risk_level": disasters.drought.risk_level,
                "water_deficit_mm": disasters.drought.water_deficit_mm,
                "dry_season_months": disasters.drought.dry_season_months
            },
            "landslide": {
                "risk_level": disasters.landslide.risk_level,
                "steep_terrain_percent": disasters.landslide.steep_terrain_percent,
                "high_rainfall": disasters.landslide.high_rainfall
            }
        }
    
    def _degrees_to_cardinal(self, degrees: float) -> str:
        """Convert degrees to cardinal direction"""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def _get_risk_summary(self, score: float) -> str:
        """Convert risk score to text summary"""
        if score < 2:
            return "very_low"
        elif score < 4:
            return "low"
        elif score < 6:
            return "moderate"
        elif score < 8:
            return "high"
        else:
            return "very_high"