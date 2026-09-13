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