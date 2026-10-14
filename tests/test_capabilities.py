from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)

REQUIRED_FIELDS = {
    "description",
    "practice_area",
    "skill_levels",
    "certifications",
    "industry_verticals",
    "capacity",
    "consultants",
}


def test_get_capabilities_returns_all_capabilities():
    response = client.get("/capabilities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Cloud Architecture" in data
    for name, details in data.items():
        assert REQUIRED_FIELDS <= details.keys(), f"{name} is missing fields"
        assert isinstance(details["consultants"], list)
        assert isinstance(details["capacity"], int)


def test_capability_filter_implementation():
    response = client.get("/capabilities", params={"practice_area": "Technology"})

    assert response.status_code == 200
    data = response.json()
    assert data
    assert all(c["practice_area"] == "Technology" for c in data.values())
    assert "Cloud Architecture" in data
    assert "Change Management" not in data


def test_capability_filter_is_case_insensitive_and_combinable():
    response = client.get(
        "/capabilities",
        params={"practice_area": "technology", "industry_vertical": "healthcare"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data
    for details in data.values():
        assert details["practice_area"] == "Technology"
        assert "Healthcare" in details["industry_verticals"]


def test_capability_filter_with_no_match_returns_empty():
    response = client.get("/capabilities", params={"practice_area": "Nonexistent"})

    assert response.status_code == 200
    assert response.json() == {}
