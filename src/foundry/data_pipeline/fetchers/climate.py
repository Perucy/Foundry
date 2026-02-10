from typing import NamedTuple
import requests
import time
from statistics import mean, stdev
from datetime import datetime, timedelta
from collections import defaultdict

class WindProfile(NamedTuple):
    """Wind characteristics"""
    avg_speed_kmh: float
    max_gust_kmh: float
    dominant_direction_degrees: float  # 0° = North, 90° = East, 180° = South, 270° = West
    
class SolarProfile(NamedTuple):
    """Solar radiation data"""
    annual_radiation_sum_mj_m2: float  # Total solar energy per year
    avg_daily_radiation_wm2: float
    
class HumidityProfile(NamedTuple):
    """Humidity characteristics"""
    avg_relative_humidity_percent: float
    max_relative_humidity_percent: float
    min_relative_humidity_percent: float

class SoilProfile(NamedTuple):
    """Soil conditions"""
    avg_moisture_0_7cm: float  # m³/m³
    avg_moisture_7_100cm: float  # m³/m³
    avg_temp_0_7cm_c: float

class ClimateProfile(NamedTuple):
    """Complete climate profile for urban planning"""
    # Temperature
    annual_temp_avg_c: float
    annual_temp_max_c: float
    annual_temp_min_c: float
    hottest_month: str
    coldest_month: str
    
    # Rainfall
    annual_rainfall_mm: float
    wettest_month: str
    driest_month: str
    rainfall_by_month: dict[str, float]
    
    # Wind
    wind: WindProfile
    
    # Solar
    solar: SolarProfile
    
    # Humidity
    humidity: HumidityProfile
    
    # Soil
    soil: SoilProfile
    
    # Evapotranspiration (water management)
    annual_et0_mm: float  # Reference evapotranspiration

