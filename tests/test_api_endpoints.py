import json
import uuid
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_farmer_registration_api(client):
    fid = f"TEST-REG-{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "name": "Ananya Sharma",
        "farmer_id": fid,
        "phone": "9988776655",
        "location": "Warangal",
        "crop": "Rice",
        "pin": "5432"
    }

    response = client.post(
        "/api/auth/register",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["authenticated"] is True
    assert data["farmer_id"] == fid
    assert data["farmer_name"] == "Ananya Sharma"

    # Now verify login with the registered farmer credentials
    login_resp = client.post(
        "/api/auth/login",
        data=json.dumps({"farmer_id": fid, "pin": "5432"}),
        content_type="application/json"
    )
    assert login_resp.status_code == 200
    login_data = login_resp.get_json()
    assert login_data["authenticated"] is True


def test_farmer_registration_auto_id(client):
    payload = {
        "name": "Auto ID Farmer",
        "phone": "9123456789",
        "location": "Anantapur",
        "crop": "Groundnut",
        "pin": "1122"
    }

    response = client.post(
        "/api/auth/register",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["farmer_id"].startswith("FARMER-")


def test_admin_authentication_and_route_protection(client):
    # Unauthenticated access to /admin should redirect to /admin/login
    admin_page = client.get("/admin", follow_redirects=False)
    assert admin_page.status_code == 302
    assert "/admin/login" in admin_page.headers["Location"]

    # Unauthenticated access to /api/admin/summary should return 401
    api_summary = client.get("/api/admin/summary")
    assert api_summary.status_code == 401
    assert api_summary.get_json()["authenticated"] is False

    # Invalid admin credentials should fail
    bad_login = client.post(
        "/api/admin/login",
        data=json.dumps({"username": "ramsai016", "password": "wrongpassword"}),
        content_type="application/json"
    )
    assert bad_login.status_code == 401

    # Valid admin credentials (User name: ramsai016, password: luffyzoro) should succeed
    good_login = client.post(
        "/api/admin/login",
        data=json.dumps({"username": "ramsai016", "password": "luffyzoro"}),
        content_type="application/json"
    )
    assert good_login.status_code == 200
    assert good_login.get_json()["authenticated"] is True

    # After login, /admin should be accessible
    admin_access = client.get("/admin")
    assert admin_access.status_code == 200
    assert b"Operational Control Center" in admin_access.data

    # Protected endpoint should now return 200
    authed_summary = client.get("/api/admin/summary")
    assert authed_summary.status_code == 200
    assert authed_summary.get_json()["success"] is True

    # Admin logout
    logout_resp = client.post("/api/admin/logout")
    assert logout_resp.status_code == 200

    # /admin is blocked again
    post_logout = client.get("/admin")
    assert post_logout.status_code == 302


def test_farmer_offline_wallet_sync_endpoint(client):
    # Register/login farmer
    client.post(
        "/api/auth/login",
        data=json.dumps({"farmer_id": "DEMO-FARMER-001", "pin": "1234"}),
        content_type="application/json"
    )

    # Call sync endpoint
    sync_resp = client.post("/api/farmer/sync")
    assert sync_resp.status_code == 200
    sync_data = sync_resp.get_json()
    assert sync_data["success"] is True
    assert sync_data["farmer_id"] == "DEMO-FARMER-001"
