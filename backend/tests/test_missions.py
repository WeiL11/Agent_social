"""Missions: parse rules, bidirectional mutual-goal matching, sprite keyword
match, daily run limit, active cap."""

from app.core.config import settings
from app.services.missions import match_mission, parse_mission_rules
from tests.conftest import auth

W = {"similarity": 0.5, "traits": 0.25, "facet": 0.15, "complement": 0.10}
AXES = ["logic", "creativity"]


def test_parse_rules_kind_and_tags():
    p = parse_mission_rules("我最近開始跑步，想找路跑社團一起練")
    assert p["kind"] == "find_group"
    assert "跑步" in p["tags"]
    p2 = parse_mission_rules("我在用 claude 做 UI，想找有類似經驗分享的人")
    assert p2["kind"] == "find_experience"
    assert "ai" in p2["tags"] and "ui設計" in p2["tags"]
    p3 = parse_mission_rules("想找人一起打羽球")
    assert p3["kind"] == "find_people"
    assert "球類" in p3["tags"]


def test_match_mission_mutual_goal_beats_sprite_match():
    me = {"id": "m", "owner_id": "u0", "radar": {"logic": 60}, "trait_tags": [], "facet": "social"}
    other_char = {"id": "a", "owner_id": "u1", "name": "跑者", "radar": {"logic": 60},
                  "trait_tags": [], "facet": "social", "persona": "喜歡慢跑的小夥伴"}
    other_missions = [{"tags": ["跑步"], "query_text": "找晨跑夥伴",
                       "character": {"id": "b", "owner_id": "u2", "radar": {"logic": 60},
                                     "trait_tags": [], "facet": "social", "persona": ""}}]
    items = match_mission({"tags": ["跑步"], "query_text": "想找跑友"}, me,
                          other_missions, [other_char], W, AXES)
    assert len(items) == 2
    assert items[0]["type"] == "mutual_goal"          # 雙向同目標排最前
    assert items[1]["type"] == "sprite_match"
    assert "跑步" in items[1]["matched_tags"]          # persona 提到慢跑 → alias 命中


def test_match_dedups_by_owner():
    me = {"id": "m", "owner_id": "u0", "radar": {}, "trait_tags": [], "facet": None}
    c1 = {"id": "a", "owner_id": "same", "name": "x", "radar": {}, "trait_tags": [],
          "facet": None, "persona": "跑步跑步"}
    om = [{"tags": ["跑步"], "query_text": "q",
           "character": {"id": "b", "owner_id": "same", "radar": {}, "trait_tags": [], "facet": None}}]
    items = match_mission({"tags": ["跑步"], "query_text": "q"}, me, om, [c1], W, AXES)
    assert len(items) == 1  # one owner -> one best item


def _mk_char(client, user, text):
    return client.post("/profiles/extract", json={"text": text}, headers=auth(user)).json()


def test_mission_end_to_end_bidirectional(client):
    _mk_char(client, "runner_a", "我每天早上慢跑，最近在練馬拉松，跑步讓我很快樂" * 2)
    _mk_char(client, "runner_b", "剛開始學跑步，想養成路跑習慣，順便交朋友" * 2)

    ma = client.post("/missions", json={"query_text": "想找一起跑步的夥伴"}, headers=auth("runner_a"))
    assert ma.status_code == 200, ma.text
    mb = client.post("/missions", json={"query_text": "找路跑同好一起晨跑"}, headers=auth("runner_b"))
    body_b = mb.json()
    # B 建立時 A 的任務已存在 → B 立刻找到 mutual goal
    assert any(i["type"] == "mutual_goal" for i in body_b["items"]), body_b
    assert body_b["report"]

    # A 重跑 → 現在也找到 B
    rerun = client.post(f"/missions/{ma.json()['id']}/run", headers=auth("runner_a")).json()
    assert any(i["type"] == "mutual_goal" for i in rerun["items"])
    assert rerun["items"][0]["character"] is not None  # hydrated public profile


def test_mission_daily_run_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "mission_daily_runs", 1)
    _mk_char(client, "alice", "我喜歡攝影和拍照，也愛旅行" * 3)
    m = client.post("/missions", json={"query_text": "找攝影同好"}, headers=auth("alice")).json()
    # 建立時已跑 1 次 → 再跑超限
    assert client.post(f"/missions/{m['id']}/run", headers=auth("alice")).status_code == 429


def test_mission_active_cap(client, monkeypatch):
    monkeypatch.setattr(settings, "mission_active_cap", 1)
    _mk_char(client, "bob", "我熱愛煮飯做菜料理烘焙" * 3)
    assert client.post("/missions", json={"query_text": "找料理同好"}, headers=auth("bob")).status_code == 200
    assert client.post("/missions", json={"query_text": "找烘焙夥伴"}, headers=auth("bob")).status_code == 409
