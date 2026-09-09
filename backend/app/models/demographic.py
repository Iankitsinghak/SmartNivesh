from sqlalchemy import Column, Integer, String, Float, Enum
from app.models.base import Base
from app.core.enums import Provenance

class DemographicRecord(Base):
    __tablename__ = "demographics"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(String, index=True, nullable=False)
    indicator = Column(String, index=True, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    geographic_scope = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    dataset_date = Column(String, nullable=False)
    provenance = Column(Enum(Provenance), nullable=False)
