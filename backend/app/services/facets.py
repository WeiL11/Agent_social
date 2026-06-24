"""Turn a validated self-extract payload into ranked facet candidates. The
self-extract source already carries facets (the user's own model clustered
them); we just sanitize, whitelist, and rank by weight."""

from app.core.constants import TRAIT_WHITELIST, VALID_FACETS
from app.schemas.profile import FacetIn, SelfExtractProfileIn


def sanitize_trait_tags(tags: list[str]) -> list[str]:
    return [t for t in tags if t in TRAIT_WHITELIST]


def rank_facets(profile: SelfExtractProfileIn, threshold: int) -> list[FacetIn]:
    """Keep valid facets above the weight threshold, highest weight first."""
    kept: list[FacetIn] = []
    for f in profile.facets:
        facet = f.facet if f.facet in VALID_FACETS else "learning"
        f = f.model_copy(update={"facet": facet, "trait_tags": sanitize_trait_tags(f.trait_tags)})
        if f.weight >= threshold:
            kept.append(f)
    # Fallback: if everything got filtered, keep the single strongest so the
    # player always ends up with at least one character.
    if not kept and profile.facets:
        strongest = max(profile.facets, key=lambda x: x.weight)
        strongest = strongest.model_copy(
            update={
                "facet": strongest.facet if strongest.facet in VALID_FACETS else "learning",
                "trait_tags": sanitize_trait_tags(strongest.trait_tags),
            }
        )
        kept = [strongest]
    return sorted(kept, key=lambda x: x.weight, reverse=True)
