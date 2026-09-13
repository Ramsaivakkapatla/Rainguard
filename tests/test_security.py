import pytest

from security.device_security import DeviceSecurity


def test_farmer_can_register():

    security = DeviceSecurity()

    result = security.register_farmer(
        farmer_id="FARMER-A",
        pin="1234"
    )

    assert result is True


def test_farmer_can_login():

    security = DeviceSecurity()

    security.register_farmer(
        farmer_id="FARMER-A",
        pin="1234"
    )

    result = security.login(
        farmer_id="FARMER-A",
        pin="1234"
    )

    assert result["success"] is True

    assert (
        result["farmer_id"]
        == "FARMER-A"
    )


def test_wrong_pin_is_rejected():

    security = DeviceSecurity()

    security.register_farmer(
        farmer_id="FARMER-A",
        pin="1234"
    )

    result = security.login(
        farmer_id="FARMER-A",
        pin="9999"
    )

    assert result["success"] is False


def test_second_farmer_cannot_access_first_wallet():

    security = DeviceSecurity()

    security.register_farmer(
        farmer_id="FARMER-A",
        pin="1234"
    )

    security.register_farmer(
        farmer_id="FARMER-B",
        pin="5678"
    )

    login = security.login(
        farmer_id="FARMER-A",
        pin="1234"
    )

    token = login[
        "session_token"
    ]


    # Farmer A's session attempts
    # to access Farmer B's wallet.

    assert security.validate_session(
        token,
        "FARMER-B"
    ) is False


def test_policy_binding_is_protected():

    security = DeviceSecurity()

    security.register_farmer(
        farmer_id="FARMER-A",
        pin="1234"
    )

    login = security.login(
        farmer_id="FARMER-A",
        pin="1234"
    )

    token = login[
        "session_token"
    ]


    assert security.authorize_policy_binding(
        token,
        "FARMER-A"
    ) is True


def test_payout_is_protected():

    security = DeviceSecurity()

    security.register_farmer(
        farmer_id="FARMER-A",
        pin="1234"
    )

    login = security.login(
        farmer_id="FARMER-A",
        pin="1234"
    )

    token = login[
        "session_token"
    ]


    assert security.authorize_payout(
        token,
        "FARMER-A"
    ) is True


def test_unauthorized_payout_is_rejected():

    security = DeviceSecurity()

    security.register_farmer(
        farmer_id="FARMER-A",
        pin="1234"
    )

    login = security.login(
        farmer_id="FARMER-A",
        pin="1234"
    )

    token = login[
        "session_token"
    ]


    with pytest.raises(
        PermissionError
    ):

        security.authorize_payout(
            token,
            "FARMER-B"
        )