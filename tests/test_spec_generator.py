"""
Tests for the AI Engine Spec Generator

Run with: uv run pytest tests/test_spec_generator.py -v -s

Uses sample city profile data so you don't need to hit all 6 APIs.
For integration testing with real data, see test_full_pipeline.py
"""

import json
import os

import pytest

from foundry.ai_engine.spec_generator import SpecGenerator, SpecGeneratorError
from foundry.ai_engine.schemas.building_spec_schema import validate_building_spec
from foundry.config.settings import settings


# ============================================================
# SAMPLE DATA - Dar es Salaam city profile (from real pipeline)
# ============================================================
DAR_ES_SALAAM_PROFILE = {
    "city_name": "Dar es Salaam, Tanzania",
    "formatted_address": "Dar es Salaam, Tanzania",
    "coordinates": {
        "latitude": -6.8165054,
        "longitude": 39.2894367,
    },
    "bounds": {
        "northeast": {"lat": -6.5767, "lng": 39.5486},
        "southwest": {"lat": -7.0388, "lng": 39.0931},
    },
    "place_id": "ChIJqU3Re8hcXBgRljBftYBVoqc",
    "generated_at": "2025-02-09T15:30:00",
    "terrain": {
        "elevation_stats": {
            "min_meters": 0.0,
            "max_meters": 263.0,
            "avg_meters": 48.2,
            "range_meters": 263.0,
        },
        "grid_points": 25,
        "terrain_classification": "hilly",
    },
    "climate": {
        "temperature": {
            "annual_avg_c": 26.7,
            "annual_max_c": 31.2,
            "annual_min_c": 22.1,
            "hottest_month": "February",
            "coldest_month": "July",
        },
        "precipitation": {
            "annual_mm": 1073,
            "wettest_month": "April",
            "driest_month": "August",
            "monthly_averages_mm": {
                "January": 75, "February": 60, "March": 130,
                "April": 250, "May": 180, "June": 40,
                "July": 25, "August": 20, "September": 25,
                "October": 55, "November": 100, "December": 113,
            },
        },
        "wind": {
            "avg_speed_kmh": 12.5,
            "dominant_direction": "ESE",
            "max_gust_kmh": 65.0,
        },
        "humidity": {
            "annual_avg_percent": 77,
        },
        "solar_radiation": {
            "annual_avg_kwh_m2_day": 5.2,
        },
    },
    "soil": {
        "texture": "clay_loam",
        "composition": {
            "clay_percent": 45,
            "sand_percent": 25,
            "silt_percent": 30,
        },
        "ph": 6.5,
        "foundation_assessment": {
            "recommended_type": "reinforced_slab_on_grade",
            "min_depth_m": 1.5,
            "bearing_capacity_kpa": 120,
            "notes": "High clay content requires reinforced foundation. Expansive soil potential.",
        },
        "data_source": "regional_profile",
    },
    "disasters": {
        "overall_risk_score": 6.6,
        "risk_summary": "high",
        "earthquake": {
            "risk_level": "very_high",
            "total_events_100yr": 47,
            "max_magnitude": 7.4,
            "avg_magnitude": 5.2,
            "nearest_event_km": 85,
        },
        "tsunami": {
            "risk_level": "moderate",
            "coastal_city": True,
            "events_within_500km": 3,
        },
        "tropical_cyclone": {
            "risk_level": "low",
            "events_50yr": 2,
            "frequency_per_decade": 0.4,
            "max_category": 1,
            "avg_wind_speed_kmh": 95,
        },
        "flood": {
            "risk_level": "high",
            "low_elevation_percent": 35,
            "annual_rainfall_mm": 1073,
        },
        "drought": {
            "risk_level": "moderate",
        },
        "landslide": {
            "risk_level": "low",
        },
    },
    "infrastructure": {
        "summary": {
            "total_buildings": 969,
            "total_roads": 244,
            "total_amenities": 165,
        },
        "building_types": {
            "yes": 522,
            "commercial": 164,
            "public": 72,
            "residential": 66,
            "commercial;residential": 64,
        },
        "road_types": {
            "service": 155,
            "tertiary": 28,
            "unclassified": 13,
            "footway": 11,
            "secondary": 10,
        },
        "amenity_types": {
            "bank": 21,
            "restaurant": 19,
            "parking": 13,
            "bureau_de_change": 10,
            "fast_food": 9,
        },
        "sample_buildings": [
            {"name": "Unnamed", "type": "commercial", "levels": None, "coordinates": {"lat": -6.816, "lon": 39.289}},
            {"name": "Life House", "type": "commercial", "levels": 3, "coordinates": {"lat": -6.817, "lon": 39.290}},
            {"name": "Bank of Africa", "type": "commercial", "levels": 5, "coordinates": {"lat": -6.815, "lon": 39.291}},
        ],
        "sample_amenities": [
            {"name": "Kinondoni Police Station", "type": "police", "coordinates": {"lat": -6.814, "lon": 39.288}},
            {"name": "General Post Office", "type": "post_box", "coordinates": {"lat": -6.818, "lon": 39.292}},
        ],
    },
}


