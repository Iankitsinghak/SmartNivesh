from sqlalchemy import Column, String, Float, Enum
from app.models.base import Base
from app.core.enums import Provenance

class PlaceRecord(Base):
    __tablename__ = "places"

    place_id = Column(String, primary_key=True, index=True)
    category = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    source_id = Column(String, nullable=False)
    dataset_date = Column(String, nullable=False)
    provenance = Column(Enum(Provenance), nullable=False)