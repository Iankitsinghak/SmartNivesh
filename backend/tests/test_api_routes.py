from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_financial_roadmap_route_is_exposed():
    response = client.post("/api/finance/roadmap", json={"margin_capital": 10_000})
    assert response.status_code == 200
    assert response.json()["assessment"]["project_cost"] == 100_000


def test_scheme_route_is_registered():
    response = client.post("/api/schemes/route", json={
        "project_cost": 100_000,
        "loan_requirement": 90_000,
        "financing_band": "MICRO_FINANCE",
        "actual_modeled_loan": 90_000,
        "financing_gap": 0,
    })
    assert response.status_code == 200
    assert response.json()["applicable"] is True


def test_local_demographics_route_works_without_public_api():
    response = client.post("/api/market/local-demographics", json={
        "state_name": "Uttar Pradesh",
        "district_name": "Saharanpur",
        "subdistrict_name": "Behat",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "AVAILABLE"
    assert body["total_population"] > 0
