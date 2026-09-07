from pydantic import BaseModel
from typing import Optional

class Demographics(BaseModel):
    location_id: str
    total_population: int
    male_population: int
    female_population: int
    age_0_6: Optional[int] = None
    age_7_17: Optional[int] = None
    age_18_24: Optional[int] = None
    age_25_44: Optional[int] = None
    age_45_59: Optional[int] = None
    age_60_plus: Optional[int] = None
    households: Optional[int] = None
    working_population: Optional[int] = None
    literacy_rate: Optional[float] = None
