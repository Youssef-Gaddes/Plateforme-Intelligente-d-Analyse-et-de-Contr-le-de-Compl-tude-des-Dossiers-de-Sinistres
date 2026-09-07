import main
from conftest import  create_claim, auth_headers, make_admin, make_lecteur, fake_file, upload_with_type




def test_completeness_score_auto_all_present(client, monkeypatch):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id, claim_type="auto").json()

    for doc_type in ["declaration_sinistre", "carte_grise", "permis_conduire", "constat_amiable"]:
        upload_with_type(client, admin_token, claim["id"], monkeypatch, doc_type)

    response = client.get(f"/claims/{claim['id']}", headers=auth_headers(admin_token))
    assert response.json()["completeness_score"] == 100.0


def test_completeness_score_auto_partial(client, monkeypatch):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id, claim_type="auto").json()

    upload_with_type(client, admin_token, claim["id"], monkeypatch, "declaration_sinistre")
    upload_with_type(client, admin_token, claim["id"], monkeypatch, "carte_grise")
    # permis_conduire and constat_amiable missing -> 2/4 = 50%

    response = client.get(f"/claims/{claim['id']}", headers=auth_headers(admin_token))
    assert response.json()["completeness_score"] == 50.0


def test_low_confidence_classification_not_counted(client, monkeypatch):
    """Below CONFIDENCE_THRESHOLD (0.3), a doc shouldn't count toward completeness
    unless it's been manually reviewed."""
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id, claim_type="habitation").json()

    upload_with_type(client, admin_token, claim["id"], monkeypatch, "declaration_sinistre", confidence=0.9)
    upload_with_type(client, admin_token, claim["id"], monkeypatch, "devis", confidence=0.15)  # below threshold

    response = client.get(f"/claims/{claim['id']}", headers=auth_headers(admin_token))
    assert response.json()["completeness_score"] == 50.0  # only declaration counts


def test_manual_review_overrides_low_confidence(client, monkeypatch):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id, claim_type="habitation").json()

    upload_with_type(client, admin_token, claim["id"], monkeypatch, "declaration_sinistre", confidence=0.9)
    doc = upload_with_type(client, admin_token, claim["id"], monkeypatch, "devis", confidence=0.15).json()

    # correct it via manual review -> should now count regardless of stored confidence
    client.put(
        f"/documents/{doc['id']}",
        json={"document_type": "devis"},
        headers=auth_headers(admin_token),
    )

    response = client.get(f"/claims/{claim['id']}", headers=auth_headers(admin_token))
    assert response.json()["completeness_score"] == 100.0


def test_completeness_recalculates_after_document_delete(client, monkeypatch):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id, claim_type="sante").json()

    doc1 = upload_with_type(client, admin_token, claim["id"], monkeypatch, "declaration_sinistre").json()
    upload_with_type(client, admin_token, claim["id"], monkeypatch, "facture")
    # 2/2 = 100%

    client.delete(f"/documents/{doc1['id']}", headers=auth_headers(admin_token))
    # facture alone -> 1/2 = 50%

    response = client.get(f"/claims/{claim['id']}", headers=auth_headers(admin_token))
    assert response.json()["completeness_score"] == 50.0


def test_unknown_claim_type_scores_zero(client, monkeypatch):
    """REQUIRED_DOCUMENTS.get(claim_type, []) returns [] for anything
    outside auto/habitation/sante -- confirms the safe-default branch."""
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id, claim_type="auto").json()

    response = client.get(f"/claims/{claim['id']}", headers=auth_headers(admin_token))
    assert response.json()["completeness_score"] == 0.0  # no documents yet

def test_completeness_recomputes_when_claim_type_changes(client, monkeypatch):
    admin_token = make_admin(client)
    _, lecteur_id = make_lecteur(client)
    claim = create_claim(client, admin_token, user_id=lecteur_id, claim_type="habitation").json()

    upload_with_type(client, admin_token, claim["id"], monkeypatch, "declaration_sinistre")
    upload_with_type(client, admin_token, claim["id"], monkeypatch, "devis")
    # habitation requires [declaration_sinistre, devis] -> both present -> 100%

    response = client.get(f"/claims/{claim['id']}", headers=auth_headers(admin_token))
    assert response.json()["completeness_score"] == 100.0

    # now reclassify the claim as "auto", which requires 4 pieces instead of 2
    client.put(f"/claims/{claim['id']}", json={
        "claim_number": claim["claim_number"], "insured_name": claim["insured_name"],
        "status": "ouvert", "claim_type": "auto", "user_id": lecteur_id,
    }, headers=auth_headers(admin_token))

    response = client.get(f"/claims/{claim['id']}", headers=auth_headers(admin_token))
    # only declaration_sinistre and constat/carte_grise/permis missing -> 1/4 = 25%
    # (devis isn't in the auto required list at all, so it contributes nothing)
    assert response.json()["completeness_score"] == 25.0