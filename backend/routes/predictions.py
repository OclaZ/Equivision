from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
from core.auth import get_current_active_user
from models.database import User, Prediction

router = APIRouter(prefix="/predictions", tags=["predictions"])

from schemas.predictions import PredictionCreate, PredictionResponse

@router.post("/", response_model=PredictionResponse)
def save_prediction(
    prediction: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Save a new prediction to the user's history"""
    db_prediction = Prediction(
        user_id=current_user.id,
        predicted_breed=prediction.predicted_breed,
        breed_confidence=prediction.breed_confidence,
        estimated_price=prediction.estimated_price,
        price_min=prediction.price_min,
        price_max=prediction.price_max,
        input_breed=prediction.input_breed,
        input_gender=prediction.input_gender,
        input_age=prediction.input_age,
        image_url=prediction.image_url
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction

@router.get("/", response_model=List[PredictionResponse])
def get_user_predictions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get prediction history for the current user"""
    predictions = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).order_by(Prediction.created_at.desc()).offset(skip).limit(limit).all()
    
    return predictions

@router.get("/{prediction_id}", response_model=PredictionResponse)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific prediction by ID"""
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == current_user.id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    return prediction
