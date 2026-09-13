import uuid

from services.wallet_service import OfflineWallet
from services.sync_service import SyncService


def unique_farmer():

    return (
        "SYNC-TEST-"
        + uuid.uuid4().hex[:8]
    )


def test_sync_credit():

    wallet = OfflineWallet()

    sync = SyncService()

    farmer_id = unique_farmer()

    result = wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id="CLAIM-SYNC-001",
        amount=8000
    )

    transaction_id = (
        result["transaction_id"]
    )

    report = sync.synchronize()

    matching = [

        item

        for item in report["results"]

        if item.get(
            "transaction_id"
        ) == transaction_id
    ]

    assert len(matching) == 1

    assert matching[0][
        "status"
    ] == "SYNCED"


def test_sync_does_not_change_balance():

    wallet = OfflineWallet()

    sync = SyncService()

    farmer_id = unique_farmer()

    wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id="CLAIM-SYNC-002",
        amount=8000
    )

    before = wallet.get_balance(
        farmer_id
    )

    sync.synchronize()

    after = wallet.get_balance(
        farmer_id
    )

    assert before == 8000

    assert after == 8000


def test_sync_debit():

    wallet = OfflineWallet()

    sync = SyncService()

    farmer_id = unique_farmer()

    wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id="CLAIM-SYNC-003",
        amount=8000
    )

    wallet.spend(
        farmer_id=farmer_id,
        amount=2000
    )

    before = wallet.get_balance(
        farmer_id
    )

    sync.synchronize()

    after = wallet.get_balance(
        farmer_id
    )

    assert before == 6000

    assert after == 6000


def test_repeated_sync_is_safe():

    wallet = OfflineWallet()

    sync = SyncService()

    farmer_id = unique_farmer()

    wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id="CLAIM-SYNC-004",
        amount=5000
    )

    first = sync.synchronize()

    second = sync.synchronize()

    assert first["synced"] >= 1

    assert second["total"] == 0


def test_sync_handles_multiple_events():

    wallet = OfflineWallet()

    sync = SyncService()

    farmer_id = unique_farmer()

    wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id="CLAIM-SYNC-005",
        amount=10000
    )

    wallet.spend(
        farmer_id=farmer_id,
        amount=3000
    )

    wallet.spend(
        farmer_id=farmer_id,
        amount=2000
    )

    report = sync.synchronize()

    assert report["synced"] >= 3

    assert (
        wallet.get_balance(
            farmer_id
        )
        == 5000
    )