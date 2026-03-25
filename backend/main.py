import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import Optional
import logging
import os
import uuid
import shutil
import json
from pathlib import Path

from ML_DL.DL.MODELS.inference import BreedClassifierService
try:
    from ML_DL.ML.MODELS.inference import PricingService
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
            from database.database import init_db
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

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files for Uploads
UPLOAD_DIR = Path("static/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

from database.database import get_db
from core.auth import get_current_active_user
from models.database import User, Prediction
from sqlalchemy.orm import Session

# Import schemas
from schemas.predictions import PriceEstimateRequest

# Include routers conditionally
ml_mode = os.getenv("ML_MODE", "FULL")
if ml_mode == "FULL":
    from routes.auth import router as auth_router
    from routes.listings import router as listings_router
    from routes.predictions import router as predictions_router
    
    app.include_router(auth_router)
    app.include_router(listings_router)
    app.include_router(predictions_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to EquiVision API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/metadata")
def get_metadata():
    """Return lists of supported breeds and genders"""
    breeds = []
    if breed_service and hasattr(breed_service, 'class_names'):
        # Capitalize and clean up names
        breeds = [b.replace('_', ' ').title() for b in breed_service.class_names]
    
    return {
        "breeds": breeds or ["Arabe", "Barbe", "Thoroughbred", "Quarter Horse"],
        "genders": ["Femelle (Mare)", "Mâle (Stallion)", "Hongre (Gelding)"],
        "price_ranges": ["0 - 5,000€", "5,000 - 20,000€", "20,000 - 50,000€", "50,000€+"]
    }

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
async def predict_complete(
    file: UploadFile = File(...), 
    gender: Optional[str] = Form(None), 
    age: Optional[int] = Form(None), 
    height: Optional[float] = Form(None),
    input_breed: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Combined endpoint: Upload horse image and get both breed classification and price estimate.
    Saves the result to the database for the current user.
    """
    if not breed_service or not pricing_service:
        raise HTTPException(status_code=503, detail="ML Services not available")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Step 1: Predict breed from image
        breed_result = breed_service.predict(file.file)
        logger.info(f"Breed Predictor Result: {breed_result}")
        
        # Robust Horse Detection Validation
        horse_not_detected = breed_result.get('horse_not_detected', False)
        
        # Additional checks if YOLO is unavailable or returned weird results
        if "error" in breed_result and "No horse detected" in breed_result["error"]:
             horse_not_detected = True
             
        detected_breed = breed_result.get('breed', 'unidentified')
        confidence = breed_result.get('confidence', 0)
        
        if detected_breed.lower() in ["unknown", "unidentified", "non identifié"]:
             horse_not_detected = True
             
        if horse_not_detected:
             detected_breed = "Non identifié"
             confidence = 0.0
        
        # Step 2: Estimate price
        # If no horse detected, user input breed takes precedence, or default
        effective_breed = input_breed if input_breed else detected_breed
        
        price_result = pricing_service.predict(
            breed=effective_breed.lower(),
            gender=gender,
            age=int(age) if age is not None else None,
            height=height
        )
        
        prediction_id = None
        created_at = None
        
        # Step 4: Save to Database ONLY IF HORSE DETECTED
        if not horse_not_detected:
            # Step 3: Save Image for Persistence
            file.file.seek(0)
            file_extension = Path(file.filename).suffix or ".jpg"
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                image_url = f"/static/uploads/{unique_filename}"
            except Exception as e:
                logger.error(f"Failed to save image: {e}")
                image_url = None

            db_prediction = Prediction(
                user_id=current_user.id,
                predicted_breed=detected_breed,
                breed_confidence=float(confidence),
                estimated_price=float(price_result.get('estimated_price', 0)),
                price_min=float(price_result.get('confidence_interval', {}).get('min', 0)),
                price_max=float(price_result.get('confidence_interval', {}).get('max', 0)),
                input_breed=effective_breed,
                input_gender=gender,
                input_age=age,
                input_height=height,
                image_url=image_url,
                warning=None,
                detection_info=json.dumps(breed_result.get('detection', {}))
            )
            db.add(db_prediction)
            db.commit()
            db.refresh(db_prediction)
            prediction_id = db_prediction.id
            created_at = db_prediction.created_at.isoformat() if db_prediction.created_at else None
        else:
            image_url = None # Don't save image if not a horse

        # Step 5: Return result (matching frontend interface)
        return {
            "id": prediction_id,
            "predicted_breed": "Pas un cheval" if horse_not_detected else detected_breed,
            "breed_confidence": 0.0 if horse_not_detected else confidence,
            "estimated_price": 0.0 if horse_not_detected else float(price_result.get('estimated_price', 0)),
            "price_min": 0.0 if horse_not_detected else float(price_result.get('confidence_interval', {}).get('min', 0)),
            "price_max": 0.0 if horse_not_detected else float(price_result.get('confidence_interval', {}).get('max', 0)),
            "age": age,
            "gender": gender,
            "height": height,
            "image_url": image_url,
            "created_at": created_at,
            "warning": "NOT_A_HORSE" if horse_not_detected else None,
            "detection": breed_result.get("detection")
        }
    except Exception as e:
        logger.error(f"Combined prediction error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
