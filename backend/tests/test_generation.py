from app.core.constants import CORE_AXIS_IDS
from app.schemas.profile import FacetIn, SelfExtractProfileIn
from app.services.facets import rank_facets
from app.services.generation import generate_character_fields


def test_schema_clamps_radar_and_caps_facets():
    p = SelfExtractProfileIn.model_validate({
        "version": "1.0",
        "facets": [{"facet": "coding", "weight": 80, "radar": {"logic": 9999, "structure": -5},
                    "trait_tags": ["systematic", "EVIL_TAG"]}] * 10,
    })
    assert len(p.facets) == 4  # MAX_FACETS
    assert p.facets[0].radar["logic"] == 100
    assert p.facets[0].radar["structure"] == 0


def test_rank_facets_whitelists_traits_and_orders_by_weight():
    prof = SelfExtractProfileIn.model_validate({
        "version": "1.0",
        "facets": [
            {"facet": "creative", "weight": 40, "trait_tags": ["imaginative", "EVIL"]},
            {"facet": "coding", "weight": 90, "trait_tags": ["systematic"]},
        ],
    })
    ranked = rank_facets(prof, threshold=30)
    assert [f.facet for f in ranked] == ["coding", "creative"]
    assert "EVIL" not in ranked[1].trait_tags


def test_generation_maps_archetype_and_clamps_with_bias():
    facet = FacetIn(facet="coding", weight=80, radar={"logic": 95}, trait_tags=["systematic"])
    fields = generate_character_fields(facet, list(CORE_AXIS_IDS), llm_provider="none")
    assert fields["archetype"] == "analyst"
    assert fields["name"]
    assert fields["radar"]["logic"] == 100  # 95 + analyst bias, clamped
    assert set(fields["radar"]) == set(CORE_AXIS_IDS)  # all axes present
