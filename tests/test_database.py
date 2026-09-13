from database.database import (
    initialize_database,
    save_farmer,
    save_policy,
    save_rainfall,
    save_claim,
    save_audit_record,
    get_claim,
    get_audit_records
)


def test_database_initialization():

    initialize_database()

    assert True


def test_save_farmer():

    initialize_database()

    save_farmer(
        farmer_id="TEST-FARMER-001",
        name="Demo Farmer",
        phone="9000000001",
        location="Demo District",
        crop="Rice"
    )

    assert True


def test_save_policy():

    initialize_database()

    save_policy(
        policy_id="TEST-POLICY-001",
        farmer_id="TEST-FARMER-001",
        product_code="RG-RICE-01",
        coverage_amount=10000,
        premium=300
    )

    assert True


def test_save_rainfall():

    initialize_database()

    save_rainfall(
        observation_id="OBS-001",
        source_id="ORACLE-A",
        source_name="Rainfall Oracle A",
        location="Demo District",
        rainfall_mm=43,
        observation_time="2026-09-12T09:00:00"
    )

    assert True


def test_save_claim_and_audit():

    initialize_database()

    save_claim(
        claim_id="CLAIM-001",
        policy_id="TEST-POLICY-001",
        farmer_id="TEST-FARMER-001",
        trusted_rainfall_mm=43,
        threshold_mm=60,
        payout_amount=8000,
        status="PAYOUT_SETTLED",
        reason="Rainfall below threshold",
        settlement_id="SET-001"
    )

    save_audit_record(
        audit_id="AUD-001",
        claim_id="CLAIM-001",
        event_type="SETTLEMENT_RECONSTRUCTION",
        event_data={
            "rainfall": 43,
            "source": "ORACLE-A",
            "timestamp":
                "2026-09-12T09:00:00",
            "payout": 8000
        }
    )

    claim = get_claim(
        "CLAIM-001"
    )

    audit = get_audit_records(
        "CLAIM-001"
    )

    assert claim is not None

    assert claim[
        "payout_amount"
    ] == 8000

    assert len(audit) >= 1