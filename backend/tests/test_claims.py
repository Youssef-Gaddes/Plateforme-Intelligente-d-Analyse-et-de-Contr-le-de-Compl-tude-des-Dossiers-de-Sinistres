import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conftest import register_user, login, auth_headers, create_claim, make_admin, make_gestionnaire, make_lecteur




# ---- Creation & role guards ----

def test_admin_can_create_claim(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)

    response = create_claim(client, admin_token, user_id=lecteur_id)
    assert response.status_code == 200
    data = response.json()
    assert data["claim_number"] == "SIN-TEST-001"
    assert data["user_id"] == lecteur_id


def test_gestionnaire_can_create_claim(client):
    gest_token = make_gestionnaire(client)
    _, lecteur_id = make_lecteur(client)

    response = create_claim(client, gest_token, user_id=lecteur_id)
    assert response.status_code == 200


def test_lecteur_cannot_create_claim(client):
    lecteur_token, lecteur_id = make_lecteur(client)

    response = create_claim(client, lecteur_token, user_id=lecteur_id)
    assert response.status_code == 403


def test_create_claim_rejects_non_lecteur_owner(client):
    admin_token = make_admin(client)
    gest_token = make_gestionnaire(client)  # gestionnaire, not lecteur
    gest_id = login(client, "gest@test.com", "pass123")  # just to reuse; get actual id below

    # fetch gestionnaire's real id via /users/me
    me = client.get("/users/me", headers=auth_headers(gest_token)).json()

    response = create_claim(client, admin_token, user_id=me["id"])
    assert response.status_code == 400


def test_create_claim_rejects_nonexistent_user(client):
    admin_token = make_admin(client)
    response = create_claim(client, admin_token, user_id=99999)
    assert response.status_code == 404


def test_create_claim_rejects_duplicate_claim_number(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)

    create_claim(client, admin_token, claim_number="SIN-DUP-001", user_id=lecteur_id)
    response = create_claim(client, admin_token, claim_number="SIN-DUP-001", user_id=lecteur_id)
    assert response.status_code == 400


# ---- Ownership: the important part ----

def test_lecteur_sees_only_own_claims(client):
    admin_token = make_admin(client)
    lecteur1_token, lecteur1_id = make_lecteur(client, email="l1@test.com")
    lecteur2_token, lecteur2_id = make_lecteur(client, email="l2@test.com")

    create_claim(client, admin_token, claim_number="SIN-L1", user_id=lecteur1_id)
    create_claim(client, admin_token, claim_number="SIN-L2", user_id=lecteur2_id)

    response = client.get("/claims", headers=auth_headers(lecteur1_token))
    assert response.status_code == 200
    claims = response.json()
    assert len(claims) == 1
    assert claims[0]["claim_number"] == "SIN-L1"


