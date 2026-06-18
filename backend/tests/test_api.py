"""API/integration tests via FastAPI TestClient (no ML pipeline involved)."""


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model"] == "gemini-2.5-flash"
    assert "gemini_configured" in body


def test_meetings_open_when_auth_off(client):
    r = client.get("/api/meetings")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_meeting_detail_404(client):
    assert client.get("/api/meetings/999999").status_code == 404


def test_login_disabled_returns_400(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "x"})
    assert r.status_code == 400


def test_auth_flow_when_enabled(client, auth_on):
    # protected route now rejects unauthenticated requests
    assert client.get("/api/meetings").status_code == 401
    assert client.post("/api/search", json={"query": "hi"}).status_code == 401

    # wrong credentials
    bad = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert bad.status_code == 401

    # correct credentials -> token
    r = client.post("/api/auth/login", json=auth_on)
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert r.json()["token_type"] == "bearer"

    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/meetings", headers=headers).status_code == 200

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert me.json()["auth_enabled"] is True

    # health and login stay public even with auth enabled
    assert client.get("/api/health").status_code == 200


def test_bad_token_rejected(client, auth_on):
    r = client.get("/api/meetings", headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code == 401
