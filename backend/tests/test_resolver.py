from app.services.progression import apply_rewards, level_for_xp
from app.services.resolver import resolve, team_radar

AXES = ["logic", "structure", "humor", "empathy"]


def _char(radar, traits=None, name="x"):
    return {"name": name, "radar": radar, "trait_tags": traits or []}


def test_determinism_same_seed():
    chars = [_char({"logic": 80, "structure": 70})]
    scen = {"requirements": {"min": {"logic": 60}}, "rewards": {"xp": 50}, "text_templates": {}}
    a = resolve(chars, scen, seed=42, axis_ids=AXES)
    b = resolve(chars, scen, seed=42, axis_ids=AXES)
    assert a == b


def test_min_requirement_pass_and_fail():
    scen = {"requirements": {"min": {"logic": 60}}, "rewards": {"xp": 50}, "text_templates": {}}
    ok = resolve([_char({"logic": 90})], scen, seed=1, axis_ids=AXES)
    assert ok["outcome"] == "success"
    assert ok["rewards"] == {"xp": 50}
    bad = resolve([_char({"logic": 10})], scen, seed=1, axis_ids=AXES)
    assert bad["outcome"] == "fail"
    assert bad["rewards"] == {}


def test_fail_above_auto_fail():
    scen = {"requirements": {"min": {"logic": 10}, "fail_above": {"humor": 90}},
            "rewards": {"xp": 50}, "text_templates": {}}
    res = resolve([_char({"logic": 99, "humor": 99})], scen, seed=1, axis_ids=AXES)
    assert res["outcome"] == "fail"
    assert res["log"]["reason"] == "over_threshold"


def test_team_radar_takes_best():
    r = team_radar([_char({"logic": 30}), _char({"logic": 80})], AXES)
    assert r["logic"] == 80


def test_synergy_helps():
    scen = {"requirements": {"min": {"logic": 75}, "synergy_traits": ["curious"]},
            "rewards": {"xp": 10}, "text_templates": {}}
    # logic just below; synergy bonus + a decent roll can push it over on some seeds
    outcomes = {resolve([_char({"logic": 75}, ["curious"])], scen, seed=s, axis_ids=AXES)["outcome"]
                for s in range(20)}
    assert "success" in outcomes


def test_progression_levels_up():
    class C:
        xp = 90
        level = 1
    c = C()
    summary = apply_rewards(c, {"xp": 50})
    assert c.xp == 140
    assert c.level == level_for_xp(140) == 2
    assert summary["xp_gained"] == 50