def test_admin_sees_all_claims(client):
    admin_token = make_admin(client)
    _, lecteur1_id = make_lecteur(client, email="l1@test.com")
    _, lecteur2_id = make_lecteur(client, email="l2@test.com")

    create_claim(client, admin_token, claim_number="SIN-A", user_id=lecteur1_id)
    create_claim(client, admin_token, claim_number="SIN-B", user_id=lecteur2_id)

    response = client.get("/claims", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_lecteur_cannot_view_others_claim_detail(client):
    admin_token = make_admin(client)
    lecteur1_token, lecteur1_id = make_lecteur(client, email="l1@test.com")
    _, lecteur2_id = make_lecteur(client, email="l2@test.com")

    created = create_claim(client, admin_token, claim_number="SIN-OTHER", user_id=lecteur2_id)
    claim_id = created.json()["id"]

    response = client.get(f"/claims/{claim_id}", headers=auth_headers(lecteur1_token))
    assert response.status_code == 403


def test_lecteur_can_view_own_claim_detail(client):
    admin_token = make_admin(client)
    lecteur_token, lecteur_id = make_lecteur(client)

    created = create_claim(client, admin_token, user_id=lecteur_id)
    claim_id = created.json()["id"]

    response = client.get(f"/claims/{claim_id}", headers=auth_headers(lecteur_token))
    assert response.status_code == 200


def test_get_nonexistent_claim_returns_404(client):
    admin_token = make_admin(client)
    response = client.get("/claims/99999", headers=auth_headers(admin_token))
    assert response.status_code == 404


# ---- Update & delete guards ----

def test_lecteur_cannot_update_claim(client):
    admin_token = make_admin(client)
    lecteur_token, lecteur_id = make_lecteur(client)

    created = create_claim(client, admin_token, user_id=lecteur_id)
    claim_id = created.json()["id"]

    response = client.put(f"/claims/{claim_id}", json={
        "claim_number": "SIN-TEST-001", "insured_name": "Changed",
        "status": "ferme", "claim_type": "auto", "user_id": lecteur_id,
    }, headers=auth_headers(lecteur_token))
    assert response.status_code == 403


def test_only_admin_can_delete_claim(client):
    admin_token = make_admin(client)
    gest_token = make_gestionnaire(client)
    _, lecteur_id = make_lecteur(client)

    created = create_claim(client, admin_token, user_id=lecteur_id)
    claim_id = created.json()["id"]

    # gestionnaire tries to delete -> should fail
    response = client.delete(f"/claims/{claim_id}", headers=auth_headers(gest_token))
    assert response.status_code == 403

    # admin deletes -> should succeed
    response = client.delete(f"/claims/{claim_id}", headers=auth_headers(admin_token))
    assert response.status_code == 200


# ---- Filters ----

def test_filter_claims_by_status(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)

    create_claim(client, admin_token, claim_number="SIN-OPEN", status="ouvert", user_id=lecteur_id)
    create_claim(client, admin_token, claim_number="SIN-CLOSED", status="ferme", user_id=lecteur_id)

    response = client.get("/claims?status=ferme", headers=auth_headers(admin_token))
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["claim_number"] == "SIN-CLOSED"


def test_filter_claims_by_type(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)

    create_claim(client, admin_token, claim_number="SIN-AUTO", claim_type="auto", user_id=lecteur_id)
    create_claim(client, admin_token, claim_number="SIN-HABIT", claim_type="habitation", user_id=lecteur_id)

    response = client.get("/claims?claim_type=habitation", headers=auth_headers(admin_token))
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["claim_number"] == "SIN-HABIT"

def test_admin_can_update_claim_success(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()

    response = client.put(f"/claims/{claim['id']}", json={
        "claim_number": claim["claim_number"], "insured_name": "Updated Name",
        "status": "en_cours", "claim_type": "auto", "user_id": lecteur_id,
    }, headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert response.json()["insured_name"] == "Updated Name"
    assert response.json()["status"] == "en_cours"


def test_update_claim_rejects_duplicate_claim_number(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    create_claim(client, admin_token, claim_number="SIN-EXISTING", user_id=lecteur_id)
    claim2 = create_claim(client, admin_token, claim_number="SIN-OTHER", user_id=lecteur_id).json()

    response = client.put(f"/claims/{claim2['id']}", json={
        "claim_number": "SIN-EXISTING", "insured_name": "X",
        "status": "ouvert", "claim_type": "auto", "user_id": lecteur_id,
    }, headers=auth_headers(admin_token))
    assert response.status_code == 400


def test_update_claim_rejects_nonexistent_user(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()

    response = client.put(f"/claims/{claim['id']}", json={
        "claim_number": claim["claim_number"], "insured_name": "X",
        "status": "ouvert", "claim_type": "auto", "user_id": 99999,
    }, headers=auth_headers(admin_token))
    assert response.status_code == 404


def test_update_nonexistent_claim_404(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    response = client.put("/claims/99999", json={
        "claim_number": "X", "insured_name": "X",
        "status": "ouvert", "claim_type": "auto", "user_id": lecteur_id,
    }, headers=auth_headers(admin_token))
    assert response.status_code == 404


def test_delete_claim_cascades_to_documents(client, monkeypatch):
    from conftest import upload_with_type
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = upload_with_type(client, admin_token, claim["id"], monkeypatch, "facture").json()

    client.delete(f"/claims/{claim['id']}", headers=auth_headers(admin_token))

    response = client.get(f"/documents/{doc['id']}", headers=auth_headers(admin_token))
    assert response.status_code == 404  # cascaded away with the claim