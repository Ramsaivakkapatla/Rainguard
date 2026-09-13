from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session
)

from engine.policy_engine import PolicyEngine
from security.auth import AuthManager


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)

# Session secret for hackathon prototype
app.secret_key = "RAINGUARD-HACKATHON-DEMO-SECRET-CHANGE-ME"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ==========================================================
# ENGINES
# ==========================================================

policy_engine = PolicyEngine()

auth_manager = AuthManager()


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

    # ------------------------------------------------------
    # NOT LOGGED IN
    # ------------------------------------------------------

    if not farmer_id:

        return render_template(
            "farmer_login.html"
        )

    # ------------------------------------------------------
    # LOGGED IN
    # ------------------------------------------------------

    return render_template(
        "farmer.html",
        farmer_id=farmer_id,
        farmer_name=session.get(
            "farmer_name",
            "Farmer"
        )
    )


# ==========================================================
# FARMER LOGIN API
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

    # ------------------------------------------------------
    # BASIC VALIDATION
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # VERIFY FARMER
    # ------------------------------------------------------

    result = auth_manager.verify_pin(
        farmer_id,
        pin
    )

    # ------------------------------------------------------
    # LOGIN FAILED
    # ------------------------------------------------------

    if not result.get(
        "authenticated",
        False
    ):

        return jsonify(
            result
        ), 401

    # ------------------------------------------------------
    # CREATE SESSION
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # NOT AUTHENTICATED
    # ------------------------------------------------------

    if not farmer_id:

        return jsonify({

            "authenticated": False,

            "farmer_id": None
        })


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

                "authenticated": False,

                "farmer_id": None,

                "error":
                    "Session expired."
            })


    # ------------------------------------------------------
    # AUTHENTICATED
    # ------------------------------------------------------

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
# GET PRODUCTS
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

    # ------------------------------------------------------
    # VALIDATE PRODUCT
    # ------------------------------------------------------

    if product_code is None:

        return jsonify({

            "success": False,

            "error":
                "Product code is required."
        }), 400

    # ------------------------------------------------------
    # VALIDATE RAINFALL
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # POLICY ENGINE
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # SECURITY CHECK
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
    # SESSION CHECK
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
    # REQUEST DATA
    # ------------------------------------------------------

    data = request.get_json() or {}

    product_code = data.get(
        "product_code"
    )

    rainfall_mm = data.get(
        "rainfall_mm"
    )

    # ------------------------------------------------------
    # VALIDATE PRODUCT
    # ------------------------------------------------------

    if not product_code:

        return jsonify({

            "success": False,

            "error":
                "Product code is required."
        }), 400

    # ------------------------------------------------------
    # VALIDATE RAINFALL
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # EVALUATE POLICY
    # ------------------------------------------------------

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
# ADMIN
# ==========================================================

@app.route("/admin")
def admin():

    return render_template(
        "admin.html"
    )


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )