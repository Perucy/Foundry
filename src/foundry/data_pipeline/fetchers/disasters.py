from typing import NamedTuple
import requests
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

class EarthquakeRisk(NamedTuple):
    """Earthquake risk assessment"""
    total_events: int
    events_last_100yr: int
    max_magnitude: float
    avg_magnitude: float
    nearest_event_km: float
    risk_level: str  # "very_low", "low", "moderate", "high", "very_high"

class TsunamiRisk(NamedTuple):
    """Tsunami risk assessment"""
    coastal_city: bool
    nearest_event_km: float
    events_within_500km: int
    risk_level: str

class CycloneRisk(NamedTuple):
    """Tropical cyclone risk assessment"""
    events_50yr: int
    frequency_per_decade: float
    max_category: int  # Saffir-Simpson scale
    avg_wind_speed_kmh: float
    risk_level: str

class FloodRisk(NamedTuple):
    """Flood risk assessment (derived from climate + elevation)"""
    low_elevation_percent: float  # % of city below 10m
    annual_rainfall_mm: float
    wet_season_intensity: float  # Wettest month / annual average
    drainage_capacity: str  # "poor", "moderate", "good"
    risk_level: str

class DroughtRisk(NamedTuple):
    """Drought risk assessment (derived from climate)"""
    water_deficit_mm: float  # Rainfall - ET0
    dry_season_months: int
    risk_level: str

class LandslideRisk(NamedTuple):
    """Landslide risk assessment (derived from terrain + rainfall)"""
    steep_terrain_percent: float  # % of city with slope >15°
    high_rainfall: bool  # Annual rainfall >1500mm
    risk_level: str

class ComprehensiveDisasterProfile(NamedTuple):
    """Complete disaster risk profile"""
    earthquake: EarthquakeRisk
    tsunami: TsunamiRisk
    cyclone: CycloneRisk
    flood: FloodRisk
    drought: DroughtRisk
    landslide: LandslideRisk
    overall_risk_score: float  # 0-10 composite risk score


