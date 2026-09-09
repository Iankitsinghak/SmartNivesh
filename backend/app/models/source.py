from sqlalchemy import Column, String, Date, JSON
from app.models.base import Base

class SourceRecord(Base):
    __tablename__ = "sources"

    source_id = Column(String, primary_key=True, index=True)
    provider_name = Column(String, nullable=False)
    dataset_name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    access_method = Column(String, nullable=False)
    publication_date = Column(Date, nullable=False)
    geographic_coverage = Column(String, nullable=False)
    limitations = Column(JSON, nullable=False)  # list of strings
    update_frequency = Column(String, nullable=True)
    last_verified = Column(Date, nullable=True)