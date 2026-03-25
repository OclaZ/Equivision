from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="user")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Breed prediction
    predicted_breed = Column(String, nullable=True)
    breed_confidence = Column(Float, nullable=True)
    
    # Price prediction
    estimated_price = Column(Float, nullable=True)
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    
    # Input features
    input_breed = Column(String, nullable=True)
    input_gender = Column(String, nullable=True)
    input_age = Column(Integer, nullable=True)
    input_height = Column(Float, nullable=True)
    
    # Analysis outputs
    warning = Column(String, nullable=True)
    detection_info = Column(String, nullable=True) # JSON store for bounding boxes, etc.
    
    # Metadata
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="predictions")

class HorseListing(Base):
    __tablename__ = "horse_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Scraped data
    source = Column(String, default="avito")  # avito, other sources
    external_id = Column(String, unique=True, index=True)
    url = Column(String)
    title = Column(String)
    price = Column(Float, nullable=True)
    location = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    
    # Extracted features
    breed = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    
    # Metadata
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
