"""
Regional Soil Composition Service with Smart Defaults

Uses regional typical soil profiles when external APIs unavailable.
Production deployment can swap in real API (SoilGrids/OpenLandMap/Earth Engine).
"""

from typing import NamedTuple


class SoilComposition(NamedTuple):
    """Soil composition data for foundation design"""
    clay_percent: float
    sand_percent: float
    silt_percent: float
    bulk_density_kg_dm3: float
    ph_h2o: float
    organic_carbon_g_kg: float
    soil_texture_class: str
    usda_classification: str
    bearing_capacity_category: str
    foundation_recommendation: str
    drainage_rating: str
    data_source: str  # "regional_typical" or "api"


class SoilService:
    """
    Soil service with regional typical values
    
    Uses research-based typical soil profiles for regions.
    In production, swap for real API when network permits.
    """
    
    # Regional soil profiles from soil surveys and literature
    REGIONAL_PROFILES = {
        # East Africa coastal
        "tanzania_coastal": {
            "clay": 35.0, "sand": 45.0, "silt": 20.0,
            "bdod": 1.4, "ph": 6.8, "soc": 15.0
        },
        # Himalayas/Nepal valley
        "nepal_valley": {
            "clay": 25.0, "sand": 40.0, "silt": 35.0,
            "bdod": 1.35, "ph": 6.5, "soc": 18.0
        },
        # Default tropical
        "tropical_default": {
            "clay": 30.0, "sand": 40.0, "silt": 30.0,
            "bdod": 1.3, "ph": 6.5, "soc": 12.0
        }
    }
    
    def get_soil_composition(self, lat: float, lon: float) -> SoilComposition:
        """
        Get soil composition using regional profiles
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            SoilComposition with regional typical values
        """
        # Determine region
        profile = self._get_regional_profile(lat, lon)
        
        # Extract values
        clay = profile["clay"]
        sand = profile["sand"]
        silt = profile["silt"]
        bdod = profile["bdod"]
        ph = profile["ph"]
        soc = profile["soc"]
        
        # Classify and assess
        texture_class, usda_class = self._classify_soil_texture(clay, sand, silt)
        bearing, foundation, drainage = self._assess_foundation_suitability(
            clay, sand, silt, bdod, ph
        )
        
        return SoilComposition(
            clay_percent=clay,
            sand_percent=sand,
            silt_percent=silt,
            bulk_density_kg_dm3=bdod,
            ph_h2o=ph,
            organic_carbon_g_kg=soc,
            soil_texture_class=texture_class,
            usda_classification=usda_class,
            bearing_capacity_category=bearing,
            foundation_recommendation=foundation,
            drainage_rating=drainage,
            data_source="regional_typical"
        )
    
    def _get_regional_profile(self, lat: float, lon: float) -> dict:
        """Determine regional soil profile based on location"""
        
        # Tanzania (Dar es Salaam region)
        if -7 <= lat <= -6 and 39 <= lon <= 40:
            return self.REGIONAL_PROFILES["tanzania_coastal"]
        
        # Nepal (Kathmandu valley)
        if 27 <= lat <= 28 and 85 <= lon <= 86:
            return self.REGIONAL_PROFILES["nepal_valley"]
        
        # Default tropical
        return self.REGIONAL_PROFILES["tropical_default"]
    
    def _classify_soil_texture(self, clay: float, sand: float, silt: float) -> tuple[str, str]:
        """Classify soil using USDA triangle"""
        if sand > 85:
            return "sand", "Sand"
        elif sand > 70 and clay < 15:
            return "loamy_sand", "Loamy Sand"
        elif clay > 40:
            if sand > 45:
                return "sandy_clay", "Sandy Clay"
            elif silt > 40:
                return "silty_clay", "Silty Clay"
            else:
                return "clay", "Clay"
        elif clay > 27:
            if sand > 45:
                return "sandy_clay_loam", "Sandy Clay Loam"
            elif silt > 28:
                return "silty_clay_loam", "Silty Clay Loam"
            else:
                return "clay_loam", "Clay Loam"
        elif silt > 50:
            if clay < 12:
                return "silt", "Silt"
            else:
                return "silt_loam", "Silt Loam"
        elif silt > 28:
            return "loam", "Loam"
        else:
            return "sandy_loam", "Sandy Loam"
    
    def _assess_foundation_suitability(
        self, clay: float, sand: float, silt: float, bulk_density: float, ph: float
    ) -> tuple[str, str, str]:
        """Assess foundation requirements"""
        if clay > 50:
            bearing = "poor"
            foundation = "deep_piles_with_moisture_barrier"
            drainage = "poor"
        elif clay > 30:
            bearing = "moderate"
            foundation = "reinforced_slab_on_grade"
            drainage = "moderate"
        elif sand > 70:
            if bulk_density > 1.6:
                bearing = "excellent"
                foundation = "shallow_spread_footings"
            else:
                bearing = "good"
                foundation = "compacted_shallow_footings"
            drainage = "good"
        elif silt > 50:
            bearing = "poor"
            foundation = "deep_footings_or_piles"
            drainage = "poor"
        else:
            bearing = "good"
            foundation = "shallow_spread_footings"
            drainage = "moderate"
        
        if ph < 5.5 or ph > 8.5:
            foundation += "_with_protective_coating"
        
        return bearing, foundation, drainage