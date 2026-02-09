
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
import logging

from app.ml.vision.inference import BreedClassifierService
from app.ml.pricing.inference import PricingService
from app.core.database import init_db
from app.api.auth import router as auth_router

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

breed_service = None
pricing_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database and Load ML Models
    global breed_service, pricing_service
    try:
        logger.info("Initializing Database...")
        init_db()
        logger.info("Database initialized successfully")
        
        logger.info("Initializing ML Services...")
        breed_service = BreedClassifierService()
        pricing_service = PricingService()
        logger.info("All ML Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
    yield
    # Shutdown: Clean up checks if needed
    logger.info("Shutting down...")

app = FastAPI(title="EquiVision API", lifespan=lifespan)

# Include routers
app.include_router(auth_router)

# Request models
class PriceEstimateRequest(BaseModel):
    breed: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None

@app.get("/")
def read_root():
    return {"message": "Welcome to EquiVision API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict/breed")
async def predict_breed(file: UploadFile = File(...)):
    if not breed_service:
        raise HTTPException(status_code=503, detail="Breed Classification Service not available")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        # Fallback: check filename extension if content_type is missing/generic
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Pass file-like object directly to PIL in service
        result = breed_service.predict(file.file)
        return result
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/price")
async def predict_price(request: PriceEstimateRequest):
    if not pricing_service:
        raise HTTPException(status_code=503, detail="Pricing Service not available")
    
    try:
        result = pricing_service.predict(
            breed=request.breed,
            gender=request.gender,
            age=request.age
        )
        return result
    except Exception as e:
        logger.error(f"Price prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/complete")
async def predict_complete(file: UploadFile = File(...), gender: Optional[str] = None, age: Optional[int] = None):
    """
    Combined endpoint: Upload horse image and get both breed classification and price estimate.
    """
    if not breed_service or not pricing_service:
        raise HTTPException(status_code=503, detail="ML Services not available")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Step 1: Predict breed from image
        breed_result = breed_service.predict(file.file)
        detected_breed = breed_result.get('breed', 'unknown')
        
        # Step 2: Estimate price using detected breed
        price_result = pricing_service.predict(
            breed=detected_breed.lower(),
            gender=gender,
            age=age
        )
        
        # Step 3: Combine results
        return {
            "breed_classification": breed_result,
            "price_estimation": price_result,
            "combined_confidence": breed_result.get('confidence', 0) * 0.7  # Weighted confidence
        }
    except Exception as e:
        logger.error(f"Combined prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
