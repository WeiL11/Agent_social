"""邂逅 (explore) + real extraction: sprite meets compatible strangers, digest
shows the encounter, extraction turns raw text into characters."""

from app.core.config import settings
from app.services.extraction import rule_based_extract
from tests.conftest import auth


def _mk(client, user, facet="creative", radar=None):
    body = {"source": "self_extract", "apply_mode": "create_new",
            "profile": {"version": "1.0", "facets": [
                {"facet": facet, "weight": 85,
                 "radar": radar or {"creativity": 85, "curiosity": 80},
                 "trait_tags": ["curious"]}]}}
    return client.post("/profiles", json=body, headers=auth(user)).json()["created"][0]


def test_explore_meets_stranger_and_digest(client, monkeypatch):
    monkeypatch.setattr(settings, "character_explore_daily_limit", 2)
    mine = _mk(client, "alice")
    other = _mk(client, "bob")

    r = client.post(f"/characters/{mine['id']}/explore", headers=auth("alice")).json()
    assert r["encounter"] is not None
    assert r["encounter"]["other_character"]["id"] == other["id"]
    assert r["encounter"]["summary"]
    assert 0 <= r["encounter"]["compatibility"] <= 100
    assert r["remaining_today"] == 1

    digest = client.get("/me/encounters", headers=auth("alice")).json()
    assert len(digest) == 1
    assert digest[0]["other_character"]["id"] == other["id"]
    # never meet the same sprite twice
    r2 = client.post(f"/characters/{mine['id']}/explore", headers=auth("alice")).json()
    assert r2["encounter"] is None  # only bob exists and already met


def test_explore_daily_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "character_explore_daily_limit", 1)
    mine = _mk(client, "alice")
    _mk(client, "bob")
    _mk(client, "carol")
    assert client.post(f"/characters/{mine['id']}/explore", headers=auth("alice")).json()["encounter"]
    r = client.post(f"/characters/{mine['id']}/explore", headers=auth("alice")).json()
    assert r["encounter"] is None
    assert r["remaining_today"] == 0


def test_explore_skips_opted_out_users(client):
    mine = _mk(client, "alice")
    _mk(client, "hidden")
    client.put("/me", json={"discoverable": False}, headers=auth("hidden"))
    r = client.post(f"/characters/{mine['id']}/explore", headers=auth("alice")).json()
    assert r["encounter"] is None  # only candidate opted out


def test_rule_based_extraction_maps_signals():
    text = ("幫我 debug 這段 python code，有個 error。為什麼會這樣？"
            "我想分析一下原因。1. 先看 log 2. 再看 stack 3. 修 bug。再試一次！") * 3
    prof = rule_based_extract(text)
    assert prof.facets
    facets = {f.facet for f in prof.facets}
    assert "coding" in facets or "analytical" in facets
    radar = prof.facets[0].radar
    assert radar["logic"] > 40  # code+analysis signals present
    assert all(0 <= v <= 100 for v in radar.values())


def test_extract_endpoint_creates_characters(client):
    text = ("我在寫一個短篇故事，想要一點靈感。可以幫我設計角色嗎？"
            "我喜歡畫畫和寫作，story 和 design 是我的最愛。為什麼悲劇更動人？") * 4
    r = client.post("/profiles/extract", json={"text": text}, headers=auth("writer"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["engine"] == "rules"  # no gemini key in tests
    assert len(body["created"]) >= 1
    assert body["created"][0]["persona"]  # has a profile