class DisasterService:
    """Comprehensive disaster history and risk assessment"""
    
    def __init__(self):
        self.usgs_base = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    def get_disaster_profile(
        self,
        lat: float,
        lon: float,
        elevation_grid: list,  # From ElevationService
        climate_profile,  # From ClimateService
        city_bounds: dict
    ) -> ComprehensiveDisasterProfile:
        """
        Comprehensive disaster risk assessment
        
        Args:
            lat, lon: City center coordinates
            elevation_grid: Elevation data across city
            climate_profile: Climate data from ClimateService
            city_bounds: City boundaries
        
        Returns:
            Complete disaster profile
        """
        # Assess each disaster type
        earthquake = self._assess_earthquake_risk(lat, lon)
        tsunami = self._assess_tsunami_risk(lat, lon, elevation_grid)
        cyclone = self._assess_cyclone_risk(lat, lon)
        flood = self._assess_flood_risk(elevation_grid, climate_profile)
        drought = self._assess_drought_risk(climate_profile)
        landslide = self._assess_landslide_risk(elevation_grid, climate_profile)
        
        # Calculate overall risk score (0-10)
        risk_scores = {
            'earthquake': self._risk_to_score(earthquake.risk_level),
            'tsunami': self._risk_to_score(tsunami.risk_level),
            'cyclone': self._risk_to_score(cyclone.risk_level),
            'flood': self._risk_to_score(flood.risk_level),
            'drought': self._risk_to_score(drought.risk_level),
            'landslide': self._risk_to_score(landslide.risk_level)
        }
        
        # Weighted average (some disasters more critical for urban planning)
        weights = {
            'earthquake': 2.0,  # High impact on building codes
            'tsunami': 1.5,     # Coastal cities only
            'cyclone': 1.5,     # Wind-resistant design
            'flood': 2.0,       # Drainage systems
            'drought': 1.0,     # Water management
            'landslide': 1.0    # Site selection
        }
        
        total_score = sum(risk_scores[k] * weights[k] for k in risk_scores)
        total_weight = sum(weights.values())
        overall_risk = round(total_score / total_weight, 1)
        
        return ComprehensiveDisasterProfile(
            earthquake=earthquake,
            tsunami=tsunami,
            cyclone=cyclone,
            flood=flood,
            drought=drought,
            landslide=landslide,
            overall_risk_score=overall_risk
        )
    
    def _assess_earthquake_risk(self, lat: float, lon: float) -> EarthquakeRisk:
        """Query USGS for historical earthquakes within 500km radius"""
        # Get earthquakes from last 100 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=36500)  # ~100 years
        
        params = {
            "format": "geojson",
            "starttime": start_date.strftime("%Y-%m-%d"),
            "endtime": end_date.strftime("%Y-%m-%d"),
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": 500,
            "minmagnitude": 4.0,  # Only significant earthquakes
            "orderby": "magnitude"
        }
        
        response = requests.get(self.usgs_base, params=params)
        response.raise_for_status()
        
        data = response.json()
        events = data["features"]
        
        if not events:
            return EarthquakeRisk(
                total_events=0,
                events_last_100yr=0,
                max_magnitude=0.0,
                avg_magnitude=0.0,
                nearest_event_km=999.0,
                risk_level="very_low"
            )
        
        magnitudes = [e["properties"]["mag"] for e in events if e["properties"]["mag"]]
        max_mag = max(magnitudes)
        avg_mag = sum(magnitudes) / len(magnitudes)
        
        # Find nearest event
        nearest_dist = min(
            self._haversine_distance(
                lat, lon,
                e["geometry"]["coordinates"][1],
                e["geometry"]["coordinates"][0]
            )
            for e in events
        )
        
        # Determine risk level
        if max_mag >= 7.0 or len(events) > 50:
            risk = "very_high"
        elif max_mag >= 6.0 or len(events) > 20:
            risk = "high"
        elif max_mag >= 5.0 or len(events) > 10:
            risk = "moderate"
        elif len(events) > 5:
            risk = "low"
        else:
            risk = "very_low"
        
        return EarthquakeRisk(
            total_events=len(events),
            events_last_100yr=len(events),
            max_magnitude=round(max_mag, 1),
            avg_magnitude=round(avg_mag, 1),
            nearest_event_km=round(nearest_dist, 1),
            risk_level=risk
        )
    
    def _assess_tsunami_risk(self, lat: float, lon: float, elevation_grid: list) -> TsunamiRisk:
        """
        Assess tsunami risk based on coastal proximity and elevation
        Note: Full tsunami database requires CSV download, using simplified assessment
        """
        # Check if coastal (any elevation point below 10m)
        coastal = any(e.elevation_meters < 10 for e in elevation_grid)
        
        # Simplified: coastal cities within tsunami-prone regions
        # Pacific Ring of Fire, Indian Ocean, Caribbean
        tsunami_zones = [
            (-60, 60, 90, 180),    # Pacific (lat_min, lat_max, lon_min, lon_max)
            (-40, 30, 40, 120),    # Indian Ocean
            (10, 30, -90, -60),    # Caribbean
        ]
        
        in_tsunami_zone = any(
            lat_min <= lat <= lat_max and lon_min <= lon <= lon_max
            for lat_min, lat_max, lon_min, lon_max in tsunami_zones
        )
        
        if coastal and in_tsunami_zone:
            risk = "high"
            events = 3  # Simplified estimate
        elif coastal:
            risk = "moderate"
            events = 1
        else:
            risk = "very_low"
            events = 0
        
        return TsunamiRisk(
            coastal_city=coastal,
            nearest_event_km=100.0 if coastal else 999.0,  # Simplified
            events_within_500km=events,
            risk_level=risk
        )
    
    def _assess_cyclone_risk(self, lat: float, lon: float) -> CycloneRisk:
        """
        Assess tropical cyclone risk based on location
        Note: Full IBTrACS data requires CSV download, using simplified assessment
        """
        # Cyclone-prone latitudes: 5-30° N/S
        in_cyclone_belt = (5 <= abs(lat) <= 30)
        
        # Cyclone basins
        cyclone_regions = {
            "atlantic": (10, 30, -100, -20),
            "pacific": (5, 30, 100, -80),
            "indian": (-30, 30, 40, 120),
        }
        
        in_basin = any(
            lat_min <= lat <= lat_max and lon_min <= lon <= lon_max
            for lat_min, lat_max, lon_min, lon_max in cyclone_regions.values()
        )
        
        if in_cyclone_belt and in_basin:
            risk = "high"
            events = 15  # Estimated over 50 years
            frequency = 3.0
            max_cat = 4
            avg_wind = 150
        elif in_basin:
            risk = "moderate"
            events = 5
            frequency = 1.0
            max_cat = 2
            avg_wind = 100
        else:
            risk = "very_low"
            events = 0
            frequency = 0.0
            max_cat = 0
            avg_wind = 0
        
        return CycloneRisk(
            events_50yr=events,
            frequency_per_decade=frequency,
            max_category=max_cat,
            avg_wind_speed_kmh=avg_wind,
            risk_level=risk
        )
    
    def _assess_flood_risk(self, elevation_grid: list, climate_profile) -> FloodRisk:
        """Assess flood risk from elevation and rainfall data"""
        # Calculate % of city below 10m elevation
        low_areas = sum(1 for e in elevation_grid if e.elevation_meters < 10)
        low_percent = (low_areas / len(elevation_grid)) * 100
        
        # Wet season intensity
        max_monthly = max(climate_profile.rainfall_by_month.values())
        avg_monthly = climate_profile.annual_rainfall_mm / 12
        wet_intensity = max_monthly / avg_monthly if avg_monthly > 0 else 1.0
        
        # Assess drainage capacity based on rainfall and terrain
        if climate_profile.annual_rainfall_mm > 1500 and low_percent > 50:
            drainage = "poor"
            risk = "very_high"
        elif climate_profile.annual_rainfall_mm > 1000 or low_percent > 30:
            drainage = "moderate"
            risk = "high"
        elif climate_profile.annual_rainfall_mm > 500:
            drainage = "good"
            risk = "moderate"
        else:
            drainage = "good"
            risk = "low"
        
        return FloodRisk(
            low_elevation_percent=round(low_percent, 1),
            annual_rainfall_mm=climate_profile.annual_rainfall_mm,
            wet_season_intensity=round(wet_intensity, 1),
            drainage_capacity=drainage,
            risk_level=risk
        )
    
    def _assess_drought_risk(self, climate_profile) -> DroughtRisk:
        """Assess drought risk from climate data"""
        # Water balance: rainfall - evapotranspiration
        water_deficit = climate_profile.annual_rainfall_mm - climate_profile.annual_et0_mm
        
        # Count dry season months (< 50mm rainfall)
        dry_months = sum(
            1 for rainfall in climate_profile.rainfall_by_month.values()
            if rainfall < 50
        )
        
        # Determine risk
        if water_deficit < -1000 or dry_months >= 6:
            risk = "very_high"
        elif water_deficit < -500 or dry_months >= 4:
            risk = "high"
        elif water_deficit < 0 or dry_months >= 2:
            risk = "moderate"
        else:
            risk = "low"
        
        return DroughtRisk(
            water_deficit_mm=round(water_deficit, 1),
            dry_season_months=dry_months,
            risk_level=risk
        )
    
    def _assess_landslide_risk(self, elevation_grid: list, climate_profile) -> LandslideRisk:
        """Assess landslide risk from terrain and rainfall"""
        # Calculate terrain variance (proxy for steepness)
        elevations = [e.elevation_meters for e in elevation_grid]
        elev_range = max(elevations) - min(elevations)
        
        # Steep terrain if elevation range > 100m across city
        steep_percent = min(100.0, (elev_range / 100) * 50)  # Simplified
        
        high_rainfall = climate_profile.annual_rainfall_mm > 1500
        
        # Determine risk
        if steep_percent > 30 and high_rainfall:
            risk = "high"
        elif steep_percent > 20 or high_rainfall:
            risk = "moderate"
        else:
            risk = "low"
        
        return LandslideRisk(
            steep_terrain_percent=round(steep_percent, 1),
            high_rainfall=high_rainfall,
            risk_level=risk
        )
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    def _risk_to_score(self, risk_level: str) -> float:
        """Convert risk level to numeric score (0-10)"""
        scores = {
            "very_low": 1.0,
            "low": 3.0,
            "moderate": 5.0,
            "high": 7.5,
            "very_high": 10.0
        }
        return scores.get(risk_level, 5.0)