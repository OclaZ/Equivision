import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch
import io
import os
import sys

sys.path.append('/') 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set mode so routers are included
os.environ["ML_MODE"] = "FULL" 

import ML_DL.DL.MODELS.inference
import ML_DL.ML.MODELS.inference

# Mock the actual classes before importing main
class FakeBreed:
    def predict(self, file): return {"breed_classification": {"breed": "Arabian", "confidence": 0.99}, "combined_confidence": 0.99}
    def visualize_prediction(self, file): return io.BytesIO(b"dummy")

class FakePrice:
    def predict(self, *args, **kwargs): return {"estimated_price": 5000, "currency": "MAD", "models": {}}

ML_DL.DL.MODELS.inference.BreedClassifierService = FakeBreed
ML_DL.ML.MODELS.inference.PricingService = FakePrice

from main import app
from routes.auth import router as auth_router
from routes.listings import router as listings_router
from routes.predictions import router as predictions_router

routers = [r.path for r in app.routes]
if "/auth/register" not in routers and not any(r.path.startswith("/auth") for r in app.routes):
    app.include_router(auth_router)
    app.include_router(listings_router)
    app.include_router(predictions_router)

from database.database import get_db
from models.database import Base

from sqlalchemy.pool import StaticPool

# Setup SQLite In-Memory DB for Testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Mock the ML services at the module level
mock_breed_service = MagicMock()
mock_breed_service.predict.return_value = {
    "breed_classification": {"breed": "Arabian", "confidence": 0.99},
    "combined_confidence": 0.99
}
mock_breed_service.visualize_prediction.return_value = io.BytesIO(b"dummy_image")

mock_pricing_service = MagicMock()
mock_pricing_service.predict.return_value = {
    "estimated_price": 5000, "currency": "MAD", "models": {}
}

@pytest.fixture(autouse=True)
def mock_services():
    from main import app
    import main
    main.breed_service = mock_breed_service
    main.pricing_service = mock_pricing_service
    yield
    
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(autouse=True)
def wipe_db():
    # Clean up tables between tests to ensure isolation
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

client = TestClient(app)

@pytest.fixture
def auth_token():
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@test.com",
        "password": "password",
        "role": "user"
    })
    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "password"
    })
    return response.json()["access_token"]


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200

# ================= AUTH ENDPOINTS =================
def test_register():
    resp = client.post("/auth/register", json={
        "username": "newuser",
        "email": "newuser@test.com",
        "password": "password123",
        "role": "user"  
    })
    assert resp.status_code == 200
    assert resp.json()["email"] == "newuser@test.com"

def test_login_and_me(auth_token):
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@test.com"

# ================= LISTING ENDPOINTS =================
def test_get_listings_and_specific_listing(auth_token):
    # Insert a dummy listing via db session directly
    from models.database import HorseListing
    db = TestingSessionLocal()
    dummy = HorseListing(
        title="Stunning Arabian",
        external_id="ext-dummy-01",
        url="http://dummy.url",
        price=10000,
        breed="Arabian",
        gender="Mare",
        is_active=True
    )
    db.add(dummy)
    db.commit()
    db.refresh(dummy)
    listing_id = dummy.id
    db.close()
    
    get_resp = client.get(f"/listings/{listing_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Stunning Arabian"
    
    list_resp = client.get("/listings/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

# ================= ML PREDICT ENDPOINTS (MOCKED) =================
def test_predict_price():
    resp = client.post("/predict/price", json={
        "breed": "Arabian",
        "gender": "Mare",
        "age": 5,
        "height": 155
    })
    assert resp.status_code == 200
    assert "estimated_price" in resp.json()

def test_predict_breed():
    # Send a dummy image file
    file = {'file': ('dummy.jpg', b'dummy_content', 'image/jpeg')}
    resp = client.post("/predict/breed", files=file)
    assert resp.status_code == 200
    assert "breed_classification" in resp.json()

def test_predict_complete():
    file = {'file': ('dummy.jpg', b'dummy_content', 'image/jpeg')}
    data = {'gender': 'Mare', 'age': '5', 'height': '155'}
    resp = client.post("/predict/complete", files=file, data=data)
    assert resp.status_code == 200
    assert "breed_classification" in resp.json()
    assert "price_estimation" in resp.json()

def test_predict_breed_visualize():
    file = {'file': ('dummy.jpg', b'dummy_content', 'image/jpeg')}
    resp = client.post("/predict/breed/visualize", files=file)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"

# ================= PREDICTION HISTORY ENDPOINTS =================
def test_save_and_get_prediction(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    create_resp = client.post("/predictions/", headers=headers, json={
        "predicted_breed": "Arabian",
        "breed_confidence": 0.95,
        "estimated_price": 5000.0,
        "price_min": 4000.0,
        "price_max": 6000.0,
        "input_breed": "Arabian",
        "input_gender": "Mare",
        "input_age": 5,
        "image_url": "dummy.jpg"
    })
    assert create_resp.status_code == 200
    pred_id = create_resp.json()["id"]
    
    me_resp = client.get("/predictions/", headers=headers)
    assert me_resp.status_code == 200
    assert len(me_resp.json()) == 1
    assert me_resp.json()[0]["predicted_breed"] == "Arabian"

