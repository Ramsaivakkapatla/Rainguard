import uuid

from services.wallet_service import OfflineWallet


def unique_farmer_id():
    return f"WALLET-TEST-{uuid.uuid4().hex[:8]}"


def test_wallet_receives_payout():

    wallet = OfflineWallet()

    farmer_id = unique_farmer_id()

    result = wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id=f"CLAIM-{uuid.uuid4().hex[:8]}",
        amount=8000
    )

    assert result["amount"] == 8000

    assert result["offline"] is True

    assert result["balance"] == 8000


def test_wallet_can_spend_offline():

    wallet = OfflineWallet()

    farmer_id = unique_farmer_id()

    wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id=f"CLAIM-{uuid.uuid4().hex[:8]}",
        amount=8000
    )

    result = wallet.spend(
        farmer_id=farmer_id,
        amount=2000
    )

    assert result["offline"] is True

    assert result["balance"] == 6000


def test_wallet_rejects_overspending():

    wallet = OfflineWallet()

    farmer_id = unique_farmer_id()

    wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id=f"CLAIM-{uuid.uuid4().hex[:8]}",
        amount=3000
    )

    try:

        wallet.spend(
            farmer_id=farmer_id,
            amount=5000
        )

        assert False, "Overspending should have been rejected"

    except ValueError as error:

        assert "Insufficient" in str(error)


def test_wallet_creates_sync_queue():

    wallet = OfflineWallet()

    farmer_id = unique_farmer_id()

    wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id=f"CLAIM-{uuid.uuid4().hex[:8]}",
        amount=5000
    )

    events = wallet.get_pending_sync_events()

    assert len(events) > 0


def test_wallet_can_mark_synced():

    wallet = OfflineWallet()

    farmer_id = unique_farmer_id()

    result = wallet.credit_payout(
        farmer_id=farmer_id,
        claim_id=f"CLAIM-{uuid.uuid4().hex[:8]}",
        amount=4000
    )

    transaction_id = result["transaction_id"]

    wallet.mark_synced(transaction_id)

    events = wallet.get_pending_sync_events()

    matching_events = [
        event
        for event in events
        if event["event_id"] == transaction_id
    ]

    assert len(matching_events) == 0