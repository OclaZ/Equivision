

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
import logging
import os

# Commented out due to Windows numpy DLL issue
from app.ml.vision.inference import BreedClassifierService
try:
    from app.ml.pricing.inference import PricingService
except ImportError:
    PricingService = None # Will crash later if used, but handled by ML_MODE check

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

breed_service = None
pricing_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Determine mode
    ml_mode = os.getenv("ML_MODE", "FULL")
    
    # Startup: Initialize Database (only in FULL mode)
    global breed_service, pricing_service
    
    if ml_mode == "FULL":
        # Try to initialize database (optional)
        try:
            from app.core.database import init_db
            logger.info("Initializing Database...")
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed (continuing without DB): {e}")
    else:
        logger.info(f"Skipping Database initialization in {ml_mode} mode")
    

    # Initialize ML Services
    try:
        ml_mode = os.getenv("ML_MODE", "FULL")
        logger.info(f"Initializing ML Services (Mode: {ml_mode})...")
        
        # 1. Vision Service (Breed Classifier)
        if ml_mode in ["FULL", "VISION_ONLY"]:
            # Breed Classifier with auto-proxy logic
            breed_service = BreedClassifierService()
            logger.info("Breed Classifier service initialized (Local/Remote)")
        else:
            breed_service = None

        # 2. Pricing Service
        if ml_mode in ["FULL", "PRICING_ONLY"]:
            try:
                pricing_service = PricingService()
                logger.info("Pricing Service loaded successfully") 
            except Exception as e:
                logger.warning(f"Pricing Service failed to load: {e}")
                pricing_service = None
        else:
             pricing_service = None
             
        logger.info("ML Services initialization complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize ML Services: {e}")
        import traceback
        traceback.print_exc()
    
    yield
    # Shutdown: Clean up checks if needed
    logger.info("Shutting down...")

app = FastAPI(title="EquiVision API", lifespan=lifespan)

# Request models
class PriceEstimateRequest(BaseModel):
    breed: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None # New feature

# Include routers conditionally
ml_mode = os.getenv("ML_MODE", "FULL")
if ml_mode == "FULL":
    from app.api.auth import router as auth_router
    app.include_router(auth_router)


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

from fastapi.responses import StreamingResponse

@app.post("/predict/breed/visualize")
async def visualize_breed(file: UploadFile = File(...)):
    if not breed_service:
        raise HTTPException(status_code=503, detail="Breed Classification Service not available")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Get processed image stream
        img_stream = breed_service.visualize_prediction(file.file)
        return StreamingResponse(img_stream, media_type="image/jpeg")
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/price")
async def predict_price(request: PriceEstimateRequest):
    if not pricing_service:
        raise HTTPException(status_code=503, detail="Pricing Service not available")
    
    try:
        result = pricing_service.predict(
            breed=request.breed,
            gender=request.gender,
            age=request.age,
            height=request.height
        )
        return result
    except Exception as e:
        logger.error(f"Price prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/complete")
async def predict_complete(file: UploadFile = File(...), gender: Optional[str] = None, age: Optional[int] = None, height: Optional[int] = None):
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
            age=age,
            height=height
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
