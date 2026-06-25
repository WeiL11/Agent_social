"""Owner-friend direct messages: friend-gated, send/list/read, conversations."""

from tests.conftest import auth


def _make_char(client, user):
    body = {"source": "self_extract", "apply_mode": "create_new",
            "profile": {"version": "1.0", "facets": [{"facet": "coding", "weight": 80, "radar": {"logic": 70}}]}}
    client.post("/profiles", json=body, headers=auth(user))


def _befriend(client, a, b):
    client.get("/characters", headers=auth(a))
    client.get("/characters", headers=auth(b))
    fid = client.post("/friends/requests", json={"handle": b}, headers=auth(a)).json()["friendship_id"]
    client.post(f"/friends/requests/{fid}/accept", headers=auth(b))
    return client.get("/friends", headers=auth(a)).json()[0]["user_id"]  # b's user_id


def test_cannot_message_non_friend(client):
    client.get("/characters", headers=auth("alice"))
    other = client.get("/characters", headers=auth("stranger"))  # noqa: F841
    # need stranger's user_id; fetch via a friend request that we DON'T accept
    req = client.post("/friends/requests", json={"handle": "stranger"}, headers=auth("alice")).json()
    r = client.post(f"/friends/{req['user_id']}/messages", json={"body": "hi"}, headers=auth("alice"))
    assert r.status_code == 403


def test_send_list_and_read(client):
    bob_id = _befriend(client, "alice", "bob")
    alice_id = client.get("/friends", headers=auth("bob")).json()[0]["user_id"]

    client.post(f"/friends/{bob_id}/messages", json={"body": "嗨 bob"}, headers=auth("alice"))
    client.post(f"/friends/{alice_id}/messages", json={"body": "嗨 alice"}, headers=auth("bob"))

    # alice sees both, ordered; her incoming (from bob) gets marked read on fetch
    msgs = client.get(f"/friends/{bob_id}/messages", headers=auth("alice")).json()
    assert [m["body"] for m in msgs] == ["嗨 bob", "嗨 alice"]
    assert msgs[0]["from_me"] is True and msgs[1]["from_me"] is False


def test_conversations_unread(client):
    bob_id = _befriend(client, "alice", "bob")
    client.post(f"/friends/{bob_id}/messages", json={"body": "ping"}, headers=auth("alice"))
    convos = client.get("/conversations", headers=auth("bob")).json()
    assert len(convos) == 1
    assert convos[0]["unread"] == 1
    assert convos[0]["last_message"] == "ping"
    # after bob reads, unread clears
    client.get(f"/friends/{convos[0]['friend_user_id']}/messages", headers=auth("bob"))
    assert client.get("/conversations", headers=auth("bob")).json()[0]["unread"] == 0
