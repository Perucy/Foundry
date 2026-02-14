"""
Tests for the IFC Building Generator

Run with: uv run pytest tests/test_ifc_generator.py -v -s

Generates IFC files from building specs and validates the output.
"""

import json
from pathlib import Path

import pytest

from foundry.ifc.building_generator import BuildingGenerator


# Same sample spec as in test_spec_generator.py
# (In production, the AI engine generates this)
SAMPLE_SPEC = {
    "metadata": {
        "city": "Dar es Salaam, Tanzania",
        "generated_at": "2025-02-12T10:30:00Z",
        "spec_version": "1.0",
        "data_sources_used": ["geocoding", "elevation", "climate", "soil", "disasters", "osm"],
        "design_rationale_summary": "Climate-responsive coastal development",
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
            "rationale": "Clay loam + earthquake",
        },
        "columns": {
            "grid_spacing_x_m": 6.0,
            "grid_spacing_y_m": 7.0,
            "width_mm": 400,
            "depth_mm": 400,
        },
        "slabs": {"thickness_mm": 200},
        "walls": {
            "exterior": {"total_thickness_mm": 280},
            "interior_load_bearing": {"thickness_mm": 200},
        },
        "roof": {
            "type": "flat_with_parapet",
            "thickness_mm": 200,
            "parapet_height_mm": 900,
        },
    },
    "envelope": {"windows": {}, "doors": {}},
    "circulation": {
        "stairs": {
            "width_mm": 1200,
            "landing_depth_mm": 1200,
        },
        "corridors": {},
        "elevator": {"provided": True},
    },
    "floor_plans": {
        "ground_floor": {
            "floor_to_floor_height_mm": 4000,
            "elevation_above_grade_mm": 2000,
            "spaces": [{"name": "lobby"}],
        },
        "typical_floor": {
            "floor_to_floor_height_mm": 3200,
        },
    },
    "finishes": {},
    "mep": {},
    "fixtures": {},
    "climate_adaptations": [],
    "design_rationale": {"narrative": "Test", "key_tradeoffs": []},
}


class TestBuildingGenerator:
    """Test IFC generation from specs."""

    def test_generate_basic_building(self, tmp_path):
        """Generate a complete building and verify IFC contents."""
        generator = BuildingGenerator(SAMPLE_SPEC)
        generator.generate(verbose=True)
        
        output = tmp_path / "test_building.ifc"
        generator.save(output)

        assert output.exists()
        assert output.stat().st_size > 10000  # Should be substantial

        # Verify IFC contents
        import ifcopenshell
        ifc = ifcopenshell.open(str(output))

        assert len(ifc.by_type("IfcBuildingStorey")) == 5
        assert len(ifc.by_type("IfcWall")) > 20  # Exterior + stair core
        assert len(ifc.by_type("IfcSlab")) >= 6   # 5 floors + foundation + roof
        assert len(ifc.by_type("IfcColumn")) > 50  # Grid of columns
        assert ifc.schema == "IFC4"

        print(f"\n📁 IFC saved: {output}")
        print(f"   Size: {output.stat().st_size:,} bytes")

    def test_storeys_have_correct_elevation(self, tmp_path):
        """Verify storey elevations match the spec."""
        generator = BuildingGenerator(SAMPLE_SPEC)
        generator.generate(verbose=False)
        
        output = tmp_path / "elevation_test.ifc"
        generator.save(output)

        import ifcopenshell
        ifc = ifcopenshell.open(str(output))
        
        storeys = sorted(ifc.by_type("IfcBuildingStorey"), key=lambda s: s.Elevation)
        
        print("\nStorey Elevations:")
        for s in storeys:
            print(f"  {s.Name}: {s.Elevation}m")

        # Ground floor should be elevated (flood protection)
        assert storeys[0].Elevation == 2.0  # 2000mm elevation offset
        # Second floor
        assert storeys[1].Elevation == 6.0  # 2.0 + 4.0 ground floor height

    def test_column_count_matches_grid(self, tmp_path):
        """Verify column count matches the grid specification."""
        generator = BuildingGenerator(SAMPLE_SPEC)
        generator.generate(verbose=False)
        
        output = tmp_path / "column_test.ifc"
        generator.save(output)

        import ifcopenshell
        ifc = ifcopenshell.open(str(output))
        
        total_columns = len(ifc.by_type("IfcColumn"))
        # 5x3 grid × 5 storeys = 75
        cols_per_floor = total_columns // 5
        
        print(f"\nColumns: {total_columns} total ({cols_per_floor} per floor)")
        assert total_columns == 75  # 15 per floor × 5 floors

    def test_different_building_size(self, tmp_path):
        """Test with a different building spec."""
        spec = SAMPLE_SPEC.copy()
        spec["structure"] = {
            **SAMPLE_SPEC["structure"],
            "stories": 3,
            "footprint": {"length_m": 18.0, "width_m": 10.0, "gross_area_m2": 180.0},
        }
        
        generator = BuildingGenerator(spec)
        generator.generate(verbose=True)
        
        output = tmp_path / "small_building.ifc"
        generator.save(output)

        import ifcopenshell
        ifc = ifcopenshell.open(str(output))
        
        assert len(ifc.by_type("IfcBuildingStorey")) == 3
        print(f"\n✅ 3-storey building: {output.stat().st_size:,} bytes")