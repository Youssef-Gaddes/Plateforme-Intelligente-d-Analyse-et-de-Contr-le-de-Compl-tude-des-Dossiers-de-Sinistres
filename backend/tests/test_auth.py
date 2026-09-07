from conftest import register_user, login, auth_headers


def test_register_success(client):
    response = register_user(client, email="alice@test.com", role="gestionnaire")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@test.com"
    assert data["role"] == "gestionnaire"
    assert "password" not in data  # never leak the hash


def test_register_duplicate_email_rejected(client):
    register_user(client, email="bob@test.com")
    response = register_user(client, email="bob@test.com")
    assert response.status_code == 400


def test_register_invalid_role_rejected(client):
    response = client.post("/auth/register", json={
        "name": "Eve", "email": "eve@test.com", "password": "pass123", "role": "hacker"
    })
    assert response.status_code == 422  # Pydantic enum validation catches this


def test_login_success(client):
    register_user(client, email="carol@test.com", password="mypassword")
    response = client.post("/auth/login", json={
        "email": "carol@test.com", "password": "mypassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_rejected(client):
    register_user(client, email="dave@test.com", password="correctpass")
    response = client.post("/auth/login", json={
        "email": "dave@test.com", "password": "wrongpass"
    })
    assert response.status_code == 401


def test_login_nonexistent_user_rejected(client):
    response = client.post("/auth/login", json={
        "email": "ghost@test.com", "password": "whatever"
    })
    assert response.status_code == 401


def test_protected_route_requires_token(client):
    response = client.get("/users/me")
    assert response.status_code in (401, 403)  # HTTPBearer returns 403 if header missing entirely


def test_protected_route_works_with_valid_token(client):
    register_user(client, email="frank@test.com", password="pass123", role="admin")
    token = login(client, "frank@test.com", "pass123")
    response = client.get("/users/me", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["email"] == "frank@test.com"