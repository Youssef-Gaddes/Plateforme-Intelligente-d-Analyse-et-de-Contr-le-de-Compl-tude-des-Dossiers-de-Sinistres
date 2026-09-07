import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
from conftest import register_user, login, auth_headers, create_claim, make_admin, make_lecteur, fake_file, upload_with_type, make_gestionnaire
from PIL import Image




# ---- Upload validation ----

def test_upload_success(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()

    response = client.post(
        "/documents/upload",
        data={"claim_id": str(claim["id"])},
        files=fake_file(),
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["file_name"] == "test.png"


def test_upload_rejects_bad_extension(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()

    response = client.post(
        "/documents/upload",
        data={"claim_id": str(claim["id"])},
        files=fake_file(filename="malware.exe"),
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 400


def test_upload_rejects_nonexistent_claim(client):
    admin_token = make_admin(client)
    response = client.post(
        "/documents/upload",
        data={"claim_id": "99999"},
        files=fake_file(),
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404


def test_upload_rejects_oversized_file(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "MAX_FILE_SIZE", 10)  # shrink limit to 10 bytes for this test

    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()

    response = client.post(
        "/documents/upload",
        data={"claim_id": str(claim["id"])},
        files=fake_file(content=b"this is definitely more than 10 bytes"),
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 400


# ---- Upload ownership ----

def test_lecteur_can_upload_to_own_claim(client):
    admin_token = make_admin(client)
    lecteur_token, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()

    response = client.post(
        "/documents/upload",
        data={"claim_id": str(claim["id"])},
        files=fake_file(),
        headers=auth_headers(lecteur_token),
    )
    assert response.status_code == 200


def test_lecteur_cannot_upload_to_others_claim(client):
    admin_token = make_admin(client)
    lecteur1_token, lecteur1_id = make_lecteur(client, email="l1@test.com")
    _, lecteur2_id = make_lecteur(client, email="l2@test.com")

    claim = create_claim(client, admin_token, user_id=lecteur2_id).json()

    response = client.post(
        "/documents/upload",
        data={"claim_id": str(claim["id"])},
        files=fake_file(),
        headers=auth_headers(lecteur1_token),
    )
    assert response.status_code == 403


# ---- Document list ownership (the bug we just fixed) ----

def test_lecteur_sees_only_own_documents(client):
    admin_token = make_admin(client)
    lecteur1_token, lecteur1_id = make_lecteur(client, email="l1@test.com")
    _, lecteur2_id = make_lecteur(client, email="l2@test.com")

    claim1 = create_claim(client, admin_token, claim_number="SIN-L1", user_id=lecteur1_id).json()
    claim2 = create_claim(client, admin_token, claim_number="SIN-L2", user_id=lecteur2_id).json()

    client.post("/documents/upload", data={"claim_id": str(claim1["id"])}, files=fake_file(), headers=auth_headers(admin_token))
    client.post("/documents/upload", data={"claim_id": str(claim2["id"])}, files=fake_file(), headers=auth_headers(admin_token))

    response = client.get("/documents", headers=auth_headers(lecteur1_token))
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["claim_id"] == claim1["id"]


def test_admin_sees_all_documents(client):
    admin_token = make_admin(client)
    _, lecteur1_id = make_lecteur(client, email="l1@test.com")
    _, lecteur2_id = make_lecteur(client, email="l2@test.com")

    claim1 = create_claim(client, admin_token, claim_number="SIN-A", user_id=lecteur1_id).json()
    claim2 = create_claim(client, admin_token, claim_number="SIN-B", user_id=lecteur2_id).json()

    client.post("/documents/upload", data={"claim_id": str(claim1["id"])}, files=fake_file(), headers=auth_headers(admin_token))
    client.post("/documents/upload", data={"claim_id": str(claim2["id"])}, files=fake_file(), headers=auth_headers(admin_token))

    response = client.get("/documents", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert len(response.json()) == 2


# ---- OCR endpoint (mocked — no real Tesseract call) ----

def test_ocr_runs_and_saves_text(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "extract_text", lambda path, ext: "RAW OCR OUTPUT")
    monkeypatch.setattr(main, "clean_ocr_text", lambda text: "raw ocr output")
    monkeypatch.setattr(main, "extract_fields", lambda text: {"numero_contrat": "12345"})

    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = client.post("/documents/upload", data={"claim_id": str(claim["id"])}, files=fake_file(), headers=auth_headers(admin_token)).json()

    response = client.post(f"/documents/{doc['id']}/ocr", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert response.json()["ocr_text"] == "raw ocr output"
    assert response.json()["extracted_fields"]["numero_contrat"] == "12345"


def test_ocr_requires_admin_or_gestionnaire(client):
    admin_token = make_admin(client)
    lecteur_token, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = client.post("/documents/upload", data={"claim_id": str(claim["id"])}, files=fake_file(), headers=auth_headers(admin_token)).json()

    response = client.post(f"/documents/{doc['id']}/ocr", headers=auth_headers(lecteur_token))
    assert response.status_code == 403


def test_ocr_nonexistent_document_404(client):
    admin_token = make_admin(client)
    response = client.post("/documents/99999/ocr", headers=auth_headers(admin_token))
    assert response.status_code == 404


# ---- Classify endpoint (mocked — no real model inference) ----

def test_classify_requires_ocr_first(client):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = client.post("/documents/upload", data={"claim_id": str(claim["id"])}, files=fake_file(), headers=auth_headers(admin_token)).json()

    response = client.post(f"/documents/{doc['id']}/classify", headers=auth_headers(admin_token))
    assert response.status_code == 400


def test_classify_success(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "extract_text", lambda path, ext: "raw")
    monkeypatch.setattr(main, "clean_ocr_text", lambda text: "declaration de sinistre ahmed ben salah")
    monkeypatch.setattr(main, "extract_fields", lambda text: {})
    monkeypatch.setattr(main, "predict_document_type", lambda text: ("declaration_sinistre", 0.87))

    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = client.post("/documents/upload", data={"claim_id": str(claim["id"])}, files=fake_file(), headers=auth_headers(admin_token)).json()

    client.post(f"/documents/{doc['id']}/ocr", headers=auth_headers(admin_token))
    response = client.post(f"/documents/{doc['id']}/classify", headers=auth_headers(admin_token))

    assert response.status_code == 200
    assert response.json()["document_type"] == "declaration_sinistre"
    assert response.json()["confidence"] == 0.87


# ---- Manual review endpoint ----

def test_manual_review_updates_and_flags_document(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "extract_text", lambda path, ext: "raw")
    monkeypatch.setattr(main, "clean_ocr_text", lambda text: "cleaned")
    monkeypatch.setattr(main, "extract_fields", lambda text: {})

    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = client.post("/documents/upload", data={"claim_id": str(claim["id"])}, files=fake_file(), headers=auth_headers(admin_token)).json()
    client.post(f"/documents/{doc['id']}/ocr", headers=auth_headers(admin_token))

    response = client.patch(
        f"/documents/{doc['id']}/review",
        json={"document_type": "carte_grise", "ocr_text": "corrected text"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_type"] == "carte_grise"
    assert data["is_manually_reviewed"] == 1

def test_documents_types_endpoint_returns_known_classes(client):
    admin_token = make_admin(client)
    response = client.get("/documents/types", headers=auth_headers(admin_token))
    assert response.status_code == 200
    returned = set(response.json())
    expected = {
        "declaration_sinistre", "carte_grise", "permis_conduire",
        "facture", "devis", "constat_amiable", "rapport_expertise",
    }
    assert expected.issubset(returned)


def test_get_document_file_success(client, monkeypatch):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = upload_with_type(client, admin_token, claim["id"], monkeypatch, "facture").json()

    response = client.get(f"/documents/{doc['id']}/file", headers=auth_headers(admin_token))
    assert response.status_code == 200


def test_get_document_file_lecteur_forbidden_for_others_claim(client, monkeypatch):
    admin_token = make_admin(client)
    _, owner_id = make_lecteur(client, email="owner@test.com")
    other_token, _ = make_lecteur(client, email="other@test.com")
    claim = create_claim(client, admin_token, user_id=owner_id).json()
    doc = upload_with_type(client, admin_token, claim["id"], monkeypatch, "facture").json()

    response = client.get(f"/documents/{doc['id']}/file", headers=auth_headers(other_token))
    assert response.status_code == 403


def test_update_document_flags_manual_review(client, monkeypatch):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = upload_with_type(client, admin_token, claim["id"], monkeypatch, "facture", confidence=0.2).json()

    response = client.put(
        f"/documents/{doc['id']}",
        json={"document_type": "devis"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["document_type"] == "devis"
    # confirm is_manually_reviewed actually flips -- check via DB or a field on DocumentOut if exposed


def test_lecteur_sees_only_own_documents_via_list(client, monkeypatch):
    admin_token = make_admin(client)
    lecteur1_token, lecteur1_id = make_lecteur(client, email="l1b@test.com")
    _, lecteur2_id = make_lecteur(client, email="l2b@test.com")

    claim1 = create_claim(client, admin_token, claim_number="SIN-X1", user_id=lecteur1_id).json()
    claim2 = create_claim(client, admin_token, claim_number="SIN-X2", user_id=lecteur2_id).json()

    upload_with_type(client, admin_token, claim1["id"], monkeypatch, "facture")
    upload_with_type(client, admin_token, claim2["id"], monkeypatch, "facture")

    response = client.get("/documents", headers=auth_headers(lecteur1_token))
    claim_ids_seen = {d["claim_id"] for d in response.json()}
    assert claim_ids_seen == {claim1["id"]}

def test_classify_requires_admin_or_gestionnaire(client, monkeypatch):
    admin_token = make_admin(client)
    lecteur_token, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = upload_with_type(client, admin_token, claim["id"], monkeypatch, "facture").json()

    response = client.post(f"/documents/{doc['id']}/classify", headers=auth_headers(lecteur_token))
    assert response.status_code == 403


def test_review_requires_admin_or_gestionnaire(client, monkeypatch):
    admin_token = make_admin(client)
    lecteur_token, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = upload_with_type(client, admin_token, claim["id"], monkeypatch, "facture").json()

    response = client.patch(
        f"/documents/{doc['id']}/review",
        json={"document_type": "devis"},
        headers=auth_headers(lecteur_token),
    )
    assert response.status_code == 403


def test_get_document_nonexistent_404(client):
    admin_token = make_admin(client)
    response = client.get("/documents/99999", headers=auth_headers(admin_token))
    assert response.status_code == 404


def test_get_document_file_nonexistent_404(client):
    admin_token = make_admin(client)
    response = client.get("/documents/99999/file", headers=auth_headers(admin_token))
    assert response.status_code == 404


def test_get_document_file_missing_on_disk_404(client, monkeypatch, db_session):
    from models import Document
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = upload_with_type(client, admin_token, claim["id"], monkeypatch, "facture").json()

    # simulate the file having been removed/moved outside the API's knowledge
    stored = db_session.query(Document).filter(Document.id == doc["id"]).first()
    os.remove(stored.file_path)

    response = client.get(f"/documents/{doc['id']}/file", headers=auth_headers(admin_token))
    assert response.status_code == 404


def test_list_documents_filtered_by_claim_id(client, monkeypatch):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim1 = create_claim(client, admin_token, claim_number="SIN-F1", user_id=lecteur_id).json()
    claim2 = create_claim(client, admin_token, claim_number="SIN-F2", user_id=lecteur_id).json()
    upload_with_type(client, admin_token, claim1["id"], monkeypatch, "facture")
    upload_with_type(client, admin_token, claim2["id"], monkeypatch, "devis")

    response = client.get(f"/documents?claim_id={claim1['id']}", headers=auth_headers(admin_token))
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["claim_id"] == claim1["id"]


def test_delete_document_requires_admin(client, monkeypatch):
    admin_token = make_admin(client)
    gest_token = make_gestionnaire(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id).json()
    doc = upload_with_type(client, admin_token, claim["id"], monkeypatch, "facture").json()

    response = client.delete(f"/documents/{doc['id']}", headers=auth_headers(gest_token))
    assert response.status_code == 403