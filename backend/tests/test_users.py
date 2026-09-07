from conftest import make_admin, make_lecteur, auth_headers


def test_admin_can_create_user(client):
    admin_token = make_admin(client)
    response = client.post(
        "/users",
        json={"name": "New Gest", "email": "newgest@test.com", "password": "pass123", "role": "gestionnaire"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["role"] == "gestionnaire"


def test_non_admin_cannot_create_user(client):
    lecteur_token, _ = make_lecteur(client)
    response = client.post(
        "/users",
        json={"name": "X", "email": "x@test.com", "password": "pass123", "role": "lecteur"},
        headers=auth_headers(lecteur_token),
    )
    assert response.status_code == 403


def test_admin_can_update_user_email(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    response = client.put(
        f"/users/{lecteur_id}",
        json={"email": "updated@test.com"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["email"] == "updated@test.com"


def test_update_user_rejects_duplicate_email(client):
    admin_token = make_admin(client)
    _, l1_id = make_lecteur(client, email="dup1@test.com")
    _, l2_id = make_lecteur(client, email="dup2@test.com")
    response = client.put(
        f"/users/{l2_id}",
        json={"email": "dup1@test.com"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 400


def test_admin_can_delete_user(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    response = client.delete(f"/users/{lecteur_id}", headers=auth_headers(admin_token))
    assert response.status_code == 200


def test_list_users_filtered_by_role(client):
    admin_token = make_admin(client)
    make_lecteur(client, email="filterl@test.com")
    response = client.get("/users?role=lecteur", headers=auth_headers(admin_token))
    assert all(u["role"] == "lecteur" for u in response.json())