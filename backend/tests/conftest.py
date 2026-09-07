import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import io
from PIL import Image

from main import app, get_db
from database import Base
from models import User, Claim, Document

TEST_DATABASE_URL = "postgresql://claims_user:devpass@localhost:5432/claims_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all tables once at the start of the test session, drop them when done."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Fresh session per test. Wipes data after each test for isolation."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # delete in FK-safe order: documents -> claims -> users
        session.query(Document).delete()
        session.query(Claim).delete()
        session.query(User).delete()
        session.commit()
        session.close()


@pytest.fixture()
def client(db_session):
    """TestClient with the real DB dependency swapped for the test session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---- Helper functions used across test files ----

def register_user(client, name="Test User", email="test@example.com", password="testpass123", role="lecteur"):
    return client.post("/auth/register", json={
        "name": name, "email": email, "password": password, "role": role
    })


def login(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def create_claim(client, token, claim_number="SIN-TEST-001", insured_name="Test Insured",
                  status="ouvert", claim_type="auto", user_id=None):
    return client.post("/claims", json={
        "claim_number": claim_number,
        "insured_name": insured_name,
        "status": status,
        "claim_type": claim_type,
        "user_id": user_id,
    }, headers=auth_headers(token))

def make_admin(client):
    register_user(client, email="admin@test.com", password="pass123", role="admin")
    return login(client, "admin@test.com", "pass123")


def make_gestionnaire(client):
    register_user(client, email="gest@test.com", password="pass123", role="gestionnaire")
    return login(client, "gest@test.com", "pass123")


def make_lecteur(client, email="lecteur1@test.com"):
    resp = register_user(client, email=email, password="pass123", role="lecteur")
    user_id = resp.json()["id"]
    token = login(client, email, "pass123")
    return token, user_id


def fake_file(filename="test.png", content=None):
    if content is not None:
        buf = io.BytesIO(content)
    else:
        img = Image.new("RGB", (20, 20), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
    buf.seek(0)
    return {"file": (filename, buf, "image/png")}


def upload_with_type(client, token, claim_id, monkeypatch, doc_type, confidence=0.9):
    import main
    monkeypatch.setattr(main, "extract_text", lambda path, ext: "raw")
    monkeypatch.setattr(main, "clean_ocr_text", lambda text: "cleaned")
    monkeypatch.setattr(main, "predict_document_type", lambda text: (doc_type, confidence))
    return client.post(
        "/documents/upload",
        data={"claim_id": str(claim_id)},
        files=fake_file(),
        headers=auth_headers(token),
    )