# ============================================================
# TESTS
# ============================================================

class TestSpecGenerator:
    """Test the spec generator with real Claude API calls."""

    @pytest.fixture
    def generator(self):
        """Create a SpecGenerator instance."""
        api_key = settings.claude_api_key
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set — skipping API tests")
        return SpecGenerator(api_key=api_key)

    def test_generate_dar_es_salaam(self, generator):
        """Generate a full building spec for Dar es Salaam."""
        spec = generator.generate_building_spec(
            DAR_ES_SALAAM_PROFILE,
            validate=True,
            verbose=True,
        )

        # Should have all required sections
        assert "metadata" in spec
        assert "structure" in spec
        assert "envelope" in spec
        assert "mep" in spec
        assert "climate_adaptations" in spec

        # Metadata should reference our city
        assert "Dar" in spec["metadata"]["city"]

        # Structure should be earthquake-appropriate
        structure = spec["structure"]
        assert structure["structural_system"] in [
            "reinforced_concrete_frame",
            "steel_frame",
        ], "Earthquake zone requires RC or steel frame"

        # Foundation should be reinforced (clay + earthquake)
        foundation = structure.get("foundation", {})
        assert "reinforced" in foundation.get("type", "").lower() or \
               "pile" in foundation.get("type", "").lower(), \
            "Clay loam + very_high earthquake requires reinforced/pile foundation"

        # Should have climate adaptations
        adaptations = spec.get("climate_adaptations", {})
        if isinstance(adaptations, list):
            features = adaptations
        else:
            features = adaptations.get("features", [])
        assert len(features) >= 3, "Should have at least 3 climate adaptations"

        # Print the full spec for review
        print("\n" + "=" * 70)
        print("GENERATED BUILDING SPEC")
        print("=" * 70)
        print(json.dumps(spec, indent=2))
        print("=" * 70)

    def test_spec_output_as_json_file(self, generator, tmp_path):
        """Generate spec and save to JSON file."""
        spec_json = generator.generate_building_spec_json(
            DAR_ES_SALAAM_PROFILE,
            validate=True,
            verbose=True,
        )

        # Save to file
        output_path = tmp_path / "dar_building_spec.json"
        output_path.write_text(spec_json)

        print(f"\n📁 Spec saved to: {output_path}")
        print(f"   Size: {len(spec_json)} chars")

        # Verify it's valid JSON
        loaded = json.loads(output_path.read_text())
        assert "structure" in loaded


