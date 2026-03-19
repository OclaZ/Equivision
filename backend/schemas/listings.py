from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HorseListingResponse(BaseModel):
    id: int
    source: str
    external_id: str
    url: str
    title: str
    price: Optional[float] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    scraped_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True
