"""Character<->character short chat: friend-gated, bounded length, summary, limit."""

from app.core.config import settings
from tests.conftest import auth


def _make_char(client, user):
    body = {"source": "self_extract", "apply_mode": "create_new",
            "profile": {"version": "1.0", "facets": [
                {"facet": "coding", "weight": 80, "radar": {"logic": 70}, "trait_tags": ["curious"]}]}}
    return client.post("/profiles", json=body, headers=auth(user)).json()["created"][0]["id"]


def _befriend_chars(client, mine, target_id):
    return client.post(f"/characters/{mine}/friends",
                       json={"target_character_id": target_id}, headers=auth("alice")).status_code


def test_chat_requires_friendship(client):
    mine = _make_char(client, "alice")
    other = _make_char(client, "bob")
    r = client.post(f"/characters/{mine}/chats", json={"with_character_id": other}, headers=auth("alice"))
    assert r.status_code == 403


def test_chat_is_short_and_summarized(client, monkeypatch):
    monkeypatch.setattr(settings, "character_chat_turns", 3)
    mine = _make_char(client, "alice")
    other = _make_char(client, "bob")
    _befriend_chars(client, mine, other)
    r = client.post(f"/characters/{mine}/chats", json={"with_character_id": other}, headers=auth("alice"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["transcript"]) == 6  # 3 turns * 2 speakers — bounded
    assert body["summary"]
    # appears in the character's chat list
    lst = client.get(f"/characters/{mine}/chats", headers=auth("alice")).json()
    assert any(c["id"] == body["id"] for c in lst)


def test_chat_daily_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "character_chat_daily_limit", 1)
    mine = _make_char(client, "alice")
    t1 = _make_char(client, "bob")
    t2 = _make_char(client, "carol")
    _befriend_chars(client, mine, t1)
    _befriend_chars(client, mine, t2)
    assert client.post(f"/characters/{mine}/chats", json={"with_character_id": t1}, headers=auth("alice")).status_code == 200
    assert client.post(f"/characters/{mine}/chats", json={"with_character_id": t2}, headers=auth("alice")).status_code == 429