class TestSchemaValidator:
    """Test the schema validator independently (no API needed)."""

    def test_valid_spec(self):
        """Test validation of a complete, valid spec."""
        # Load the example spec we designed
        spec = _make_valid_spec()
        result = validate_building_spec(spec)
        print(f"\n{result}")
        assert result.valid, f"Expected valid but got errors: {result.errors}"

    def test_missing_sections(self):
        """Test that missing sections are caught."""
        spec = {"metadata": {"city": "Test"}}
        result = validate_building_spec(spec)
        assert not result.valid
        assert any("Missing required section" in e for e in result.errors)

    def test_insane_values(self):
        """Test that crazy values are caught."""
        spec = _make_valid_spec()
        spec["structure"]["stories"] = 500  # 500-story building? 🤔
        result = validate_building_spec(spec)
        assert not result.valid
        assert any("stories" in e for e in result.errors)

    def test_masonry_too_tall(self):
        """Load-bearing masonry shouldn't be used for tall buildings."""
        spec = _make_valid_spec()
        spec["structure"]["structural_system"] = "load_bearing_masonry"
        spec["structure"]["stories"] = 5
        result = validate_building_spec(spec)
        assert not result.valid
        assert any("masonry" in e.lower() for e in result.errors)

    def test_no_elevator_warning(self):
        """5+ stories without elevator should warn."""
        spec = _make_valid_spec()
        spec["structure"]["stories"] = 6
        spec["circulation"]["elevator"] = {"provided": False}
        result = validate_building_spec(spec)
        assert any("elevator" in w.lower() for w in result.warnings)

    def test_missing_rationale_warning(self):
        """Missing rationale fields should warn."""
        spec = _make_valid_spec()
        spec["structure"]["foundation"]["rationale"] = ""
        result = validate_building_spec(spec)
        assert any("rationale" in w.lower() for w in result.warnings)


def _make_valid_spec() -> dict:
    """Create a minimal but valid building spec for testing."""
    return {
        "metadata": {
            "city": "Test City",
            "generated_at": "2025-01-01T00:00:00Z",
            "spec_version": "1.0",
            "data_sources_used": ["geocoding", "elevation", "climate", "soil", "disasters", "osm"],
            "design_rationale_summary": "Test building for validation",
        },
        "site": {
            "coordinates": {"lat": -6.8165, "lon": 39.2894},
            "elevation_m": 15.0,
            "orientation_deg": 112,
        },
        "structure": {
            "building_type": "mixed_use_residential",
            "stories": 5,
            "total_height_m": 18.4,
            "footprint": {
                "shape": "rectangular",
                "length_m": 24.0,
                "width_m": 14.0,
                "gross_area_m2": 336.0,
            },
            "structural_system": "reinforced_concrete_frame",
            "foundation": {
                "type": "reinforced_slab_on_grade",
                "depth_m": 1.8,
                "thickness_m": 0.4,
                "rationale": "Clay loam + earthquake risk",
            },
            "columns": {"width_mm": 400, "depth_mm": 400},
            "slabs": {"thickness_mm": 200},
            "walls": {},
            "roof": {},
        },
        "envelope": {
            "windows": {"window_wall_ratio": 0.25},
            "doors": {},
        },
        "circulation": {
            "stairs": {},
            "corridors": {},
            "elevator": {"provided": True},
        },
        "floor_plans": {
            "ground_floor": {
                "floor_to_floor_height_mm": 4000,
                "spaces": [{"name": "lobby", "area_m2": 50}],
            },
            "typical_floor": {},
        },
        "finishes": {
            "by_space_type": {},
        },
        "mep": {
            "mechanical": {"ventilation_strategy": "natural_cross_ventilation"},
            "electrical": {"supply": "three_phase_415v"},
            "plumbing": {"water_supply": {"source": "municipal"}},
            "fire_protection": {"type": "hose_reel_system"},
        },
        "fixtures": {
            "bathroom": {},
            "kitchen": {},
        },
        "climate_adaptations": {
            "features": [
                {"feature": "elevated_ground", "specification": "2m", "addresses": "flood", "data_source": "disasters.flood"},
                {"feature": "cross_ventilation", "specification": "opposite windows", "addresses": "heat", "data_source": "climate.wind"},
                {"feature": "reinforced_structure", "specification": "RC frame", "addresses": "earthquake", "data_source": "disasters.earthquake"},
            ],
        },
        "design_rationale": {
            "narrative": "Test building designed for validation purposes.",
            "key_tradeoffs": ["Test tradeoff 1"],
        },
    }