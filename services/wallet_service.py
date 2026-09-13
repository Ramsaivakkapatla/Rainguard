import uuid
import json

from database.database import (
    initialize_database,
    save_wallet_transaction,
    add_sync_event,
    get_connection
)


class OfflineWallet:
    """
    Offline-first wallet for RainGuard.

    The wallet can:
    - receive insurance payouts offline
    - spend money offline
    - calculate balance locally
    - queue transactions for later synchronization
    - prevent duplicate transactions
    """


    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self):

        initialize_database()


    # ========================================================
    # GENERATE TRANSACTION ID
    # ========================================================

    def _transaction_id(self):

        return (
            "TXN-"
            + uuid.uuid4().hex[:12].upper()
        )


    # ========================================================
    # GET CURRENT BALANCE
    # ========================================================

    def get_balance(
        self,
        farmer_id
    ):

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'CREDIT'
                            THEN amount

                            WHEN transaction_type = 'DEBIT'
                            THEN -amount

                            ELSE 0
                        END
                    ),
                    0
                ) AS balance

            FROM wallet_transactions

            WHERE farmer_id = ?
            """,
            (
                farmer_id,
            )
        )

        row = cursor.fetchone()

        connection.close()

        return float(
            row["balance"]
        )


    # ========================================================
    # CREDIT PAYOUT
    # ========================================================

    def credit_payout(
        self,
        farmer_id,
        claim_id,
        amount
    ):

        if amount <= 0:

            raise ValueError(
                "Payout amount must be greater than zero."
            )


        transaction_id = (
            self._transaction_id()
        )


        # ----------------------------------------------------
        # Save locally FIRST
        # ----------------------------------------------------

        save_wallet_transaction(

            transaction_id=transaction_id,

            farmer_id=farmer_id,

            claim_id=claim_id,

            amount=amount,

            transaction_type="CREDIT",

            sync_status="PENDING"
        )


        # ----------------------------------------------------
        # Add synchronization event
        # ----------------------------------------------------

        add_sync_event(

            event_id=transaction_id,

            event_type="WALLET_CREDIT",

            payload={
                "transaction_id":
                    transaction_id,

                "farmer_id":
                    farmer_id,

                "claim_id":
                    claim_id,

                "amount":
                    amount,

                "transaction_type":
                    "CREDIT"
            }
        )


        return {

            "transaction_id":
                transaction_id,

            "farmer_id":
                farmer_id,

            "claim_id":
                claim_id,

            "amount":
                amount,

            "type":
                "CREDIT",

            "offline":
                True,

            "balance":
                self.get_balance(
                    farmer_id
                )
        }


    # ========================================================
    # SPEND OFFLINE
    # ========================================================

    def spend(
        self,
        farmer_id,
        amount
    ):

        if amount <= 0:

            raise ValueError(
                "Spend amount must be greater than zero."
            )


        # ----------------------------------------------------
        # Check local balance
        # ----------------------------------------------------

        current_balance = (
            self.get_balance(
                farmer_id
            )
        )


        if amount > current_balance:

            raise ValueError(
                "Insufficient wallet balance."
            )


        transaction_id = (
            self._transaction_id()
        )


        # ----------------------------------------------------
        # Save local transaction
        # ----------------------------------------------------

        save_wallet_transaction(

            transaction_id=transaction_id,

            farmer_id=farmer_id,

            claim_id=None,

            amount=amount,

            transaction_type="DEBIT",

            sync_status="PENDING"
        )


        # ----------------------------------------------------
        # Queue for later synchronization
        # ----------------------------------------------------

        add_sync_event(

            event_id=transaction_id,

            event_type="WALLET_DEBIT",

            payload={
                "transaction_id":
                    transaction_id,

                "farmer_id":
                    farmer_id,

                "amount":
                    amount,

                "transaction_type":
                    "DEBIT"
            }
        )


        return {

            "transaction_id":
                transaction_id,

            "farmer_id":
                farmer_id,

            "amount":
                amount,

            "type":
                "DEBIT",

            "offline":
                True,

            "balance":
                self.get_balance(
                    farmer_id
                )
        }


    # ========================================================
    # CHECK PENDING SYNCHRONIZATION
    # ========================================================

    def pending_sync_count(self):

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM sync_queue
            WHERE status = 'PENDING'
            """
        )

        row = cursor.fetchone()

        connection.close()

        return int(
            row["count"]
        )


    # ========================================================
    # GET PENDING EVENTS
    # ========================================================

    def get_pending_sync_events(self):

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM sync_queue
            WHERE status = 'PENDING'
            ORDER BY id ASC
            """
        )

        rows = cursor.fetchall()

        connection.close()

        return [
            dict(row)
            for row in rows
        ]


    # ========================================================
    # MARK SYNCED
    # ========================================================

    def mark_synced(
        self,
        event_id
    ):

        connection = get_connection()

        connection.execute(
            """
            UPDATE sync_queue

            SET status = 'SYNCED'

            WHERE event_id = ?
            """,
            (
                event_id,
            )
        )


        # Also update wallet transaction status

        connection.execute(
            """
            UPDATE wallet_transactions

            SET sync_status = 'SYNCED'

            WHERE transaction_id = ?
            """,
            (
                event_id,
            )
        )


        connection.commit()

        connection.close()


    # ========================================================
    # WALLET SUMMARY
    # ========================================================

    def summary(
        self,
        farmer_id
    ):

        balance = self.get_balance(
            farmer_id
        )

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) AS count

            FROM wallet_transactions

            WHERE farmer_id = ?
            """,
            (
                farmer_id,
            )
        )

        row = cursor.fetchone()

        connection.close()


        return {

            "farmer_id":
                farmer_id,

            "balance":
                balance,

            "transaction_count":
                int(row["count"]),

            "pending_sync":
                self.pending_sync_count(),

            "offline_ready":
                True
        }