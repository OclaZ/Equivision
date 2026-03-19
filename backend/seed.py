import os
import sys

# Ensure backend root is in PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from database.database import SessionLocal, init_db, engine
from models.database import User, Prediction, HorseListing, Base
from core.auth import get_password_hash
from datetime import datetime, timedelta

def verify_tables():
    """Ensure tables exist before seeding"""
    print("Initializing schemas...")
    init_db()

def seed_data():
    session = SessionLocal()
    
    try:
        # Check if already seeded
        if session.query(User).first():
            print("Database already contains data. Wiping for fresh seed...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
        
        print("Seeding Users...")
        admin = User(
            email="admin@equivision.io",
            username="admin",
            hashed_password=get_password_hash("password123"),
            is_verified=True
        )
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("testpass"),
            is_verified=True
        )
        session.add(admin)
        session.add(test_user)
        session.commit()
        
        print("Seeding Horse Listings...")
        listings = [
            HorseListing(
                source="avito",
                external_id="avito_1001",
                url="https://avito.ma/dummy-1",
                title="Beautiful Arabian Horse for Sale",
                price=55000.0,
                location="Marrakech",
                image_url="https://images.pexels.com/photos/1996333/pexels-photo-1996333.jpeg",
                breed="Arabian",
                gender="Stallion",
                age=5,
                scraped_at=datetime.utcnow() - timedelta(days=2)
            ),
            HorseListing(
                source="avito",
                external_id="avito_1002",
                url="https://avito.ma/dummy-2",
                title="Strong Barb Horse, trained",
                price=32000.0,
                location="Fes",
                image_url="https://images.pexels.com/photos/2034731/pexels-photo-2034731.jpeg",
                breed="Barb",
                gender="Mare",
                age=8,
                scraped_at=datetime.utcnow() - timedelta(hours=10)
            ),
            HorseListing(
                source="cheval_maroc",
                external_id="cm_505",
                url="https://cheval.ma/dummy",
                title="Anglo-Arab jumping horse",
                price=120000.0,
                location="Rabat",
                image_url="https://images.pexels.com/photos/1109159/pexels-photo-1109159.jpeg",
                breed="Anglo-Arab",
                gender="Gelding",
                age=6,
                scraped_at=datetime.utcnow() - timedelta(minutes=45)
            ),
            HorseListing(
                source="avito",
                external_id="avito_1003",
                url="https://avito.ma/dummy-3",
                title="Quarter Horse - Western Riding",
                price=45000.0,
                location="Casablanca",
                image_url="https://images.pexels.com/photos/59231/horse-equestrian-sport-winter-snow-59231.jpeg",
                breed="Quarter Horse",
                gender="Mare",
                age=4,
                scraped_at=datetime.utcnow() - timedelta(days=5)
            )
        ]
        session.add_all(listings)
        session.commit()
        
        print("Seeding Predictions...")
        predictions = [
            Prediction(
                user_id=admin.id,
                predicted_breed="Arabian",
                breed_confidence=0.94,
                estimated_price=52000.0,
                price_min=48000.0,
                price_max=58000.0,
                input_breed="Arabian",
                input_gender="Stallion",
                input_age=5,
                image_url="https://images.pexels.com/photos/1996333/pexels-photo-1996333.jpeg"
            ),
            Prediction(
                user_id=test_user.id,
                predicted_breed="Barb",
                breed_confidence=0.88,
                estimated_price=31000.0,
                price_min=28000.0,
                price_max=35000.0,
                input_breed="Barb",
                input_gender="Mare",
                input_age=7,
                image_url="https://images.pexels.com/photos/2034731/pexels-photo-2034731.jpeg"
            )
        ]
        session.add_all(predictions)
        session.commit()
        
        print(f"Successfully seeded:")
        print(f"- 2 Users")
        print(f"- 4 Horse Listings")
        print(f"- 2 Predictions")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    verify_tables()
    seed_data()
