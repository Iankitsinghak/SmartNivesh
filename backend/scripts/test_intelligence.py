import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.schemas.market import MarketAnalysisRequest
from app.services.market.market_engine import analyze_market

def main():
    print("Testing local intelligence engine with newly ingested data...")
    req = MarketAnalysisRequest(location_id="LOC-001", category_id="CAT-001", radius_km=10.0)
    try:
        res = analyze_market(req)
        print(f"Overall Score: {res.overall_score}")
        print(f"Competition Score: {res.competition.competition_score}")
        print(f"Business Density: {res.business_activity.business_density}")
        print(f"Demand Score: {res.demand.demand_score}")
        print("Intelligence engine successfully processed the request using database records!")
    except Exception as e:
        print(f"Failed to run intelligence engine: {e}")

if __name__ == "__main__":
    main()
