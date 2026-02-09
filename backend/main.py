
from fastapi import FastAPI, UploadFile, File, HTTPException
from contextlib import asynccontextmanager
import logging

from app.ml.vision.inference import BreedClassifierService

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ml_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML Models
    global ml_service
    try:
        logger.info("Initializing ML Service...")
        ml_service = BreedClassifierService()
    except Exception as e:
        logger.error(f"Failed to initialize ML Service: {e}")
    yield
    # Shutdown: Clean up checks if needed
    logger.info("Shutting down...")

app = FastAPI(title="EquiVision API", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "Welcome to EquiVision API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict/breed")
async def predict_breed(file: UploadFile = File(...)):
    if not ml_service:
        raise HTTPException(status_code=503, detail="ML Service not available")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        # Fallback: check filename extension if content_type is missing/generic
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Pass file-like object directly to PIL in service
        result = ml_service.predict(file.file)
        return result
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
