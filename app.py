import json
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session
)

from engine.policy_engine import PolicyEngine
from security.auth import AuthManager

from services.wallet_service import OfflineWallet
from services.sync_service import SyncService

from database.database import (
    initialize_database,
    get_connection
)


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)

app.secret_key = "RAINGUARD-HACKATHON-DEMO-SECRET-CHANGE-ME"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

initialize_database()


# ==========================================================
# ENGINES / SERVICES
# ==========================================================

policy_engine = PolicyEngine()

auth_manager = AuthManager()

wallet_service = OfflineWallet()

sync_service = SyncService()


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================================
# FARMER PORTAL
# ==========================================================

@app.route("/farmer")
def farmer():

    farmer_id = session.get(
        "farmer_id"
    )

    if not farmer_id:

        return render_template(
            "farmer_login.html"
        )

    return render_template(
        "farmer.html",
        farmer_id=farmer_id,
        farmer_name=session.get(
            "farmer_name",
            "Farmer"
        )
    )


# ==========================================================
# FARMER LOGIN
# ==========================================================

@app.route(
    "/api/auth/login",
    methods=["POST"]
)
def farmer_login():

    data = request.get_json() or {}

    farmer_id = data.get(
        "farmer_id"
    )

    pin = data.get(
        "pin"
    )

    if not farmer_id:

        return jsonify({

            "success": False,

            "authenticated": False,

            "error":
                "Farmer ID is required."

        }), 400


    if not pin:

        return jsonify({

            "success": False,

            "authenticated": False,

            "error":
                "PIN is required."

        }), 400


    result = auth_manager.verify_pin(
        farmer_id,
        pin
    )


    if not result.get(
        "authenticated",
        False
    ):

        return jsonify(
            result
        ), 401


    session.clear()

    session["farmer_id"] = (
        result["farmer_id"]
    )

    session["farmer_name"] = (
        result.get(
            "farmer_name",
            "Farmer"
        )
    )

    session["login_time"] = (
        result.get(
            "login_time"
        )
    )


    return jsonify({

        "success": True,

        "authenticated": True,

        "farmer_id":
            result["farmer_id"],

        "farmer_name":
            result.get(
                "farmer_name",
                "Farmer"
            ),

        "message":
            "Login successful."

    })


# ==========================================================
# FARMER LOGOUT
# ==========================================================

@app.route(
    "/api/auth/logout",
    methods=["POST"]
)
def farmer_logout():

    session.clear()

    return jsonify({

        "success": True,

        "authenticated": False,

        "message":
            "Farmer logged out successfully."

    })


# ==========================================================
# AUTHENTICATION STATUS
# ==========================================================

@app.route(
    "/api/auth/status"
)
def auth_status():

    farmer_id = session.get(
        "farmer_id"
    )

    if not farmer_id:

        return jsonify({

            "authenticated": False,

            "farmer_id": None

        })


    login_time = session.get(
        "login_time"
    )


    if login_time:

        if not auth_manager.is_session_valid(
            login_time
        ):

            session.clear()

            return jsonify({

                "authenticated": False,

                "farmer_id": None,

                "error":
                    "Session expired."

            })


    return jsonify({

        "authenticated": True,

        "farmer_id":
            farmer_id,

        "farmer_name":
            session.get(
                "farmer_name",
                "Farmer"
            )

    })


# ==========================================================
# GET INSURANCE PRODUCTS
# ==========================================================

@app.route(
    "/api/products"
)
def get_products():

    products = (
        policy_engine
        .get_active_products()
    )

    return jsonify({

        "success": True,

        "products": products

    })


# ==========================================================
# EVALUATE POLICY
# ==========================================================

