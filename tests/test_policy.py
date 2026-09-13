from engine.policy_engine import PolicyEngine


def test_policy_triggers_payout():

    engine = PolicyEngine()

    result = engine.evaluate_policy(
        "RG-RICE-01",
        42
    )

    assert result["success"] is True

    assert result["status"] == "PAYOUT_TRIGGERED"

    assert result["payout_amount"] == 8000


def test_policy_does_not_trigger():

    engine = PolicyEngine()

    result = engine.evaluate_policy(
        "RG-RICE-01",
        80
    )

    assert result["success"] is True

    assert result["status"] == "NO_PAYOUT"

    assert result["payout_amount"] == 0


def test_unknown_product():

    engine = PolicyEngine()

    result = engine.evaluate_policy(
        "UNKNOWN",
        42
    )

    assert result["success"] is False