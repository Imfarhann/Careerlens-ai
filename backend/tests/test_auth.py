def test_register_creates_user(client, user_payload):
    response = client.post("/auth/register", json=user_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["id"]
    assert body["created_at"]
    assert "password" not in body
    assert "password_hash" not in body


def test_register_normalizes_email(client, user_payload):
    client.post(
        "/auth/register",
        json={"email": "  User@Example.com ", "password": "rahasia123"},
    )

    assert user_payload["email"] == "user@example.com"
    duplicate = client.post("/auth/register", json=user_payload)
    assert duplicate.status_code == 409


def test_register_duplicate_email_conflict(client, user_payload):
    client.post("/auth/register", json=user_payload)

    response = client.post("/auth/register", json=user_payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email sudah terdaftar"


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={"email": "bukan-email", "password": "rahasia123"},
    )

    assert response.status_code == 422


def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "pendek"},
    )

    assert response.status_code == 422


def test_login_returns_access_token(client, user_payload):
    client.post("/auth/register", json=user_payload)

    response = client.post("/auth/login", json=user_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_wrong_password(client, user_payload):
    client.post("/auth/register", json=user_payload)

    response = client.post(
        "/auth/login",
        json={"email": user_payload["email"], "password": "salah-sekali"},
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/auth/login",
        json={"email": "tidak-ada@example.com", "password": "rahasia123"},
    )

    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_me_requires_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_rejects_garbage_token(client):
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer bukan-token"}
    )

    assert response.status_code == 401


def test_me_rejects_token_for_deleted_user(client):
    import uuid

    from app.core.security import create_access_token

    token = create_access_token(subject=str(uuid.uuid4()))

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
