import json
import uuid

from database.database import (
    initialize_database,
    save_wallet_transaction,
    add_sync_event,
    get_connection
)


class OfflineWallet:
    """
    Offline wallet service for RainGuard.

    Supports:
    - Offline payout credit
    - Offline spending
    - Balance calculation
    - Duplicate payout protection
    - Pending synchronization
    - Sync status tracking
    """

    def __init__(self):
        initialize_database()

    # =====================================================
    # TRANSACTION ID
    # =====================================================

    def _transaction_id(self):
        return "TXN-" + uuid.uuid4().hex[:12].upper()

    # =====================================================
    # GET WALLET BALANCE
    # =====================================================

    def get_balance(self, farmer_id):

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COALESCE(
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
            (farmer_id,)
        )

        row = cursor.fetchone()

        connection.close()

        return float(row["balance"] or 0)

    # =====================================================
    # CREDIT PAYOUT
    # =====================================================

    def credit_payout(
        self,
        farmer_id,
        claim_id,
        amount
    ):
        """
        Credit an insurance payout to the farmer's
        offline wallet.

        Duplicate protection:
        The same farmer + claim cannot receive the
        payout twice.
        """

        # -------------------------------------------------
        # VALIDATE AMOUNT
        # -------------------------------------------------

        try:
            amount = float(amount)

        except (TypeError, ValueError):

            return {
                "success": False,
                "error": "Invalid payout amount."
            }

        if amount <= 0:

            return {
                "success": False,
                "error": "Payout amount must be greater than zero."
            }

        # -------------------------------------------------
        # DUPLICATE CLAIM PROTECTION
        # -------------------------------------------------

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                transaction_id,
                amount,
                sync_status,
                created_at

            FROM wallet_transactions

            WHERE farmer_id = ?
            AND claim_id = ?
            AND transaction_type = 'CREDIT'

            LIMIT 1
            """,
            (
                farmer_id,
                claim_id
            )
        )

        existing = cursor.fetchone()

        connection.close()

        # -------------------------------------------------
        # DUPLICATE FOUND
        # -------------------------------------------------

        if existing:

            balance = self.get_balance(
                farmer_id
            )

            return {
                "success": True,
                "duplicate": True,
                "offline": True,
                "transaction_id": existing["transaction_id"],
                "claim_id": claim_id,
                "amount": float(existing["amount"]),
                "sync_status": existing["sync_status"],
                "balance": balance,
                "message": (
                    "Payout already credited "
                    "for this claim."
                )
            }

        # -------------------------------------------------
        # CREATE NEW TRANSACTION
        # -------------------------------------------------

        transaction_id = self._transaction_id()

        save_wallet_transaction(
            transaction_id,
            farmer_id,
            claim_id,
            amount,
            "CREDIT",
            "PENDING"
        )

        # -------------------------------------------------
        # CREATE SYNC EVENT
        # -------------------------------------------------

        add_sync_event(
            "SYNC-" + transaction_id,
            "WALLET_CREDIT",
            {
                "transaction_id": transaction_id,
                "claim_id": claim_id,
                "farmer_id": farmer_id,
                "amount": amount
            }
        )

        # -------------------------------------------------
        # NEW BALANCE
        # -------------------------------------------------

        balance = self.get_balance(
            farmer_id
        )

        return {
            "success": True,
            "duplicate": False,
            "offline": True,
            "transaction_id": transaction_id,
            "claim_id": claim_id,
            "amount": amount,
            "sync_status": "PENDING",
            "balance": balance,
            "message": (
                "Payout credited to "
                "offline wallet."
            )
        }

    # =====================================================
    # SPEND FROM WALLET
    # =====================================================

    def spend(
        self,
        farmer_id,
        amount
    ):
        """
        Spend money from the offline wallet.

        Raises ValueError when:
        - amount is invalid
        - amount is zero or negative
        - amount is greater than wallet balance
        """

        # -------------------------------------------------
        # VALIDATE AMOUNT
        # -------------------------------------------------

        try:
            amount = float(amount)

        except (TypeError, ValueError):

            raise ValueError(
                "Invalid spending amount."
            )

        if amount <= 0:

            raise ValueError(
                "Amount must be greater than zero."
            )

        # -------------------------------------------------
        # CHECK BALANCE
        # -------------------------------------------------

        balance = self.get_balance(
            farmer_id
        )

        if amount > balance:

            raise ValueError(
                f"Insufficient wallet balance. "
                f"Available: ₹{balance:.2f}, "
                f"Requested: ₹{amount:.2f}"
            )

        # -------------------------------------------------
        # CREATE DEBIT TRANSACTION
        # -------------------------------------------------

        transaction_id = self._transaction_id()

        save_wallet_transaction(
            transaction_id,
            farmer_id,
            None,
            amount,
            "DEBIT",
            "PENDING"
        )

        # -------------------------------------------------
        # CREATE SYNC EVENT
        # -------------------------------------------------

        add_sync_event(
            "SYNC-" + transaction_id,
            "WALLET_DEBIT",
            {
                "transaction_id": transaction_id,
                "farmer_id": farmer_id,
                "amount": amount
            }
        )

        # -------------------------------------------------
        # NEW BALANCE
        # -------------------------------------------------

        new_balance = self.get_balance(
            farmer_id
        )

        return {
            "success": True,
            "offline": True,
            "transaction_id": transaction_id,
            "amount": amount,
            "balance": new_balance,
            "sync_status": "PENDING"
        }

    # =====================================================
    # PENDING SYNC COUNT
    # =====================================================

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

        return int(row["count"])

    # =====================================================
    # GET PENDING SYNC EVENTS
    # =====================================================

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

    # =====================================================
    # MARK EVENT AS SYNCED
    # =====================================================

    def mark_synced(
        self,
        event_id
    ):

        connection = get_connection()
        cursor = connection.cursor()

        # -------------------------------------------------
        # FIND EVENT
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT payload

            FROM sync_queue

            WHERE event_id = ?
            """,
            (event_id,)
        )

        row = cursor.fetchone()

        if not row:

            connection.close()

            return False

        # -------------------------------------------------
        # READ PAYLOAD
        # -------------------------------------------------

        try:

            payload = json.loads(
                row["payload"]
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):

            connection.close()

            return False

        transaction_id = payload.get(
            "transaction_id"
        )

        # -------------------------------------------------
        # MARK SYNC EVENT
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE sync_queue

            SET status = 'SYNCED'

            WHERE event_id = ?
            """,
            (event_id,)
        )

        # -------------------------------------------------
        # MARK WALLET TRANSACTION
        # -------------------------------------------------

        if transaction_id:

            cursor.execute(
                """
                UPDATE wallet_transactions

                SET sync_status = 'SYNCED'

                WHERE transaction_id = ?
                """,
                (transaction_id,)
            )

        connection.commit()

        connection.close()

        return True

    # =====================================================
    # WALLET SUMMARY
    # =====================================================

    def summary(
        self,
        farmer_id
    ):

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) AS count

            FROM wallet_transactions

            WHERE farmer_id = ?
            """,
            (farmer_id,)
        )

        row = cursor.fetchone()

        connection.close()

        return {
            "farmer_id": farmer_id,
            "balance": self.get_balance(
                farmer_id
            ),
            "transaction_count": int(
                row["count"]
            ),
            "pending_sync_count":
                self.pending_sync_count(),
            "offline_ready": True
        }