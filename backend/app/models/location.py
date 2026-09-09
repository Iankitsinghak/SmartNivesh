from sqlalchemy import Column, String, Float, JSON
from app.models.base import Base

class LocationRecord(Base):
    __tablename__ = "locations"

    location_id = Column(String, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    hierarchy = Column(JSON, nullable=False) # Store country, state, district, village_town
