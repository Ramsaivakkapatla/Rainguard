import os
import json
import uuid

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session
)

from engine.policy_engine import PolicyEngine
from engine.oracle_engine import OracleEngine
from engine.settlement_engine import SettlementEngine
from security.auth import AuthManager

from services.wallet_service import OfflineWallet
from services.sync_service import SyncService

from database.database import (
    initialize_database,
    get_connection,
    save_farmer,
    save_claim,
    save_audit_record
)


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "RAINGUARD-HACKATHON-DEMO-SECRET-CHANGE-ME"
)

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
oracle_engine = OracleEngine()
settlement_engine = SettlementEngine(policy_engine)
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

    data = request.get_json(
        silent=True
    ) or {}

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
            "error": "Farmer ID is required."
        }), 400

    if not pin:

        return jsonify({
            "success": False,
            "authenticated": False,
            "error": "PIN is required."
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

    try:

        products = (
            policy_engine
            .get_active_products()
        )

        return jsonify({

            "success": True,

            "products":
                products

        })

    except Exception as error:

        app.logger.exception(
            "Failed to load insurance products."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# ==========================================================
# RAINFALL ORACLE
# ==========================================================

@app.route(
    "/api/oracle/evaluate",
    methods=["GET"]
)
def evaluate_oracle():

    try:

        result = (
            oracle_engine
            .evaluate()
        )

        return jsonify({

            "success": True,

            "oracle":
                result

        }), 200

    except FileNotFoundError as error:

        app.logger.exception(
            "Oracle data file not found."
        )

        return jsonify({

            "success": False,

            "error":
                str(error),

            "oracle":
                None

        }), 500

    except json.JSONDecodeError as error:

        app.logger.exception(
            "Oracle JSON file is invalid."
        )

        return jsonify({

            "success": False,

            "error":
                "Oracle data JSON is invalid: "
                + str(error),

            "oracle":
                None

        }), 500

    except Exception as error:

        app.logger.exception(
            "Oracle evaluation failed."
        )

        return jsonify({

            "success": False,

            "error":
                str(error),

            "oracle":
                None

        }), 500


# ==========================================================
# ORACLE DATA PREVIEW
# ==========================================================

@app.route(
    "/api/oracle/sources",
    methods=["GET"]
)
def oracle_sources():

    try:

        result = (
            oracle_engine
            .evaluate()
        )

        return jsonify({

            "success": True,

            "sources":
                result.get(
                    "sources",
                    []
                ),

            "oracle":
                result

        }), 200

    except Exception as error:

        app.logger.exception(
            "Failed to load oracle sources."
        )

        return jsonify({

            "success": False,

            "sources": [],

            "error":
                str(error)

        }), 500


# ==========================================================
# EVALUATE POLICY
# ==========================================================

@app.route(
    "/api/policy/evaluate",
    methods=["POST"]
)
def evaluate_policy():

    data = request.get_json(
        silent=True
    ) or {}

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

    try:

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

    except Exception as error:

        app.logger.exception(
            "Policy evaluation failed."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


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

    data = request.get_json(
        silent=True
    ) or {}

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

    try:

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

    except Exception as error:

        app.logger.exception(
            "Farmer policy evaluation failed."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# ==========================================================
# ACTIVATE FARMER INSURANCE POLICY
# ==========================================================

@app.route(
    "/api/farmer/activate-policy",
    methods=["POST"]
)
def activate_farmer_policy():

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


    data = request.get_json(
        silent=True
    ) or {}

    product_code = data.get(
        "product_code"
    )


    if not product_code:

        product_code = "RG-MONSOON-001"


    try:

        selected_product = (
            policy_engine
            .get_product(
                product_code
            )
        )

    except Exception as error:

        app.logger.exception(
            "Failed to find insurance product."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


    if selected_product is None:

        return jsonify({

            "success": False,

            "error":
                f"Insurance product "
                f"'{product_code}' was not found."

        }), 404


    if not selected_product.get(
        "active",
        False
    ):

        return jsonify({

            "success": False,

            "error":
                "Insurance product is inactive."

        }), 400


    # ======================================================
    # EXTRACT VALUES FROM products.json
    # ======================================================

    policy_config = (
        selected_product.get(
            "policy",
            {}
        )
    )

    payout_config = (
        selected_product.get(
            "payout",
            {}
        )
    )


    crop = selected_product.get(
        "crop",
        "Rice"
    )


    if isinstance(
        crop,
        dict
    ):

        crop = crop.get(
            "name",
            "Rice"
        )

    elif isinstance(
        crop,
        list
    ):

        crop = ", ".join(
            str(item)
            for item in crop
        )

    else:

        crop = str(
            crop
        )


    coverage_amount = payout_config.get(
        "coverage_amount",
        10000
    )

    try:

        coverage_amount = float(
            coverage_amount
        )

    except (
        ValueError,
        TypeError
    ):

        coverage_amount = 10000


    premium = selected_product.get(
        "premium",
        300
    )

    if premium is None:

        premium = policy_config.get(
            "premium",
            300
        )

    try:

        premium = float(
            premium
        )

    except (
        ValueError,
        TypeError
    ):

        premium = 300


    threshold_mm = policy_config.get(
        "rainfall_threshold_mm",
        60
    )

    try:

        threshold_mm = float(
            threshold_mm
        )

    except (
        ValueError,
        TypeError
    ):

        threshold_mm = 60


    measurement_period_days = (
        policy_config.get(
            "measurement_period_days",
            selected_product.get(
                "measurement_period_days",
                30
            )
        )
    )

    try:

        measurement_period_days = int(
            measurement_period_days
        )

    except (
        ValueError,
        TypeError
    ):

        measurement_period_days = 30


    condition = selected_product.get(
        "condition"
    )

    if not condition:

        condition = (
            f"Rainfall below "
            f"{threshold_mm:g} mm"
        )


    # ======================================================
    # CHECK FARMER EXISTS
    # ======================================================

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM farmers
            WHERE farmer_id = ?
            LIMIT 1
            """,
            (
                farmer_id,
            )
        )

        farmer_record = cursor.fetchone()

    finally:

        connection.close()


    if farmer_record is None:

        try:

            save_farmer(

                farmer_id=farmer_id,

                name=session.get(
                    "farmer_name",
                    "Demo Farmer"
                ),

                phone="",

                location="Demo District",

                crop=crop

            )

        except Exception as error:

            app.logger.exception(
                "Failed to create farmer record."
            )

            return jsonify({

                "success": False,

                "error":
                    "Unable to register farmer: "
                    + str(error)

            }), 500


    # ======================================================
    # CHECK EXISTING ACTIVE POLICY
    # ======================================================

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM policies
            WHERE farmer_id = ?
            AND product_code = ?
            AND status = 'ACTIVE'
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                farmer_id,
                product_code
            )
        )

        existing_policy = (
            cursor.fetchone()
        )

    finally:

        connection.close()


    if existing_policy:

        return jsonify({

            "success": True,

            "already_active": True,

            "message":
                "Insurance policy is already active.",

            "policy":
                dict(existing_policy),

            "details": {

                "threshold_mm":
                    threshold_mm,

                "measurement_period_days":
                    measurement_period_days,

                "condition":
                    condition,

                "crop":
                    crop

            }

        })


    # ======================================================
    # GENERATE POLICY ID
    # ======================================================

    policy_id = (
        "POL-"
        + uuid.uuid4().hex[:12].upper()
    )


    # ======================================================
    # SAVE POLICY
    # ======================================================

    connection = get_connection()

    try:

        connection.execute(
            """
            INSERT INTO policies
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
                "ACTIVE"
            )
        )

        connection.commit()

    except Exception as error:

        connection.rollback()

        app.logger.exception(
            "Policy activation failed."
        )

        return jsonify({

            "success": False,

            "error":
                "Policy activation failed: "
                + str(error)

        }), 500

    finally:

        connection.close()


    return jsonify({

        "success": True,

        "already_active": False,

        "message":
            "Insurance policy activated successfully.",

        "policy": {

            "policy_id":
                policy_id,

            "farmer_id":
                farmer_id,

            "product_code":
                product_code,

            "product_name":
                selected_product.get(
                    "product_name",
                    "RainGuard Monsoon Protection"
                ),

            "crop":
                crop,

            "coverage_amount":
                coverage_amount,

            "premium":
                premium,

            "status":
                "ACTIVE",

            "threshold_mm":
                threshold_mm,

            "measurement_period_days":
                measurement_period_days,

            "condition":
                condition,

            "payout_percentage":
                payout_config.get(
                    "payout_percentage",
                    80
                )

        }

    })


# ==========================================================
# AUTOMATIC SETTLEMENT
# ==========================================================

@app.route(
    "/api/farmer/settle",
    methods=["POST"]
)
def farmer_settle():

    # ------------------------------------------------------
    # CHECK LOGIN
    # ------------------------------------------------------

    farmer_id = session.get(
        "farmer_id"
    )

    if not farmer_id:

        return jsonify({

            "success": False,

            "error":
                "Authentication required."

        }), 401


    # ------------------------------------------------------
    # CHECK SESSION
    # ------------------------------------------------------

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


    # ------------------------------------------------------
    # READ REQUEST
    # ------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    product_code = data.get(
        "product_code"
    )

    if not product_code:

        product_code = "RG-MONSOON-001"


    # ======================================================
    # FIND ACTIVE POLICY
    # ======================================================

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM policies
            WHERE farmer_id = ?
            AND product_code = ?
            AND status = 'ACTIVE'
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                farmer_id,
                product_code
            )
        )

        policy_record = cursor.fetchone()

    finally:

        connection.close()


    if policy_record is None:

        return jsonify({

            "success": False,

            "error":
                "No active insurance policy found. "
                "Please activate a policy first."

        }), 404


    policy_record = dict(
        policy_record
    )


    # ======================================================
    # DUPLICATE PAYOUT PROTECTION
    # ======================================================

    # One active demo policy should not receive
    # the same automatic payout multiple times.

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM claims
            WHERE policy_id = ?
            AND farmer_id = ?
            AND status IN (
                'PAYOUT_SETTLED',
                'PAYOUT_CREDITED'
            )
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                policy_record["policy_id"],
                farmer_id
            )
        )

        previous_payout = cursor.fetchone()

    finally:

        connection.close()


    if previous_payout:

        previous_payout = dict(
            previous_payout
        )

        wallet_balance = (
            wallet_service
            .get_balance(
                farmer_id
            )
        )

        return jsonify({

            "success": True,

            "already_settled": True,

            "message":
                "This active policy has already received "
                "an automatic payout.",

            "claim":
                previous_payout,

            "wallet": {

                "balance":
                    wallet_balance

            }

        })


    # ======================================================
    # RUN MULTI-ORACLE ENGINE
    # ======================================================

    try:

        oracle_result = (
            oracle_engine
            .evaluate()
        )

    except Exception as error:

        app.logger.exception(
            "Oracle evaluation failed during settlement."
        )

        return jsonify({

            "success": False,

            "error":
                "Oracle evaluation failed: "
                + str(error)

        }), 500


    # ======================================================
    # ORACLE MUST BE TRUSTED
    # ======================================================

    oracle_decision = oracle_result.get(
        "decision"
    )

    if oracle_decision != "TRUSTED":

        return jsonify({

            "success": False,

            "settlement_blocked": True,

            "message":
                "Automatic settlement blocked because "
                "rainfall data is not trusted.",

            "oracle":
                oracle_result,

            "settlement": {

                "status":
                    "SETTLEMENT_BLOCKED",

                "payout_amount":
                    0,

                "oracle_decision":
                    oracle_decision

            }

        }), 200


    # ======================================================
    # RUN SETTLEMENT ENGINE
    # ======================================================

    try:

        settlement_result = (
            settlement_engine
            .settle(
                oracle_result=oracle_result,

                product_code=product_code,

                farmer_id=farmer_id
            )
        )

    except Exception as error:

        app.logger.exception(
            "Settlement engine failed."
        )

        return jsonify({

            "success": False,

            "error":
                "Settlement engine failed: "
                + str(error)

        }), 500


    # ======================================================
    # SETTLEMENT BLOCKED
    # ======================================================

    if settlement_result.get(
        "status"
    ) == "SETTLEMENT_BLOCKED":

        return jsonify({

            "success": False,

            "settlement_blocked": True,

            "oracle":
                oracle_result,

            "settlement":
                settlement_result

        }), 200


    # ======================================================
    # CREATE CLAIM ID
    # ======================================================

    claim_id = (
        "CLM-"
        + uuid.uuid4().hex[:12].upper()
    )


    settlement_id = settlement_result.get(
        "settlement_id"
    )

    payout_amount = float(
        settlement_result.get(
            "payout_amount",
            0
        )
    )

    trusted_rainfall = settlement_result.get(
        "trusted_rainfall_mm"
    )

    threshold_mm = settlement_result.get(
        "threshold_mm"
    )

    settlement_status = settlement_result.get(
        "status"
    )


    # ======================================================
    # NO PAYOUT
    # ======================================================

    if settlement_status == "NO_PAYOUT":

        try:

            save_claim(

                claim_id=claim_id,

                policy_id=policy_record["policy_id"],

                farmer_id=farmer_id,

                trusted_rainfall_mm=trusted_rainfall,

                threshold_mm=threshold_mm,

                payout_amount=0,

                status="NO_PAYOUT",

                reason=settlement_result.get(
                    "reason",
                    "Rainfall did not trigger payout."
                ),

                settlement_id=settlement_id

            )

            save_audit_record(

                audit_id=(
                    "AUD-"
                    + uuid.uuid4().hex[:12].upper()
                ),

                claim_id=claim_id,

                event_type="SETTLEMENT_COMPLETED",

                event_data={

                    "farmer_id":
                        farmer_id,

                    "policy_id":
                        policy_record["policy_id"],

                    "product_code":
                        product_code,

                    "oracle_decision":
                        oracle_decision,

                    "trusted_rainfall_mm":
                        trusted_rainfall,

                    "threshold_mm":
                        threshold_mm,

                    "payout_amount":
                        0,

                    "status":
                        "NO_PAYOUT"

                }

            )

        except Exception as error:

            app.logger.exception(
                "Failed to save no-payout claim."
            )

            return jsonify({

                "success": False,

                "error":
                    "Settlement completed but claim "
                    "record could not be saved: "
                    + str(error),

                "settlement":
                    settlement_result

            }), 500


        return jsonify({

            "success": True,

            "already_settled": False,

            "message":
                "Settlement evaluated successfully. "
                "No payout was triggered.",

            "oracle":
                oracle_result,

            "settlement":
                settlement_result,

            "claim": {

                "claim_id":
                    claim_id,

                "status":
                    "NO_PAYOUT",

                "payout_amount":
                    0

            }

        })


    # ======================================================
    # PAYOUT SETTLED
    # ======================================================

    if settlement_status != "PAYOUT_SETTLED":

        return jsonify({

            "success": False,

            "error":
                "Unexpected settlement status.",

            "oracle":
                oracle_result,

            "settlement":
                settlement_result

        }), 500


    if payout_amount <= 0:

        return jsonify({

            "success": False,

            "error":
                "Invalid payout amount generated by settlement engine."

        }), 500


    # ======================================================
    # SAVE CLAIM
    # ======================================================

    try:

        save_claim(

            claim_id=claim_id,

            policy_id=policy_record["policy_id"],

            farmer_id=farmer_id,

            trusted_rainfall_mm=trusted_rainfall,

            threshold_mm=threshold_mm,

            payout_amount=payout_amount,

            status="PAYOUT_SETTLED",

            reason=settlement_result.get(
                "reason",
                "Rainfall trigger satisfied."
            ),

            settlement_id=settlement_id

        )

    except Exception as error:

        app.logger.exception(
            "Failed to save payout claim."
        )

        return jsonify({

            "success": False,

            "error":
                "Payout was calculated but the claim "
                "could not be saved: "
                + str(error),

            "settlement":
                settlement_result

        }), 500


    # ======================================================
    # CREDIT OFFLINE WALLET
    # ======================================================

    try:

        wallet_result = (
            wallet_service
            .credit_payout(

                farmer_id=farmer_id,

                claim_id=claim_id,

                amount=payout_amount

            )
        )

    except Exception as error:

        app.logger.exception(
            "Wallet payout credit failed."
        )

        return jsonify({

            "success": False,

            "error":
                "Claim was created but wallet credit failed: "
                + str(error),

            "claim_id":
                claim_id,

            "settlement":
                settlement_result

        }), 500


    # ======================================================
    # SAVE AUDIT RECORD
    # ======================================================

    try:

        audit_id = (
            "AUD-"
            + uuid.uuid4().hex[:12].upper()
        )

        save_audit_record(

            audit_id=audit_id,

            claim_id=claim_id,

            event_type="PAYOUT_CREDITED",

            event_data={

                "farmer_id":
                    farmer_id,

                "policy_id":
                    policy_record["policy_id"],

                "product_code":
                    product_code,

                "settlement_id":
                    settlement_id,

                "claim_id":
                    claim_id,

                "oracle_decision":
                    oracle_decision,

                "trusted_rainfall_mm":
                    trusted_rainfall,

                "threshold_mm":
                    threshold_mm,

                "payout_amount":
                    payout_amount,

                "wallet_transaction_id":
                    wallet_result.get(
                        "transaction_id"
                    ),

                "wallet_balance":
                    wallet_result.get(
                        "balance"
                    )

            }

        )

    except Exception as error:

        app.logger.exception(
            "Audit record creation failed."
        )

        # Settlement and wallet credit already succeeded.
        # We do not reverse the payout just because
        # audit logging failed.

        return jsonify({

            "success": True,

            "warning":
                "Payout completed but audit record "
                "could not be created.",

            "oracle":
                oracle_result,

            "settlement":
                settlement_result,

            "claim": {

                "claim_id":
                    claim_id,

                "status":
                    "PAYOUT_CREDITED",

                "payout_amount":
                    payout_amount

            },

            "wallet":
                wallet_result

        })


    # ======================================================
    # FINAL SUCCESS RESPONSE
    # ======================================================

    return jsonify({

        "success": True,

        "already_settled": False,

        "message":
            "Automatic settlement completed successfully.",

        "oracle": {

            "decision":
                oracle_result.get(
                    "decision"
                ),

            "trusted_rainfall_mm":
                oracle_result.get(
                    "trusted_rainfall_mm"
                ),

            "valid_sources":
                oracle_result.get(
                    "valid_sources"
                ),

            "required_sources":
                oracle_result.get(
                    "required_sources"
                ),

            "reason":
                oracle_result.get(
                    "reason"
                ),

            "sources":
                oracle_result.get(
                    "sources",
                    []
                )

        },

        "settlement":
            settlement_result,

        "claim": {

            "claim_id":
                claim_id,

            "settlement_id":
                settlement_id,

            "status":
                "PAYOUT_CREDITED",

            "payout_amount":
                payout_amount

        },

        "wallet":
            wallet_result,

        "audit": {

            "status":
                "RECORDED",

            "event":
                "PAYOUT_CREDITED"

        }

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

    try:

        summary = wallet_service.summary(
            farmer_id
        )

        return jsonify({

            "success": True,

            "wallet":
                summary

        })

    except Exception as error:

        app.logger.exception(
            "Wallet summary failed."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


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

    try:

        balance = (
            wallet_service
            .get_balance(
                farmer_id
            )
        )

        return jsonify({

            "success": True,

            "farmer_id":
                farmer_id,

            "balance":
                balance

        })

    except Exception as error:

        app.logger.exception(
            "Wallet balance failed."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


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

    data = request.get_json(
        silent=True
    ) or {}

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

        result = (
            wallet_service
            .spend(
                farmer_id,
                amount
            )
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

    except Exception as error:

        app.logger.exception(
            "Wallet spend failed."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


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

    try:

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

        return jsonify({

            "success": True,

            "farmer_id":
                farmer_id,

            "pending_count":
                len(
                    farmer_events
                ),

            "events":
                farmer_events

        })

    except Exception as error:

        app.logger.exception(
            "Failed to retrieve pending sync events."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


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

    try:

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

    except Exception as error:

        app.logger.exception(
            "Farmer synchronization failed."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


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

    try:

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

    except Exception as error:

        app.logger.exception(
            "Failed to load wallet transactions."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500

    finally:

        connection.close()


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

    try:

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
                "Wallet synchronization "
                "status retrieved."

        })

    except Exception as error:

        app.logger.exception(
            "Failed to get sync status."
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


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
            "connected",

        "oracle":
            "ready",

        "settlement":
            "ready",

        "wallet":
            "ready"

    })


# ==========================================================
# GLOBAL 404 ERROR HANDLER
# ==========================================================

@app.errorhandler(404)
def page_not_found(error):

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success": False,

            "error":
                "API endpoint not found: "
                + request.path

        }), 404

    return (

        render_template(
            "index.html"
        ),

        404

    )


# ==========================================================
# GLOBAL 500 ERROR HANDLER
# ==========================================================

@app.errorhandler(500)
def internal_server_error(error):

    app.logger.exception(
        "Internal server error."
    )

    if request.path.startswith(
        "/api/"
    ):

        return jsonify({

            "success": False,

            "error":
                "Internal server error."

        }), 500

    return (
        "Internal Server Error",
        500
    )


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    host = os.environ.get("HOST", "0.0.0.0")

    debug = os.environ.get(
        "FLASK_DEBUG",
        "false"
    ).lower() in ("true", "1", "t")

    app.run(
        host=host,
        port=port,
        debug=debug
    )