from sqlalchemy import Column, Integer, Float, String, JSON
from app.models.base import Base

class FinancialAssessment(Base):
    __tablename__ = "financial_assessments"

    id = Column(Integer, primary_key=True, index=True)
    # Storing the raw input request and final response payload in JSON for record keeping.
    # Adhering to the rule of keeping business logic out of SQLAlchemy models.
    request_payload = Column(JSON, nullable=False)
    response_payload = Column(JSON, nullable=False)
    status = Column(String, default="completed")
