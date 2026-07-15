"""Talking to your own sprite: template reply, intent suggestion, enrichment
delta after N messages, daily limit, ownership."""

from app.core.config import settings
from tests.conftest import auth


def _mk_char(client, user):
    r = client.post("/profiles/extract",
                    json={"text": "我喜歡寫程式 debug python，也愛分析問題找原因" * 2},
                    headers=auth(user))
    return r.json()["created"][0]


def test_talk_reply_and_history(client):
    c = _mk_char(client, "alice")
    r = client.post(f"/characters/{c['id']}/talk", json={"message": "嗨！今天過得如何？"},
                    headers=auth("alice"))
    assert r.status_code == 200, r.text
    assert r.json()["reply"]["text"]
    hist = client.get(f"/characters/{c['id']}/talk", headers=auth("alice")).json()
    assert [m["role"] for m in hist] == ["user", "sprite"]


def test_talk_mission_intent_suggestion(client):
    c = _mk_char(client, "alice")
    r = client.post(f"/characters/{c['id']}/talk", json={"message": "我想找人一起爬山"},
                    headers=auth("alice")).json()
    assert r["suggest_mission"] is True


def test_talk_enrichment_after_n_messages(client, monkeypatch):
    monkeypatch.setattr(settings, "sprite_talk_enrich_every", 3)
    c = _mk_char(client, "alice")
    before = client.get(f"/characters/{c['id']}", headers=auth("alice")).json()
    msgs = ["今天寫了一首詩，感覺創作好療癒，靈感一直來",
            "我開始畫插畫了，畫畫讓我放鬆，好想寫故事",
            "週末想寫小說，設計一個奇幻世界，創作萬歲"]
    enriched_flags = []
    for m in msgs:
        rr = client.post(f"/characters/{c['id']}/talk", json={"message": m}, headers=auth("alice")).json()
        enriched_flags.append(rr["enriched"])
    assert enriched_flags[-1] is True  # 第 3 句觸發
    after = client.get(f"/characters/{c['id']}", headers=auth("alice")).json()
    assert after["radar"] != before["radar"]  # 個性有 delta


def test_talk_daily_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "sprite_talk_daily_limit", 2)
    c = _mk_char(client, "alice")
    for _ in range(2):
        assert client.post(f"/characters/{c['id']}/talk", json={"message": "hi"},
                           headers=auth("alice")).status_code == 200
    assert client.post(f"/characters/{c['id']}/talk", json={"message": "hi"},
                       headers=auth("alice")).status_code == 429


def test_talk_ownership_guard(client):
    c = _mk_char(client, "alice")
    client.get("/characters", headers=auth("mallory"))
    assert client.post(f"/characters/{c['id']}/talk", json={"message": "hi"},
                       headers=auth("mallory")).status_code == 404
