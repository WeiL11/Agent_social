"""Personality enrichment: apply a new facet signal to an EXISTING character as
a gentle delta (average toward the new radar, union traits) — never a full
regeneration, so the personality stays stable (anti-drift)."""

from app.schemas.profile import FacetIn
from app.services.generation import generate_character_fields


def apply_enrich(char, facet: FacetIn, axis_ids: list[str], llm_provider: str) -> None:
    """Mutates the ORM character in place; caller commits."""
    fields = generate_character_fields(facet, axis_ids, llm_provider)
    merged = dict(char.radar or {})
    for axis, val in fields["radar"].items():
        merged[axis] = int((merged.get(axis, val) + val) / 2)
    char.radar = merged
    char.trait_tags = sorted(set((char.trait_tags or []) + fields["trait_tags"]))
