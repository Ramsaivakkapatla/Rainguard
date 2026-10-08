import uuid
from security.auth import AuthManager


def test_valid_farmer_pin():

    auth = AuthManager()

    result = auth.verify_pin(
        "DEMO-FARMER-001",
        "1234"
    )

    assert result["success"] is True
    assert result["authenticated"] is True


def test_invalid_pin():

    auth = AuthManager()

    result = auth.verify_pin(
        "DEMO-FARMER-001",
        "9999"
    )

    assert result["success"] is False
    assert result["authenticated"] is False


def test_unknown_farmer():

    auth = AuthManager()

    result = auth.verify_pin(
        "UNKNOWN-FARMER",
        "1234"
    )

    assert result["success"] is False


def test_pin_must_be_four_digits():

    auth = AuthManager()

    result = auth.verify_pin(
        "DEMO-FARMER-001",
        "123"
    )

    assert result["success"] is False


def test_wrong_pin_attempts_are_tracked():

    auth = AuthManager()

    for _ in range(5):

        result = auth.verify_pin(
            "DEMO-FARMER-002",
            "9999"
        )

    assert result["success"] is False

    locked = auth.verify_pin(
        "DEMO-FARMER-002",
        "2345"
    )

    assert locked["success"] is False


def test_valid_session():

    auth = AuthManager()

    result = auth.verify_pin(
        "DEMO-FARMER-003",
        "3456"
    )

    assert result["authenticated"] is True

    assert auth.is_session_valid(
        result["login_time"]
    ) is True


def test_farmer_registration():

    auth = AuthManager()
    farmer_id = f"REG-TEST-{uuid.uuid4().hex[:8]}"

    reg_result = auth.register_farmer(
        farmer_id=farmer_id,
        name="New Registered Farmer",
        pin="8899",
        phone="9876543210",
        location="Guntur",
        crop="Cotton"
    )

    assert reg_result["success"] is True
    assert reg_result["farmer_id"] == farmer_id

    # Verify farmer can log in with new PIN
    auth2 = AuthManager()
    login_result = auth2.verify_pin(farmer_id, "8899")
    assert login_result["success"] is True
    assert login_result["authenticated"] is True
    assert login_result["farmer_name"] == "New Registered Farmer"

    # Verify invalid PIN fails
    fail_result = auth2.verify_pin(farmer_id, "0000")
    assert fail_result["success"] is False


def test_admin_verification():

    # Default credentials: ramsai016 / luffyzoro
    assert AuthManager.verify_admin("ramsai016", "luffyzoro") is True
    assert AuthManager.verify_admin("ramsai016", "wrongpassword") is False
    assert AuthManager.verify_admin("wronguser", "luffyzoro") is False
    assert AuthManager.verify_admin("", "") is False