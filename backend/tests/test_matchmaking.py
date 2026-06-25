"""Matchmaking: compatibility scoring (pure) + matches/wave handshake (API)."""

from app.services.matchmaking import compatibility
from tests.conftest import auth

W = {"similarity": 0.5, "traits": 0.25, "facet": 0.15, "complement": 0.10}
AXES = ["logic", "creativity", "empathy", "humor"]


def test_compatibility_alike_scores_higher_than_opposite():
    a = {"radar": {"logic": 90, "creativity": 80}, "trait_tags": ["systematic"], "facet": "coding"}
    alike = {"radar": {"logic": 88, "creativity": 78}, "trait_tags": ["systematic"], "facet": "coding"}
    opposite = {"radar": {"logic": 10, "creativity": 10}, "trait_tags": ["playful"], "facet": "social"}
    s_alike = compatibility(a, alike, W, AXES)["score"]
    s_opp = compatibility(a, opposite, W, AXES)["score"]
    assert s_alike > s_opp


def test_compatibility_reasons_mention_shared():
    a = {"radar": {"logic": 80}, "trait_tags": ["curious", "systematic"], "facet": "coding"}
    b = {"radar": {"logic": 80}, "trait_tags": ["curious"], "facet": "coding"}
    reasons = compatibility(a, b, W, AXES)["reasons"]
    joined = " ".join(reasons)
    assert "分身" in joined or "共同特質" in joined


def _make_char(client, user, radar, facet="coding"):
    body = {"source": "self_extract", "apply_mode": "create_new",
            "profile": {"version": "1.0", "facets": [
                {"facet": facet, "weight": 80, "radar": radar, "trait_tags": ["curious"]}]}}
    return client.post("/profiles", json=body, headers=auth(user)).json()["created"][0]


def test_matches_and_mutual_wave_creates_friendship(client):
    _make_char(client, "alice", {"logic": 85, "creativity": 60})
    bob_char = _make_char(client, "bob", {"logic": 82, "creativity": 58})

    matches = client.get("/matches", headers=auth("alice")).json()
    assert any(m["their_character"]["id"] == bob_char["id"] for m in matches)
    assert all(0 <= m["score"] <= 100 for m in matches)

    # alice waves at bob -> not yet mutual
    r1 = client.post(f"/matches/{bob_char['id']}/wave", headers=auth("alice")).json()
    assert r1["matched"] is False

    # bob waves back at one of alice's characters -> mutual -> owner friends
    alice_char_id = client.get("/characters", headers=auth("alice")).json()[0]["id"]
    r2 = client.post(f"/matches/{alice_char_id}/wave", headers=auth("bob")).json()
    assert r2["matched"] is True
    assert r2["friendship_id"]
    # they are now owner-friends
    assert any(f["direction"] == "friends" for f in client.get("/friends", headers=auth("alice")).json())


def test_discoverable_opt_out_hides_from_matches(client):
    _make_char(client, "alice", {"logic": 85})
    _make_char(client, "hidden", {"logic": 85})
    client.put("/me", json={"discoverable": False}, headers=auth("hidden"))
    matches = client.get("/matches", headers=auth("alice")).json()
    hidden_handles = [m for m in matches]  # hidden user's chars should be absent
    # hidden has opted out; ensure none of alice's matches belong to hidden by re-checking pool size
    assert isinstance(hidden_handles, list)
    # alice still sees others but not 'hidden' (can't see owner, so assert hidden's char id absent)
    hidden_char = client.get("/characters", headers=auth("hidden")).json()[0]["id"]
    assert all(m["their_character"]["id"] != hidden_char for m in matches)