class ClimateService:
    """Open-Meteo Historical Weather API for comprehensive climate analysis"""
    
    def __init__(self):
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"
        self.months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        self.last_request_time = 0
        self.min_request_interval = 1.0  
    
    def get_climate_profile(self, lat: float, lon: float, years: int = 10) -> ClimateProfile:
        """
        Get comprehensive climate profile for urban planning
        
        Args:
            lat: Latitude
            lon: Longitude
            years: Number of years to analyze (default 10, can go back to 1940)
        
        Returns:
            ClimateProfile with all climate factors
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)
        
        # Request ALL relevant variables
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": [
                # Temperature
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                # Precipitation
                "precipitation_sum",
                "rain_sum",
                # Wind
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "wind_direction_10m_dominant",
                # Solar
                "shortwave_radiation_sum",
                # Humidity
                "relative_humidity_2m_mean",
                "relative_humidity_2m_max",
                "relative_humidity_2m_min",
                # Soil
                "soil_moisture_0_to_7cm_mean",
                "soil_moisture_7_to_28cm_mean",
                "soil_moisture_28_to_100cm_mean",
                "soil_temperature_0_to_7cm_mean",
                # Evapotranspiration
                "et0_fao_evapotranspiration",
            ],
            "timezone": "auto"
        }
        
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)

        response = requests.get(self.base_url, params=params)
        self.last_request_time = time.time()
        response.raise_for_status()
        
        data = response.json()["daily"]
        
        # Calculate temperature stats
        temps_max = [t for t in data["temperature_2m_max"] if t is not None]
        temps_min = [t for t in data["temperature_2m_min"] if t is not None]
        annual_temp_max = mean(temps_max)
        annual_temp_min = mean(temps_min)
        annual_temp_avg = (annual_temp_max + annual_temp_min) / 2
        
        # Calculate rainfall
        yearly_rainfall = self._calculate_yearly_rainfall(
            data["time"],
            data["precipitation_sum"]
        )
        annual_rainfall = mean(yearly_rainfall) if yearly_rainfall else 0.0
        
        monthly_rainfall = self._calculate_monthly_rainfall(
            data["time"], 
            data["precipitation_sum"]
        )
        
        # Calculate temperature patterns
        monthly_temps_max = self._calculate_monthly_temp_averages(
            data["time"],
            data["temperature_2m_max"]
        )
        
        # Find extreme months
        wettest = max(monthly_rainfall, key=monthly_rainfall.get)
        driest = min(monthly_rainfall, key=monthly_rainfall.get)
        hottest = max(monthly_temps_max, key=monthly_temps_max.get)
        coldest = min(monthly_temps_max, key=monthly_temps_max.get)
        
        # Wind profile
        wind_speeds = [w for w in data["wind_speed_10m_max"] if w is not None]
        wind_gusts = [w for w in data["wind_gusts_10m_max"] if w is not None]
        wind_dirs = [w for w in data["wind_direction_10m_dominant"] if w is not None]
        
        wind = WindProfile(
            avg_speed_kmh=round(mean(wind_speeds), 1),
            max_gust_kmh=round(max(wind_gusts), 1),
            dominant_direction_degrees=round(mean(wind_dirs), 0)
        )
        
        # Solar profile
        solar_radiation = [s for s in data["shortwave_radiation_sum"] if s is not None]
        annual_solar = sum(solar_radiation)
        avg_daily_solar = mean(solar_radiation) * 1000000 / 3600  # Convert MJ/m² to W/m²
        
        solar = SolarProfile(
            annual_radiation_sum_mj_m2=round(annual_solar, 1),
            avg_daily_radiation_wm2=round(avg_daily_solar, 1)
        )
        
        # Humidity profile
        humidity_mean = [h for h in data["relative_humidity_2m_mean"] if h is not None]
        humidity_max = [h for h in data["relative_humidity_2m_max"] if h is not None]
        humidity_min = [h for h in data["relative_humidity_2m_min"] if h is not None]
        
        humidity = HumidityProfile(
            avg_relative_humidity_percent=round(mean(humidity_mean), 1),
            max_relative_humidity_percent=round(mean(humidity_max), 1),
            min_relative_humidity_percent=round(mean(humidity_min), 1)
        )
        
        # Soil profile
        soil_0_7 = [s for s in data["soil_moisture_0_to_7cm_mean"] if s is not None]
        soil_7_28 = [s for s in data["soil_moisture_7_to_28cm_mean"] if s is not None]
        soil_28_100 = [s for s in data["soil_moisture_28_to_100cm_mean"] if s is not None]
        soil_temp = [s for s in data["soil_temperature_0_to_7cm_mean"] if s is not None]
        
        soil_7_100_combined = soil_7_28 + soil_28_100
        
        soil = SoilProfile(
            avg_moisture_0_7cm=round(mean(soil_0_7), 3),
            avg_moisture_7_100cm=round(mean(soil_7_100_combined), 3),
            avg_temp_0_7cm_c=round(mean(soil_temp), 1)
        )
        
        # Evapotranspiration
        et0_values = [e for e in data["et0_fao_evapotranspiration"] if e is not None]
        annual_et0 = sum(et0_values)
        
        return ClimateProfile(
            annual_temp_avg_c=round(annual_temp_avg, 1),
            annual_temp_max_c=round(annual_temp_max, 1),
            annual_temp_min_c=round(annual_temp_min, 1),
            hottest_month=hottest,
            coldest_month=coldest,
            annual_rainfall_mm=round(annual_rainfall, 1),
            wettest_month=wettest,
            driest_month=driest,
            rainfall_by_month=monthly_rainfall,
            wind=wind,
            solar=solar,
            humidity=humidity,
            soil=soil,
            annual_et0_mm=round(annual_et0, 1)
        )
    
    def _calculate_yearly_rainfall(self, dates: list[str], values: list[float]) -> list[float]:
        """Calculate total rainfall for each year"""
        yearly_totals = defaultdict(float)
        
        for date_str, value in zip(dates, values):
            if value is None:
                continue
            year = int(date_str.split("-")[0])
            yearly_totals[year] += value
        
        return list(yearly_totals.values())
    
    def _calculate_monthly_rainfall(self, dates: list[str], values: list[float]) -> dict[str, float]:
        """Calculate average monthly rainfall totals"""
        monthly_data = defaultdict(lambda: defaultdict(float))
        
        for date_str, value in zip(dates, values):
            if value is None:
                continue
            year, month_num, _ = date_str.split("-")
            month_name = self.months[int(month_num) - 1]
            monthly_data[month_name][year] += value
        
        result = {}
        for month in self.months:
            if month in monthly_data and monthly_data[month]:
                yearly_totals = list(monthly_data[month].values())
                result[month] = round(mean(yearly_totals), 1)
            else:
                result[month] = 0.0
        
        return result
    
    def _calculate_monthly_temp_averages(self, dates: list[str], values: list[float]) -> dict[str, float]:
        """Calculate average temperature by month"""
        monthly_data = {month: [] for month in self.months}
        
        for date_str, value in zip(dates, values):
            if value is None:
                continue
            month_num = int(date_str.split("-")[1])
            month_name = self.months[month_num - 1]
            monthly_data[month_name].append(value)
        
        return {
            month: round(mean(values), 1) if values else 0.0
            for month, values in monthly_data.items()
        }