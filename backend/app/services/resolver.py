"""Deterministic dispatch resolver (#3, A-system). Pure function: same
(characters, scenario, seed) always yields the same outcome — so results are
reproducible and the frontend can replay the log. No LLM involved.

requirements schema (on Scenario.requirements):
  { "min": {axis: threshold, ...},          # team must meet each
    "fail_above": {axis: cap, ...},         # over -> auto-fail (Dispatch-style)
    "synergy_traits": ["curious", ...] }    # matching team traits give a bonus
"""

import random

from app.core.constants import CORE_AXIS_IDS


def team_radar(characters: list[dict], axis_ids: list[str]) -> dict[str, int]:
    """A team covers an axis at the best member's value."""
    return {
        ax: max((int((c.get("radar") or {}).get(ax, 0)) for c in characters), default=0)
        for ax in axis_ids
    }


def _flavor(scenario: dict, outcome: str, characters: list[dict]) -> str:
    tmpl = (scenario.get("text_templates") or {}).get(outcome, "")
    name = (characters[0].get("name") if characters else None) or "夥伴"
    return tmpl.replace("{name}", name)


def resolve(characters: list[dict], scenario: dict, seed: int,
            axis_ids: list[str] | None = None) -> dict:
    axis_ids = axis_ids or list(CORE_AXIS_IDS)
    rng = random.Random(seed)
    req = scenario.get("requirements") or {}
    radar = team_radar(characters, axis_ids)
    steps: list[dict] = []

    # 1) over-threshold auto-fail
    for ax, cap in (req.get("fail_above") or {}).items():
        have = radar.get(ax, 0)
        if have > cap:
            steps.append({"type": "fail_above", "axis": ax, "have": have, "cap": cap})
            return {"outcome": "fail",
                    "log": {"steps": steps, "reason": "over_threshold",
                            "text": _flavor(scenario, "fail", characters)},
                    "rewards": {}}

    # 2) minimum requirements + margin
    passed = True
    margin = 0
    for ax, need in (req.get("min") or {}).items():
        have = radar.get(ax, 0)
        ok = have >= need
        steps.append({"type": "check", "axis": ax, "have": have, "need": need, "ok": ok})
        margin += have - need
        passed = passed and ok

    # 3) trait synergy bonus
    team_traits = {t for c in characters for t in (c.get("trait_tags") or [])}
    syn_hit = [t for t in (req.get("synergy_traits") or []) if t in team_traits]
    if syn_hit:
        margin += 10 * len(syn_hit)
        steps.append({"type": "synergy", "traits": syn_hit, "bonus": 10 * len(syn_hit)})

    # 4) seeded roll for variability
    roll = rng.randint(-10, 10)
    steps.append({"type": "roll", "value": roll})

    success = passed and (margin + roll) >= 0
    outcome = "success" if success else "fail"
    return {
        "outcome": outcome,
        "log": {"steps": steps, "margin": margin, "roll": roll,
                "text": _flavor(scenario, outcome, characters)},
        "rewards": (scenario.get("rewards") or {}) if success else {},
    }
