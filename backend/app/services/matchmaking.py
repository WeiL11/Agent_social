"""Personality compatibility (model A: persona as matchmaker). Pure function,
no LLM. Weights are tunable via settings so the matching philosophy (similar vs
complementary) can be decided later without code changes."""

import math

from app.core.constants import CORE_AXES, CORE_AXIS_IDS, FACET_LABELS

_AXIS_NAME = {a["id"]: a["name"] for a in CORE_AXES}


def _cosine(a: dict, b: dict, axes: list[str]) -> float:
    va = [float(a.get(ax, 0)) for ax in axes]
    vb = [float(b.get(ax, 0)) for ax in axes]
    dot = sum(x * y for x, y in zip(va, vb, strict=False))
    na = math.sqrt(sum(x * x for x in va))
    nb = math.sqrt(sum(y * y for y in vb))
    return dot / (na * nb) if na and nb else 0.0


def compatibility(a: dict, b: dict, weights: dict[str, float],
                  axis_ids: list[str] | None = None) -> dict:
    """a, b are character-like dicts: {radar, trait_tags, facet}. Returns
    {score: 0..100, reasons: [str]}."""
    axes = axis_ids or list(CORE_AXIS_IDS)
    ra, rb = a.get("radar") or {}, b.get("radar") or {}

    sim = _cosine(ra, rb, axes)  # 0..1, vibe alignment

    ta, tb = set(a.get("trait_tags") or []), set(b.get("trait_tags") or [])
    shared = ta & tb
    trait_score = len(shared) / min(len(ta), len(tb)) if ta and tb else 0.0

    facet_match = 1.0 if a.get("facet") and a.get("facet") == b.get("facet") else 0.0

    comp = sum(abs(ra.get(ax, 0) - rb.get(ax, 0)) for ax in axes) / (len(axes) * 100)  # 0..1

    total = sum(weights.values()) or 1.0
    raw = (
        weights.get("similarity", 0) * sim
        + weights.get("traits", 0) * trait_score
        + weights.get("facet", 0) * facet_match
        + weights.get("complement", 0) * comp
    ) / total
    score = round(100 * raw)

    reasons: list[str] = []
    if facet_match:
        label = FACET_LABELS.get(a["facet"], a["facet"])
        reasons.append(f"都有「{label}」分身")
    if shared:
        reasons.append("共同特質：" + "、".join(sorted(shared)[:3]))
    high = [_AXIS_NAME[ax] for ax in axes if ra.get(ax, 0) >= 70 and rb.get(ax, 0) >= 70]
    if high:
        reasons.append("都很強：" + "、".join(high[:3]))
    if not reasons:
        reasons.append("性格頗有共鳴")

    return {"score": score, "reasons": reasons}
