from sqlalchemy import Column, Integer, Float, String, JSON
from app.models.base import Base

class SchemeRoutingRecord(Base):
    """
    SQLAlchemy model for storing historical scheme routing decisions.
    Follows the GOLD STATE architecture rule of models being for database representation only.
    """
    __tablename__ = "scheme_routing_records"

    id = Column(Integer, primary_key=True, index=True)
    # Storing the raw input request and final response payload in JSON
    request_payload = Column(JSON, nullable=False)
    response_payload = Column(JSON, nullable=False)
    status = Column(String, default="routed")
