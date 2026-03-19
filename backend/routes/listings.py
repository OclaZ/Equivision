from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from database.database import get_db
from models.database import HorseListing

router = APIRouter(prefix="/listings", tags=["listings"])

from schemas.listings import HorseListingResponse

@router.get("/", response_model=List[HorseListingResponse])
def get_horse_listings(
    skip: int = 0,
    limit: int = 20,
    breed: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get active horse listings with optional filtering"""
    query = db.query(HorseListing).filter(HorseListing.is_active == True)
    
    if breed:
        query = query.filter(HorseListing.breed.ilike(f"%{breed}%"))
    if min_price is not None:
        query = query.filter(HorseListing.price >= min_price)
    if max_price is not None:
        query = query.filter(HorseListing.price <= max_price)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(or_(
            HorseListing.title.ilike(search_filter),
            HorseListing.location.ilike(search_filter)
        ))
        
    listings = query.order_by(HorseListing.scraped_at.desc()).offset(skip).limit(limit).all()
    return listings

@router.get("/{listing_id}", response_model=HorseListingResponse)
def get_horse_listing(listing_id: int, db: Session = Depends(get_db)):
    """Get a specific horse listing by ID"""
    listing = db.query(HorseListing).filter(HorseListing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    return listing
