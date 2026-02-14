"""
Foundry Demo: Full Pipeline
Data Pipeline → AI Engine → Building Specification

Run with: uv run python demo_ai_engine.py

Requires:
- ANTHROPIC_API_KEY environment variable
- GOOGLE_MAPS_API_KEY environment variable (for geocoding)
"""

import json
import sys

from foundry.ai_engine.spec_generator import SpecGenerator
from foundry.config.settings import settings


# ============================================================
# Option 1: Use real data from the pipeline
# ============================================================
def demo_with_live_data():
    """Full pipeline: gather data → generate spec."""
    from foundry.data_pipeline.orchestrator import DataOrchestrator

    print("=" * 70)
    print("🌍 FOUNDRY — Full Pipeline Demo")
    print("=" * 70)

    # Step 1: Gather city data
    print("\n📡 Step 1: Gathering city data...")
    orchestrator = DataOrchestrator()
    profile = orchestrator.get_city_profile(
        "Dar es Salaam, Tanzania",
        climate_years=10,
        elevation_grid_size=5,
        osm_radius_km=2.0,
    )
    profile_dict = profile._asdict()
    print("   ✅ City profile complete!")

    # Step 2: Generate building spec
    print("\n🧠 Step 2: Generating building specification...")
    generator = SpecGenerator()
    spec = generator.generate_building_spec(profile_dict, verbose=True)

    # Step 3: Save output
    output_path = "dar_es_salaam_building_spec.json"
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"\n📁 Spec saved to: {output_path}")

    _print_spec_summary(spec)


# ============================================================
# Option 2: Use sample data (no API keys needed except Anthropic)
# ============================================================
def demo_with_sample_data():
    """Use pre-collected sample data — only needs ANTHROPIC_API_KEY."""
    from tests.test_spec_generator import DAR_ES_SALAAM_PROFILE

    print("=" * 70)
    print("🌍 FOUNDRY — AI Engine Demo (Sample Data)")
    print("=" * 70)

    # Generate building spec
    print("\n🧠 Generating building specification...")
    generator = SpecGenerator(api_key=settings.claude_api_key)
    spec = generator.generate_building_spec(DAR_ES_SALAAM_PROFILE, verbose=True)

    # Save output
    output_path = "dar_es_salaam_building_spec.json"
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"\n📁 Spec saved to: {output_path}")

    _print_spec_summary(spec)


def _print_spec_summary(spec: dict):
    """Print a nice summary of the generated spec."""
    print("\n" + "=" * 70)
    print("📋 BUILDING SPEC SUMMARY")
    print("=" * 70)

    s = spec.get("structure", {})
    print(f"\n🏗️  Building: {s.get('building_type', '?')}")
    print(f"   Stories: {s.get('stories', '?')}")
    print(f"   Height: {s.get('total_height_m', '?')}m")
    print(f"   Structure: {s.get('structural_system', '?')}")

    fp = s.get("footprint", {})
    print(f"   Footprint: {fp.get('length_m', '?')}m × {fp.get('width_m', '?')}m")

    f = s.get("foundation", {})
    print(f"\n🏗️  Foundation: {f.get('type', '?')}")
    print(f"   Depth: {f.get('depth_m', '?')}m")
    print(f"   Rationale: {f.get('rationale', '?')}")

    mep = spec.get("mep", {})
    mech = mep.get("mechanical", {})
    print(f"\n🌬️  Ventilation: {mech.get('ventilation_strategy', '?')}")

    adaptations = spec.get("climate_adaptations", {})
    if isinstance(adaptations, list):
        features = adaptations
    else:
        features = adaptations.get("features", [])
    print(f"\n🌍 Climate Adaptations ({len(features)}):")
    for a in features:
        print(f"   • {a.get('feature', '?')}: {a.get('specification', '?')}")

    rationale = spec.get("design_rationale", {})
    print(f"\n📝 Design Narrative:")
    print(f"   {rationale.get('narrative', '?')}")

    print("\n" + "=" * 70)
    print("✅ Done! Open dar_es_salaam_building_spec.json for full details.")
    print("   Next step: Feed this into the IFC generator! 🏗️")
    print("=" * 70)


if __name__ == "__main__":
    if "--live" in sys.argv:
        demo_with_live_data()
    else:
        demo_with_sample_data()