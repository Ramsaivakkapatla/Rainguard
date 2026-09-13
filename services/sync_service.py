import json

from database.database import (
    get_connection
)


class SyncService:
    """
    Offline synchronization engine.

    Handles:
    - pending wallet events
    - duplicate detection
    - replay protection
    - synchronization status
    """


    # ========================================================
    # GET PENDING EVENTS
    # ========================================================

    def get_pending_events(self):

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
    # CHECK WHETHER TRANSACTION ALREADY EXISTS
    # ========================================================

    def transaction_exists(
        self,
        transaction_id
    ):

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id

            FROM wallet_transactions

            WHERE transaction_id = ?
            """,
            (
                transaction_id,
            )
        )

        row = cursor.fetchone()

        connection.close()

        return row is not None


    # ========================================================
    # MARK EVENT AS SYNCED
    # ========================================================

    def mark_event_synced(
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
    # PROCESS ONE EVENT
    # ========================================================

    def process_event(
        self,
        event
    ):

        event_id = event[
            "event_id"
        ]

        event_type = event[
            "event_type"
        ]

        try:

            payload = json.loads(
                event["payload"]
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):

            return {
                "event_id":
                    event_id,

                "status":
                    "REJECTED",

                "reason":
                    "Invalid payload"
            }


        transaction_id = payload.get(
            "transaction_id"
        )


        if not transaction_id:

            return {
                "event_id":
                    event_id,

                "status":
                    "REJECTED",

                "reason":
                    "Missing transaction ID"
            }


        # ----------------------------------------------------
        # Replay / duplicate protection
        # ----------------------------------------------------

        if not self.transaction_exists(
            transaction_id
        ):

            return {
                "event_id":
                    event_id,

                "status":
                    "REJECTED",

                "reason":
                    "Transaction does not exist locally"
            }


        # ----------------------------------------------------
        # Event type validation
        # ----------------------------------------------------

        if event_type not in (
            "WALLET_CREDIT",
            "WALLET_DEBIT"
        ):

            return {
                "event_id":
                    event_id,

                "status":
                    "REJECTED",

                "reason":
                    "Unknown event type"
            }


        # ----------------------------------------------------
        # Mark successful synchronization
        # ----------------------------------------------------

        self.mark_event_synced(
            event_id
        )


        return {
            "event_id":
                event_id,

            "transaction_id":
                transaction_id,

            "status":
                "SYNCED",

            "reason":
                "Transaction synchronized successfully"
        }


    # ========================================================
    # SYNCHRONIZE ALL EVENTS
    # ========================================================

    def synchronize(self):

        events = (
            self.get_pending_events()
        )

        results = []

        for event in events:

            result = self.process_event(
                event
            )

            results.append(
                result
            )


        synced = sum(
            1
            for result in results
            if result["status"]
            == "SYNCED"
        )

        rejected = sum(
            1
            for result in results
            if result["status"]
            == "REJECTED"
        )


        return {

            "total":
                len(events),

            "synced":
                synced,

            "rejected":
                rejected,

            "results":
                results
        }