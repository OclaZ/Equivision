from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PriceEstimateRequest(BaseModel):
    breed: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None # New feature

class PredictionCreate(BaseModel):
    predicted_breed: Optional[str] = None
    breed_confidence: Optional[float] = None
    estimated_price: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    input_breed: Optional[str] = None
    input_gender: Optional[str] = None
    input_age: Optional[int] = None
    image_url: Optional[str] = None

class PredictionResponse(PredictionCreate):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
