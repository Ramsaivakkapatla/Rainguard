from datetime import datetime

from engine.oracle_engine import OracleEngine
from engine.policy_engine import PolicyEngine
from engine.settlement_engine import SettlementEngine


def create_engines():

    oracle_engine = OracleEngine()

    policy_engine = PolicyEngine()

    settlement_engine = SettlementEngine(
        policy_engine
    )

    return (
        oracle_engine,
        settlement_engine
    )


# ==================================================
# TEST 1
# NORMAL VALID PAYOUT
# ==================================================

def test_valid_drought_payout():

    oracle_engine, settlement_engine = (
        create_engines()
    )

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    oracle_result = oracle_engine.evaluate(
        evaluation_time
    )

    result = settlement_engine.settle(
        oracle_result,
        "RG-RICE-01"
    )

    assert result["success"] is True

    assert result["status"] == (
        "PAYOUT_SETTLED"
    )

    assert result["payout_amount"] == 8000

    assert result[
        "trusted_rainfall_mm"
    ] == 43


# ==================================================
# TEST 2
# NORMAL RAINFALL = NO PAYOUT
# ==================================================

def test_normal_rainfall_no_payout():

    oracle_engine, settlement_engine = (
        create_engines()
    )

    # Change all three trusted rainfall
    # sources to healthy rainfall.

    oracle_engine.sources[0][
        "rainfall_mm"
    ] = 80

    oracle_engine.sources[1][
        "rainfall_mm"
    ] = 82

    oracle_engine.sources[2][
        "rainfall_mm"
    ] = 81

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    oracle_result = oracle_engine.evaluate(
        evaluation_time
    )

    result = settlement_engine.settle(
        oracle_result,
        "RG-RICE-01"
    )

    assert result["success"] is True

    assert result["status"] == (
        "NO_PAYOUT"
    )

    assert result["payout_amount"] == 0


# ==================================================
# TEST 3
# DISPUTED DATA MUST NOT PAY
# ==================================================

def test_dispute_blocks_payout():

    oracle_engine, settlement_engine = (
        create_engines()
    )

    oracle_engine.sources[0][
        "rainfall_mm"
    ] = 20

    oracle_engine.sources[1][
        "rainfall_mm"
    ] = 50

    oracle_engine.sources[2][
        "rainfall_mm"
    ] = 80

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    oracle_result = oracle_engine.evaluate(
        evaluation_time
    )

    assert oracle_result[
        "decision"
    ] == "DISPUTE"

    result = settlement_engine.settle(
        oracle_result,
        "RG-RICE-01"
    )

    assert result["success"] is False

    assert result["status"] == (
        "SETTLEMENT_BLOCKED"
    )

    assert result["payout_amount"] == 0


# ==================================================
# TEST 4
# MANIPULATED SOURCE SHOULD STILL PAY
# ==================================================

def test_manipulated_source_does_not_block_valid_payout():

    oracle_engine, settlement_engine = (
        create_engines()
    )

    # Oracle C is manipulated.

    oracle_engine.sources[2][
        "rainfall_mm"
    ] = 5

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    oracle_result = oracle_engine.evaluate(
        evaluation_time
    )

    assert oracle_result[
        "decision"
    ] == "TRUSTED"

    result = settlement_engine.settle(
        oracle_result,
        "RG-RICE-01"
    )

    assert result["success"] is True

    assert result["status"] == (
        "PAYOUT_SETTLED"
    )

    assert result["payout_amount"] == 8000


# ==================================================
# TEST 5
# STALE SOURCE SHOULD NOT BLOCK VALID PAYOUT
# ==================================================

def test_stale_source_does_not_block_payout():

    oracle_engine, settlement_engine = (
        create_engines()
    )

    # Oracle C is nine days old.

    oracle_engine.sources[2][
        "timestamp"
    ] = "2026-09-03T09:00:00"

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    oracle_result = oracle_engine.evaluate(
        evaluation_time
    )

    assert oracle_result[
        "decision"
    ] == "TRUSTED"

    result = settlement_engine.settle(
        oracle_result,
        "RG-RICE-01"
    )

    assert result["success"] is True

    assert result["status"] == (
        "PAYOUT_SETTLED"
    )

    assert result["payout_amount"] == 8000