"""Handle onboarding via PUT /me (real-auth users pick a unique handle)."""

from tests.conftest import auth


def test_choose_handle_uniqueness_and_validation(client):
    client.get("/characters", headers=auth("alice"))  # provision alice
    client.get("/characters", headers=auth("bob"))

    # bob renames to a free handle
    r = client.put("/me", json={"handle": "cool-bob"}, headers=auth("bob"))
    assert r.status_code == 200
    assert r.json()["handle"] == "cool-bob"
    assert r.json()["handle_is_placeholder"] is False

    # alice cannot take bob's handle
    assert client.put("/me", json={"handle": "cool-bob"}, headers=auth("alice")).status_code == 409
    # invalid formats rejected
    assert client.put("/me", json={"handle": "A!"}, headers=auth("alice")).status_code == 400
    assert client.put("/me", json={"handle": "user-abc123"}, headers=auth("alice")).status_code == 400

    # discoverable-only update still works (no handle touched)
    r = client.put("/me", json={"discoverable": False}, headers=auth("alice"))
    assert r.json()["discoverable"] is False
