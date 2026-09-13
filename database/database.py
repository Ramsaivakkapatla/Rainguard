import sqlite3
import json
from pathlib import Path


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "data"

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = DATABASE_DIR / "rainguard.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    # Enable foreign-key support
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

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