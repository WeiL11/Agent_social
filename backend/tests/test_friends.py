"""Tests for the two friend layers: owner (user<->user, cap) and character
(creature<->creature, daily limit, only-the-other-creature visibility)."""

from app.core.config import settings
from tests.conftest import auth


def _make_char(client, user, facet="coding"):
    body = {"source": "self_extract", "apply_mode": "create_new",
            "profile": {"version": "1.0", "facets": [
                {"facet": facet, "weight": 80, "radar": {"logic": 70}}]}}
    return client.post("/profiles", json=body, headers=auth(user)).json()["created"][0]


def _make_friends(client, a, b):
    fid = client.post("/friends/requests", json={"handle": b}, headers=auth(a)).json()["friendship_id"]
    client.post(f"/friends/requests/{fid}/accept", headers=auth(b))


# ---- owner-level (user) friends ----

def test_owner_friend_can_see_friends_roster(client):
    _make_char(client, "alice")
    _make_char(client, "bob")
    _make_friends(client, "alice", "bob")
    bob_id = client.get("/friends", headers=auth("alice")).json()[0]["user_id"]
    roster = client.get(f"/friends/{bob_id}/characters", headers=auth("alice"))
    assert roster.status_code == 200
    assert len(roster.json()) == 1  # bob's whole roster is visible


def test_non_friend_cannot_see_roster(client):
    _make_char(client, "carol")
    client.get("/characters", headers=auth("dave"))  # provision dave
    carol_id = client.post("/friends/requests", json={"handle": "carol"}, headers=auth("dave"))
    # dave only sent a request (pending), not accepted
    cid = carol_id.json()["user_id"]
    r = client.get(f"/friends/{cid}/characters", headers=auth("dave"))
    assert r.status_code == 403


def test_owner_friend_cap(client, monkeypatch):
    monkeypatch.setattr(settings, "owner_friend_cap", 1)
    client.get("/characters", headers=auth("u1"))
    client.get("/characters", headers=auth("u2"))
    client.get("/characters", headers=auth("u3"))
    _make_friends(client, "u1", "u2")  # u1 now has 1 accepted (== cap)
    r = client.post("/friends/requests", json={"handle": "u3"}, headers=auth("u1"))
    assert r.status_code == 409


# ---- character-level (creature) friends ----

def test_character_friend_daily_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "character_friend_daily_limit", 2)
    mine = _make_char(client, "alice")["id"]
    t1 = _make_char(client, "bob")["id"]
    t2 = _make_char(client, "carol")["id"]
    t3 = _make_char(client, "dave")["id"]
    r1 = client.post(f"/characters/{mine}/friends", json={"target_character_id": t1}, headers=auth("alice"))
    assert r1.status_code == 200
    assert r1.json()["remaining_today"] == 1
    assert client.post(f"/characters/{mine}/friends", json={"target_character_id": t2}, headers=auth("alice")).status_code == 200
    third = client.post(f"/characters/{mine}/friends", json={"target_character_id": t3}, headers=auth("alice"))
    assert third.status_code == 429  # daily limit


def test_character_friend_list_shows_only_other_creature(client):
    mine = _make_char(client, "alice")["id"]
    target = _make_char(client, "bob")
    client.post(f"/characters/{mine}/friends", json={"target_character_id": target["id"]}, headers=auth("alice"))
    friends = client.get(f"/characters/{mine}/friends", headers=auth("alice")).json()
    assert len(friends) == 1
    assert friends[0]["id"] == target["id"]
    assert "owner_id" not in friends[0]  # owner is never revealed at character level


def test_cannot_befriend_self(client):
    mine = _make_char(client, "alice")["id"]
    r = client.post(f"/characters/{mine}/friends", json={"target_character_id": mine}, headers=auth("alice"))
    assert r.status_code == 400
