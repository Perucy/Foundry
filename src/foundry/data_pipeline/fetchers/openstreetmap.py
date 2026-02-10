"""
OpenStreetMap Service - Get existing infrastructure data

Uses Overpass API to fetch buildings, roads, and infrastructure.
Free, no authentication required.
"""

from typing import NamedTuple, List
import requests
import time


class Building(NamedTuple):
    """Individual building from OSM"""
    osm_id: str
    building_type: str  # "residential", "commercial", "industrial", etc.
    name: str | None
    levels: int | None  # number of floors
    lat: float
    lon: float
    area_sqm: float | None


class Road(NamedTuple):
    """Road/street from OSM"""
    osm_id: str
    road_type: str  # "primary", "secondary", "residential", etc.
    name: str | None
    surface: str | None  # "paved", "unpaved", etc.
    lanes: int | None
    coordinates: List[tuple[float, float]]  # list of (lat, lon) points


class Infrastructure(NamedTuple):
    """Other infrastructure (schools, hospitals, etc.)"""
    osm_id: str
    amenity_type: str  # "school", "hospital", "market", etc.
    name: str | None
    lat: float
    lon: float


class OSMData(NamedTuple):
    """Complete OpenStreetMap data for an area"""
    buildings: List[Building]
    roads: List[Road]
    infrastructure: List[Infrastructure]
    total_buildings: int
    total_roads: int
    total_infrastructure: int
    area_bounds: dict  # {"min_lat", "max_lat", "min_lon", "max_lon"}


class OpenStreetMapService:
    """
    Fetch existing infrastructure from OpenStreetMap
    
    Uses Overpass API - free, no authentication needed
    """
    
    def __init__(self):
        self.api_url = "https://overpass-api.de/api/interpreter"
        self.timeout = 60  # seconds
    
    def get_area_data(
        self,
        center_lat: float,
        center_lon: float,
        radius_km: float = 2.0
    ) -> OSMData:
        """
        Get all infrastructure data for an area
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Radius in kilometers (default 2km)
        
        Returns:
            OSMData with buildings, roads, and infrastructure
        """
        # Calculate bounding box (approximate)
        lat_delta = radius_km / 111.0  # 1 degree lat ≈ 111km
        lon_delta = radius_km / (111.0 * abs(float(center_lat)))
        
        bounds = {
            "min_lat": center_lat - lat_delta,
            "max_lat": center_lat + lat_delta,
            "min_lon": center_lon - lon_delta,
            "max_lon": center_lon + lon_delta
        }
        
        bbox_str = f"{bounds['min_lat']},{bounds['min_lon']},{bounds['max_lat']},{bounds['max_lon']}"
        
        # Fetch all data types
        buildings = self._get_buildings(bbox_str)
        roads = self._get_roads(bbox_str)
        infrastructure = self._get_infrastructure(bbox_str)
        
        return OSMData(
            buildings=buildings,
            roads=roads,
            infrastructure=infrastructure,
            total_buildings=len(buildings),
            total_roads=len(roads),
            total_infrastructure=len(infrastructure),
            area_bounds=bounds
        )
    
    def _get_buildings(self, bbox: str) -> List[Building]:
        """Fetch buildings in bounding box"""
        query = f"""
        [out:json][timeout:60];
        (
          way["building"]({bbox});
          relation["building"]({bbox});
        );
        out center;
        """
        
        try:
            response = requests.post(
                self.api_url,
                data={"data": query},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            buildings = []
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                
                # Get center point
                if "center" in element:
                    lat = element["center"]["lat"]
                    lon = element["center"]["lon"]
                elif "lat" in element:
                    lat = element["lat"]
                    lon = element["lon"]
                else:
                    continue
                
                building = Building(
                    osm_id=str(element.get("id", "")),
                    building_type=tags.get("building", "yes"),
                    name=tags.get("name"),
                    levels=int(tags["building:levels"]) if "building:levels" in tags else None,
                    lat=lat,
                    lon=lon,
                    area_sqm=None  # Could calculate from geometry
                )
                buildings.append(building)
            
            return buildings
            
        except Exception as e:
            print(f"⚠️ Error fetching buildings: {e}")
            return []
    
    def _get_roads(self, bbox: str) -> List[Road]:
        """Fetch roads in bounding box"""
        query = f"""
        [out:json][timeout:60];
        (
          way["highway"]({bbox});
        );
        out geom;
        """
        
        try:
            response = requests.post(
                self.api_url,
                data={"data": query},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            roads = []
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                
                # Get coordinates from geometry
                coords = []
                if "geometry" in element:
                    coords = [(node["lat"], node["lon"]) for node in element["geometry"]]
                
                road = Road(
                    osm_id=str(element.get("id", "")),
                    road_type=tags.get("highway", "unknown"),
                    name=tags.get("name"),
                    surface=tags.get("surface"),
                    lanes=int(tags["lanes"]) if "lanes" in tags else None,
                    coordinates=coords
                )
                roads.append(road)
            
            return roads
            
        except Exception as e:
            print(f"⚠️ Error fetching roads: {e}")
            return []
    
    def _get_infrastructure(self, bbox: str) -> List[Infrastructure]:
        """Fetch infrastructure (schools, hospitals, etc.) in bounding box"""
        query = f"""
        [out:json][timeout:60];
        (
          node["amenity"]({bbox});
          way["amenity"]({bbox});
        );
        out center;
        """
        
        try:
            response = requests.post(
                self.api_url,
                data={"data": query},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            infrastructure = []
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                
                # Get coordinates
                if "center" in element:
                    lat = element["center"]["lat"]
                    lon = element["center"]["lon"]
                elif "lat" in element:
                    lat = element["lat"]
                    lon = element["lon"]
                else:
                    continue
                
                infra = Infrastructure(
                    osm_id=str(element.get("id", "")),
                    amenity_type=tags.get("amenity", "unknown"),
                    name=tags.get("name"),
                    lat=lat,
                    lon=lon
                )
                infrastructure.append(infra)
            
            return infrastructure
            
        except Exception as e:
            print(f"⚠️ Error fetching infrastructure: {e}")
            return []
    
    def get_summary(self, osm_data: OSMData) -> dict:
        """Generate summary statistics"""
        # Count building types
        building_types = {}
        for b in osm_data.buildings:
            building_types[b.building_type] = building_types.get(b.building_type, 0) + 1
        
        # Count road types
        road_types = {}
        for r in osm_data.roads:
            road_types[r.road_type] = road_types.get(r.road_type, 0) + 1
        
        # Count infrastructure types
        infra_types = {}
        for i in osm_data.infrastructure:
            infra_types[i.amenity_type] = infra_types.get(i.amenity_type, 0) + 1
        
        return {
            "total_buildings": osm_data.total_buildings,
            "building_types": building_types,
            "total_roads": osm_data.total_roads,
            "road_types": road_types,
            "total_infrastructure": osm_data.total_infrastructure,
            "infrastructure_types": infra_types,
            "area_bounds": osm_data.area_bounds
        }