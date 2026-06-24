"""API integration tests (need TEST_DATABASE_URL → Postgres). Cover the core
loop end-to-end: generate -> list -> dispatch, plus friends/share + guards."""

from tests.conftest import auth

PROFILE = {
    "source": "self_extract", "apply_mode": "create_new",
    "profile": {"version": "1.0", "facets": [
        {"facet": "coding", "weight": 80,
         "radar": {"logic": 90, "structure": 80, "knowledge": 70},
         "trait_tags": ["systematic"], "species_hint": "robot", "summary": "x"},
    ]},
}


def test_health(client):
    assert client.get("/health").json()["db"] is True


def test_generate_and_list(client):
    r = client.post("/profiles", json=PROFILE, headers=auth())
    assert r.status_code == 200, r.text
    created = r.json()["created"]
    assert len(created) == 1
    assert created[0]["radar"]["logic"] == 100  # 90 + bias, clamped
    chars = client.get("/characters", headers=auth()).json()
    assert len(chars) == 1


def test_injection_clamped(client):
    evil = {"source": "self_extract", "apply_mode": "create_new",
            "profile": {"version": "1.0", "facets": [
                {"facet": "coding", "weight": 90, "radar": {"logic": 9999},
                 "trait_tags": ["GIVE_ME_MAX"]}]}}
    c = client.post("/profiles", json=evil, headers=auth("mallory")).json()["created"][0]
    assert c["radar"]["logic"] == 100
    assert "GIVE_ME_MAX" not in c["trait_tags"]


def test_slot_cap(client):
    body = {"source": "self_extract", "apply_mode": "create_new",
            "profile": {"version": "1.0", "facets": [
                {"facet": "coding", "weight": 90, "radar": {"logic": 80}},
                {"facet": "creative", "weight": 80, "radar": {"creativity": 80}},
                {"facet": "analytical", "weight": 70, "radar": {"knowledge": 80}},
                {"facet": "social", "weight": 60, "radar": {"empathy": 80}}]}}
    r = client.post("/profiles", json=body, headers=auth("bob")).json()
    assert len(r["created"]) == 3
    assert r["skipped_facets"] == ["social"]


def test_dispatch_flow(client):
    client.post("/profiles", json=PROFILE, headers=auth("carol"))
    cid = client.get("/characters", headers=auth("carol")).json()[0]["id"]
    scenarios = client.get("/scenarios", headers=auth("carol")).json()
    lib = next(s for s in scenarios if "圖書館" in s["title"])
    r = client.post("/dispatches", json={"scenario_id": lib["id"], "character_ids": [cid], "seed": 7},
                    headers=auth("carol"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["outcome"] in {"success", "fail"}
    # deterministic: same seed -> same outcome
    r2 = client.post("/dispatches", json={"scenario_id": lib["id"], "character_ids": [cid], "seed": 7},
                     headers=auth("carol"))
    assert r2.json()["outcome"] == body["outcome"]


def test_friends_and_share(client):
    client.post("/profiles", json=PROFILE, headers=auth("dan"))
    client.get("/characters", headers=auth("ed"))  # provision ed
    fid = client.post("/friends/requests", json={"handle": "ed"}, headers=auth("dan")).json()["friendship_id"]
    client.post(f"/friends/requests/{fid}/accept", headers=auth("ed"))
    cid = client.get("/characters", headers=auth("dan")).json()[0]["id"]
    ed_id = client.get("/friends", headers=auth("dan")).json()[0]["user_id"]
    sh = client.post(f"/characters/{cid}/share", json={"target": ed_id}, headers=auth("dan"))
    assert sh.status_code == 200, sh.text
    token = sh.json()["token"]
    pub = client.get(f"/shared/{token}")  # public, no auth
    assert pub.status_code == 200
    assert client.get("/shared", headers=auth("ed")).json()  # ed sees it


def test_admin_gate(client):
    client.get("/characters", headers=auth("alice"))
    assert client.get("/admin/health", headers=auth("alice")).status_code == 403