@app.route(
    "/api/policy/evaluate",
    methods=["POST"]
)
def evaluate_policy():

    data = request.get_json() or {}

    product_code = data.get(
        "product_code"
    )

    rainfall_mm = data.get(
        "rainfall_mm"
    )


    if product_code is None:

        return jsonify({

            "success": False,

            "error":
                "Product code is required."

        }), 400


    if rainfall_mm is None:

        return jsonify({

            "success": False,

            "error":
                "Rainfall amount is required."

        }), 400


    try:

        rainfall_mm = float(
            rainfall_mm
        )

    except (
        ValueError,
        TypeError
    ):

        return jsonify({

            "success": False,

            "error":
                "Rainfall must be a number."

        }), 400


    result = (
        policy_engine
        .evaluate_policy(
            product_code,
            rainfall_mm
        )
    )


    return jsonify(
        result
    )


# ==========================================================
# FARMER POLICY CHECK
# ==========================================================

@app.route(
    "/api/farmer/check-policy",
    methods=["POST"]
)
def farmer_check_policy():

    farmer_id = session.get(
        "farmer_id"
    )


    if not farmer_id:

        return jsonify({

            "success": False,

            "error":
                "Authentication required."

        }), 401


    login_time = session.get(
        "login_time"
    )


    if login_time:

        if not auth_manager.is_session_valid(
            login_time
        ):

            session.clear()

            return jsonify({

                "success": False,

                "error":
                    "Session expired. "
                    "Please login again."

            }), 401


    data = request.get_json() or {}

    product_code = data.get(
        "product_code"
    )

    rainfall_mm = data.get(
        "rainfall_mm"
    )


    if not product_code:

        return jsonify({

            "success": False,

            "error":
                "Product code is required."

        }), 400


    if rainfall_mm is None:

        return jsonify({

            "success": False,

            "error":
                "Rainfall amount is required."

        }), 400


    try:

        rainfall_mm = float(
            rainfall_mm
        )

    except (
        ValueError,
        TypeError
    ):

        return jsonify({

            "success": False,

            "error":
                "Rainfall must be a number."

        }), 400


    result = (
        policy_engine
        .evaluate_policy(
            product_code,
            rainfall_mm
        )
    )


    return jsonify({

        "success": True,

        "farmer_id":
            farmer_id,

        "result":
            result

    })


# ==========================================================
# WALLET BALANCE
# ==========================================================

@app.route(
    "/api/farmer/wallet",
    methods=["GET"]
)
def farmer_wallet():

    farmer_id = session.get(
        "farmer_id"
    )


    if not farmer_id:

        return jsonify({

            "success": False,

            "error":
                "Authentication required."

        }), 401


    summary = wallet_service.summary(
        farmer_id
    )


    return jsonify({

        "success": True,

        "wallet":
            summary

    })


# ==========================================================
# WALLET BALANCE ONLY
# ==========================================================

@app.route(
    "/api/farmer/wallet/balance",
    methods=["GET"]
)
def farmer_wallet_balance():

    farmer_id = session.get(
        "farmer_id"
    )


    if not farmer_id:

        return jsonify({

            "success": False,

            "error":
                "Authentication required."

        }), 401


    balance = wallet_service.get_balance(
        farmer_id
    )


    return jsonify({

        "success": True,

        "farmer_id":
            farmer_id,

        "balance":
            balance

    })


# ==========================================================
# OFFLINE WALLET SPEND
# ==========================================================

@app.route(
    "/api/farmer/wallet/spend",
    methods=["POST"]
)
def wallet_spend():

    farmer_id = session.get(
        "farmer_id"
    )


    if not farmer_id:

        return jsonify({

            "success": False,

            "error":
                "Authentication required."

        }), 401


    data = request.get_json() or {}

    amount = data.get(
        "amount"
    )


    if amount is None:

        return jsonify({

            "success": False,

            "error":
                "Amount is required."

        }), 400


    try:

        amount = float(
            amount
        )

    except (
        ValueError,
        TypeError
    ):

        return jsonify({

            "success": False,

            "error":
                "Amount must be a number."

        }), 400


    try:

        result = wallet_service.spend(
            farmer_id,
            amount
        )


        return jsonify({

            "success": True,

            "wallet":
                result

        })


    except ValueError as error:

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 400


# ==========================================================
# GET PENDING SYNCHRONIZATION
# ==========================================================

