import os
import sqlite3
import json
from pathlib import Path


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

_env_db = os.environ.get("DATABASE_PATH")
if _env_db:
    DATABASE_PATH = Path(_env_db)
    DATABASE_DIR = DATABASE_PATH.parent
else:
    DATABASE_DIR = BASE_DIR / "data"
    DATABASE_PATH = DATABASE_DIR / "rainguard.db"

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10.0
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    try:
        connection.execute(
            "PRAGMA journal_mode = WAL"
        )
    except sqlite3.OperationalError:
        pass

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # FARMERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            farmer_id TEXT UNIQUE NOT NULL,

            name TEXT NOT NULL,

            phone TEXT,

            location TEXT,

            crop TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # --------------------------------------------------------
    # POLICIES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            policy_id TEXT UNIQUE NOT NULL,

            farmer_id TEXT NOT NULL,

            product_code TEXT NOT NULL,

            coverage_amount REAL NOT NULL,

            premium REAL NOT NULL,

            status TEXT DEFAULT 'ACTIVE',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (farmer_id)
                REFERENCES farmers(farmer_id)
        )
    """)


    # --------------------------------------------------------
    # RAINFALL OBSERVATIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rainfall_observations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            observation_id TEXT UNIQUE NOT NULL,

            source_id TEXT NOT NULL,

            source_name TEXT,

            location TEXT NOT NULL,

            rainfall_mm REAL NOT NULL,

            observation_time TEXT NOT NULL,

            source_status TEXT DEFAULT 'VALID',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # --------------------------------------------------------
    # CLAIMS / SETTLEMENTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            claim_id TEXT UNIQUE NOT NULL,

            policy_id TEXT NOT NULL,

            farmer_id TEXT NOT NULL,

            trusted_rainfall_mm REAL,

            threshold_mm REAL,

            payout_amount REAL DEFAULT 0,

            status TEXT NOT NULL,

            reason TEXT,

            settlement_id TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (policy_id)
                REFERENCES policies(policy_id),

            FOREIGN KEY (farmer_id)
                REFERENCES farmers(farmer_id)
        )
    """)


    # --------------------------------------------------------
    # WALLET TRANSACTIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallet_transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            transaction_id TEXT UNIQUE NOT NULL,

            farmer_id TEXT NOT NULL,

            claim_id TEXT,

            amount REAL NOT NULL,

            transaction_type TEXT NOT NULL,

            sync_status TEXT DEFAULT 'PENDING',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # --------------------------------------------------------
    # AUDIT RECORDS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_records (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            audit_id TEXT UNIQUE NOT NULL,

            claim_id TEXT,

            event_type TEXT NOT NULL,

            event_data TEXT NOT NULL,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # --------------------------------------------------------
    # OFFLINE SYNC QUEUE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_queue (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id TEXT UNIQUE NOT NULL,

            event_type TEXT NOT NULL,

            payload TEXT NOT NULL,

            status TEXT DEFAULT 'PENDING',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # --------------------------------------------------------
    # INDEXES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_wallet_farmer
        ON wallet_transactions(farmer_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_wallet_claim
        ON wallet_transactions(claim_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_wallet_type
        ON wallet_transactions(transaction_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_sync_status
        ON sync_queue(status)
    """)


    connection.commit()

    connection.close()


# ============================================================
# FARMER
# ============================================================

def save_farmer(
    farmer_id,
    name,
    phone,
    location,
    crop
):

    connection = get_connection()

    connection.execute(
        """
        INSERT OR REPLACE INTO farmers
        (
            farmer_id,
            name,
            phone,
            location,
            crop
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            farmer_id,
            name,
            phone,
            location,
            crop
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# POLICY
# ============================================================

def save_policy(
    policy_id,
    farmer_id,
    product_code,
    coverage_amount,
    premium,
    status="ACTIVE"
):

    connection = get_connection()

    connection.execute(
        """
        INSERT OR REPLACE INTO policies
        (
            policy_id,
            farmer_id,
            product_code,
            coverage_amount,
            premium,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            policy_id,
            farmer_id,
            product_code,
            coverage_amount,
            premium,
            status
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# RAINFALL OBSERVATION
# ============================================================

def save_rainfall(
    observation_id,
    source_id,
    source_name,
    location,
    rainfall_mm,
    observation_time,
    source_status="VALID"
):

    connection = get_connection()

    connection.execute(
        """
        INSERT OR REPLACE INTO rainfall_observations
        (
            observation_id,
            source_id,
            source_name,
            location,
            rainfall_mm,
            observation_time,
            source_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            observation_id,
            source_id,
            source_name,
            location,
            rainfall_mm,
            observation_time,
            source_status
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# CLAIM / SETTLEMENT
# ============================================================

def save_claim(
    claim_id,
    policy_id,
    farmer_id,
    trusted_rainfall_mm,
    threshold_mm,
    payout_amount,
    status,
    reason,
    settlement_id=None
):

    connection = get_connection()

    connection.execute(
        """
        INSERT OR REPLACE INTO claims
        (
            claim_id,
            policy_id,
            farmer_id,
            trusted_rainfall_mm,
            threshold_mm,
            payout_amount,
            status,
            reason,
            settlement_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            policy_id,
            farmer_id,
            trusted_rainfall_mm,
            threshold_mm,
            payout_amount,
            status,
            reason,
            settlement_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# WALLET TRANSACTION
# ============================================================

def save_wallet_transaction(
    transaction_id,
    farmer_id,
    claim_id,
    amount,
    transaction_type,
    sync_status="PENDING"
):

    connection = get_connection()

    connection.execute(
        """
        INSERT OR REPLACE INTO wallet_transactions
        (
            transaction_id,
            farmer_id,
            claim_id,
            amount,
            transaction_type,
            sync_status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_id,
            farmer_id,
            claim_id,
            amount,
            transaction_type,
            sync_status
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# CHECK PAYOUT FOR CLAIM
# ============================================================

def get_wallet_transaction_by_claim(
    farmer_id,
    claim_id
):

    if not claim_id:

        return None

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM wallet_transactions

        WHERE farmer_id = ?
        AND claim_id = ?
        AND transaction_type = 'CREDIT'

        ORDER BY id DESC

        LIMIT 1
        """,
        (
            farmer_id,
            claim_id
        )
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:

        return None

    return dict(row)


# ============================================================
# GET WALLET TRANSACTIONS
# ============================================================

def get_wallet_transactions(
    farmer_id,
    limit=50
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM wallet_transactions

        WHERE farmer_id = ?

        ORDER BY id DESC

        LIMIT ?
        """,
        (
            farmer_id,
            int(limit)
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# AUDIT RECORD
# ============================================================

def save_audit_record(
    audit_id,
    claim_id,
    event_type,
    event_data
):

    connection = get_connection()

    if not isinstance(
        event_data,
        str
    ):

        event_data = json.dumps(
            event_data
        )

    connection.execute(
        """
        INSERT OR REPLACE INTO audit_records
        (
            audit_id,
            claim_id,
            event_type,
            event_data
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            audit_id,
            claim_id,
            event_type,
            event_data
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# SYNC QUEUE
# ============================================================

def add_sync_event(
    event_id,
    event_type,
    payload
):

    connection = get_connection()

    if not isinstance(
        payload,
        str
    ):

        payload = json.dumps(
            payload
        )

    connection.execute(
        """
        INSERT OR REPLACE INTO sync_queue
        (
            event_id,
            event_type,
            payload
        )
        VALUES (?, ?, ?)
        """,
        (
            event_id,
            event_type,
            payload
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# GET CLAIM
# ============================================================

def get_claim(
    claim_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM claims

        WHERE claim_id = ?
        """,
        (
            claim_id,
        )
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:

        return None

    return dict(row)


# ============================================================
# GET AUDIT TRAIL
# ============================================================

def get_audit_records(
    claim_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM audit_records

        WHERE claim_id = ?

        ORDER BY id ASC
        """,
        (
            claim_id,
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# GET RAINFALL EVIDENCE
# ============================================================

def get_rainfall_evidence(
    observation_ids
):

    if not observation_ids:

        return []

    connection = get_connection()

    placeholders = ",".join(
        ["?"] * len(observation_ids)
    )

    query = f"""
        SELECT *
        FROM rainfall_observations

        WHERE observation_id IN ({placeholders})

        ORDER BY observation_time ASC
    """

    cursor = connection.cursor()

    cursor.execute(
        query,
        observation_ids
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# SYSTEM SUMMARY & ADMIN REPORTING
# ============================================================

def get_system_summary():
    """
    Operational summary of the entire RainGuard system.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM farmers")
        total_farmers = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM policies WHERE status = 'ACTIVE'")
        active_policies = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM claims")
        total_claims = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COALESCE(SUM(payout_amount), 0) AS total
            FROM claims
            WHERE status IN ('PAYOUT_SETTLED', 'PAYOUT_CREDITED')
        """)
        total_payout_amount = float(cursor.fetchone()["total"])

        cursor.execute("SELECT COUNT(*) AS total FROM wallet_transactions")
        wallet_transactions_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM sync_queue WHERE status = 'PENDING'")
        pending_sync_count = cursor.fetchone()["total"]

        return {
            "total_farmers": total_farmers,
            "active_policies": active_policies,
            "total_claims": total_claims,
            "total_payout_amount": total_payout_amount,
            "wallet_transactions": wallet_transactions_count,
            "pending_sync_events": pending_sync_count
        }
    finally:
        connection.close()


def get_all_farmers(limit=100):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM farmers ORDER BY id DESC LIMIT ?", (int(limit),))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_all_policies(limit=100):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT p.*, f.name AS farmer_name
            FROM policies p
            LEFT JOIN farmers f ON p.farmer_id = f.farmer_id
            ORDER BY p.id DESC
            LIMIT ?
        """, (int(limit),))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_all_claims(limit=100):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT c.*, f.name AS farmer_name
            FROM claims c
            LEFT JOIN farmers f ON c.farmer_id = f.farmer_id
            ORDER BY c.id DESC
            LIMIT ?
        """, (int(limit),))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_recent_wallet_transactions(limit=100):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT w.*, f.name AS farmer_name
            FROM wallet_transactions w
            LEFT JOIN farmers f ON w.farmer_id = f.farmer_id
            ORDER BY w.id DESC
            LIMIT ?
        """, (int(limit),))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_all_sync_events(limit=100):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sync_queue ORDER BY id DESC LIMIT ?", (int(limit),))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_recent_audit_records(limit=100):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM audit_records ORDER BY id DESC LIMIT ?", (int(limit),))
        records = []
        for row in cursor.fetchall():
            rec = dict(row)
            try:
                rec["event_data"] = json.loads(rec["event_data"])
            except Exception:
                pass
            records.append(rec)
        return records
    finally:
        connection.close()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

if __name__ == "__main__":

    initialize_database()

    print(
        "RainGuard database initialized successfully."
    )

    print(
        f"Database location: {DATABASE_PATH}"
    )