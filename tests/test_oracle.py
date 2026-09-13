from datetime import datetime

from engine.oracle_engine import OracleEngine


def test_all_sources_agree():

    engine = OracleEngine()

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    result = engine.evaluate(
        evaluation_time
    )

    assert result["decision"] == "TRUSTED"

    assert result["trusted_rainfall_mm"] == 43


def test_manipulated_source_is_detected():

    engine = OracleEngine()

    # Simulate a compromised station.
    engine.sources[2]["rainfall_mm"] = 5

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    result = engine.evaluate(
        evaluation_time
    )

    assert result["decision"] == "TRUSTED"

    assert result["trusted_rainfall_mm"] == 43

    assert "ORACLE_C" not in result[
        "trusted_sources"
    ]

    oracle_c = next(
        source
        for source in result["sources"]
        if source["source_id"] == "ORACLE_C"
    )

    assert oracle_c["status"] == "OUTLIER"


def test_stale_source_is_excluded():

    engine = OracleEngine()

    # Make Oracle C nine days old.
    engine.sources[2]["timestamp"] = (
        "2026-09-03T09:00:00"
    )

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    result = engine.evaluate(
        evaluation_time
    )

    assert result["decision"] == "TRUSTED"

    oracle_c = next(
        source
        for source in result["sources"]
        if source["source_id"] == "ORACLE_C"
    )

    assert oracle_c["status"] == "STALE"


def test_non_responding_source():

    engine = OracleEngine()

    engine.sources[2]["responding"] = False

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    result = engine.evaluate(
        evaluation_time
    )

    assert result["decision"] == "TRUSTED"

    oracle_c = next(
        source
        for source in result["sources"]
        if source["source_id"] == "ORACLE_C"
    )

    assert oracle_c["status"] == "NON_RESPONDING"


def test_two_way_disagreement():

    engine = OracleEngine()

    engine.sources[0]["rainfall_mm"] = 20
    engine.sources[1]["rainfall_mm"] = 50
    engine.sources[2]["rainfall_mm"] = 80

    evaluation_time = datetime.fromisoformat(
        "2026-09-12T09:00:00"
    )

    result = engine.evaluate(
        evaluation_time
    )

    assert result["decision"] == "DISPUTE"

    assert result[
        "trusted_rainfall_mm"
    ] is None