@app.route(
    "/api/farmer/sync/pending",
    methods=["GET"]
)
def pending_sync():

    farmer_id = session.get(
        "farmer_id"
    )


    if not farmer_id:

        return jsonify({

            "success": False,

            "error":
                "Authentication required."

        }), 401


    events = (
        sync_service
        .get_pending_events()
    )


    # Only return this farmer's events

    farmer_events = []


    for event in events:

        try:

            payload = json.loads(
                event["payload"]
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):

            continue


        if payload.get(
            "farmer_id"
        ) == farmer_id:

            farmer_events.append(
                event
            )


    return jsonify({

        "success": True,

        "farmer_id":
            farmer_id,

        "pending_count":
            len(farmer_events),

        "events":
            farmer_events

    })


# ==========================================================
# SYNCHRONIZE FARMER WALLET
# ==========================================================

@app.route(
    "/api/farmer/sync",
    methods=["POST"]
)
def synchronize_farmer():

    farmer_id = session.get(
        "farmer_id"
    )


    if not farmer_id:

        return jsonify({

            "success": False,

            "error":
                "Authentication required."

        }), 401


    events = (
        sync_service
        .get_pending_events()
    )


    farmer_events = []


    for event in events:

        try:

            payload = json.loads(
                event["payload"]
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):

            continue


        if payload.get(
            "farmer_id"
        ) == farmer_id:

            farmer_events.append(
                event
            )


    results = []


    for event in farmer_events:

        result = (
            sync_service
            .process_event(
                event
            )
        )

        results.append(
            result
        )


    synced = sum(

        1
        for result in results

        if result.get(
            "status"
        ) == "SYNCED"

    )


    rejected = sum(

        1
        for result in results

        if result.get(
            "status"
        ) == "REJECTED"

    )


    return jsonify({

        "success": True,

        "farmer_id":
            farmer_id,

        "total":
            len(results),

        "synced":
            synced,

        "rejected":
            rejected,

        "results":
            results

    })


# ==========================================================
# WALLET TRANSACTION HISTORY
# ==========================================================

@app.route(
    "/api/farmer/wallet/transactions",
    methods=["GET"]
)
def wallet_transactions():

    farmer_id = session.get(
        "farmer_id"
    )


    if not farmer_id:

        return jsonify({

            "success": False,

            "error":
                "Authentication required."

        }), 401


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            transaction_id,
            claim_id,
            amount,
            transaction_type,
            sync_status,
            created_at

        FROM wallet_transactions

        WHERE farmer_id = ?

        ORDER BY id DESC
        """,
        (
            farmer_id,
        )
    )


    rows = cursor.fetchall()

    connection.close()


    transactions = [

        dict(row)

        for row in rows

    ]


    return jsonify({

        "success": True,

        "farmer_id":
            farmer_id,

        "transactions":
            transactions

    })


# ==========================================================
# WALLET SYNC STATUS
# ==========================================================

@app.route(
    "/api/farmer/sync/status",
    methods=["GET"]
)
def sync_status():

    farmer_id = session.get(
        "farmer_id"
    )


    if not farmer_id:

        return jsonify({

            "success": False,

            "error":
                "Authentication required."

        }), 401


    events = (
        sync_service
        .get_pending_events()
    )


    pending = 0


    for event in events:

        try:

            payload = json.loads(
                event["payload"]
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):

            continue


        if payload.get(
            "farmer_id"
        ) == farmer_id:

            pending += 1


    return jsonify({

        "success": True,

        "farmer_id":
            farmer_id,

        "pending_sync":
            pending,

        "online":
            True,

        "message":
            "Wallet synchronization status retrieved."

    })


# ==========================================================
# ADMIN
# ==========================================================

@app.route("/admin")
def admin():

    return render_template(
        "admin.html"
    )


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route(
    "/api/health"
)
def health():

    return jsonify({

        "success": True,

        "application":
            "RainGuard",

        "status":
            "running",

        "database":
            "connected"

    })


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )