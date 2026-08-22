import asyncio
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.company_service import company_data_service, CompanyDetailsResponse


def test_company_service_unit():
    print("\n--- Test Company Data Service Unit ---")
    res = asyncio.run(company_data_service.get_company_details("NVIDIA"))
    assert isinstance(res, CompanyDetailsResponse)
    assert res.company.name == "NVIDIA"
    print("[OK] CompanyDataService unit test passed.")


def test_companies_api_endpoints():
    print("\n--- Test Companies API Endpoints ---")
    client = TestClient(app)

    # Test /api/companies/NVIDIA
    resp = client.get("/api/companies/NVIDIA")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["company"]["name"] == "NVIDIA"
    assert "has_data" in data
    print("[OK] GET /api/companies/NVIDIA passed.")

    # Test /companies/Microsoft
    resp2 = client.get("/companies/Microsoft")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["company"]["name"] == "Microsoft"
    assert "has_data" in data2
    print("[OK] GET /companies/Microsoft passed.")

    # Test URL-encoded name like TSMC or OpenAI
    resp3 = client.get("/api/companies/OpenAI")
    assert resp3.status_code == 200
    assert resp3.json()["company"]["name"] == "OpenAI"
    print("[OK] GET /api/companies/OpenAI passed.")


if __name__ == "__main__":
    test_company_service_unit()
    test_companies_api_endpoints()
    print("\n=== ALL COMPANY TESTS PASSED ===")
