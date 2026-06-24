"""Rule-based character generation. The LLM only writes flavor text (persona);
all numbers come from rules + clamping so they are balanced, reproducible, and
impossible to inflate via prompt injection in the source conversation."""

from app.core.constants import (
    ARCHETYPES,
    CORE_AXIS_IDS,
    DEFAULT_ARCHETYPE,
    DEFAULT_AXIS_VALUE,
    FACET_TO_ARCHETYPE,
)
from app.schemas.profile import FacetIn
from app.services.deid import scrub

_ARCHETYPE_BY_ID = {a["id"]: a for a in ARCHETYPES}


def build_radar(facet: FacetIn, archetype_id: str, axis_ids: list[str]) -> dict[str, int]:
    """Merge the (already clamped) provided radar with the archetype bias over the
    active axis registry. Unknown/missing axes default to neutral."""
    bias = _ARCHETYPE_BY_ID.get(archetype_id, {}).get("bias", {})
    radar: dict[str, int] = {}
    for axis in axis_ids:
        base = facet.radar.get(axis, DEFAULT_AXIS_VALUE)
        radar[axis] = max(0, min(100, int(base) + int(bias.get(axis, 0))))
    return radar


def pick_archetype(facet: FacetIn) -> str:
    return FACET_TO_ARCHETYPE.get(facet.facet, DEFAULT_ARCHETYPE)


def pick_species(facet: FacetIn, archetype_id: str) -> str:
    if facet.species_hint:
        return facet.species_hint[:32]
    return _ARCHETYPE_BY_ID.get(archetype_id, {}).get("default_species") or "sprite"


def default_appearance(species: str, archetype_id: str) -> dict[str, str]:
    """Deterministic starter layered-avatar parts (cosmetic, decoupled from stats)."""
    return {
        "body": species,
        "eyes": "default",
        "hair": archetype_id,
        "outfit": "starter",
    }


def generate_persona(facet: FacetIn, archetype_id: str, llm_provider: str) -> str:
    """LLM flavor hook. Default 'none' returns a templated, de-identified persona.
    A real provider would be called here once with structured output + temp 0."""
    name = _ARCHETYPE_BY_ID.get(archetype_id, {}).get("name", "夥伴")
    summary = scrub(facet.summary) or "一個剛誕生、好奇心旺盛的小夥伴。"
    return f"【{name}】{summary}"


def generate_character_fields(facet: FacetIn, axis_ids: list[str], llm_provider: str) -> dict:
    archetype_id = pick_archetype(facet)
    species = pick_species(facet, archetype_id)
    return {
        "name": _ARCHETYPE_BY_ID.get(archetype_id, {}).get("name", "夥伴"),
        "facet": facet.facet,
        "archetype": archetype_id,
        "species": species,
        "radar": build_radar(facet, archetype_id, axis_ids or CORE_AXIS_IDS),
        "trait_tags": facet.trait_tags,
        "persona": generate_persona(facet, archetype_id, llm_provider),
        "appearance": default_appearance(species, archetype_id),
    }
