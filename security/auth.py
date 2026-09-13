"""
RainGuard Shared-Device Authentication
---------------------------------------

Provides a lightweight authentication layer for the
RainGuard prototype.

Purpose:
- Protect farmer data on a shared phone.
- Prevent unauthorized wallet access.
- Prevent one farmer from accessing another farmer's policy.
- Support PIN-based authentication.
- Provide session timeout and failed-login protection.

Prototype authentication:
    DEMO-FARMER-001 -> PIN 1234
    DEMO-FARMER-002 -> PIN 2345
    DEMO-FARMER-003 -> PIN 3456

These demo credentials are ONLY for the hackathon prototype.
"""

import hashlib
import hmac
import time


class AuthManager:

    # =========================================================
    # CONFIGURATION
    # =========================================================

    MAX_FAILED_ATTEMPTS = 5

    SESSION_TIMEOUT_SECONDS = 10 * 60

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self):

        # Demo farmer credentials.
        #
        # In the production system these would come from
        # a secure database instead of being stored here.

        self.farmers = {

            "DEMO-FARMER-001": {
                "name": "Demo Farmer 1",
                "pin_hash": self.hash_pin("1234"),
            },

            "DEMO-FARMER-002": {
                "name": "Demo Farmer 2",
                "pin_hash": self.hash_pin("2345"),
            },

            "DEMO-FARMER-003": {
                "name": "Demo Farmer 3",
                "pin_hash": self.hash_pin("3456"),
            },
        }

        # Track failed attempts locally.

        self.failed_attempts = {}

    # =========================================================
    # HASH PIN
    # =========================================================

    @staticmethod
    def hash_pin(pin):

        """
        Convert a PIN into a SHA-256 hash.

        We never compare or store the PIN directly.
        """

        if pin is None:

            return ""

        pin = str(pin)

        return hashlib.sha256(
            pin.encode("utf-8")
        ).hexdigest()

    # =========================================================
    # CHECK FARMER EXISTS
    # =========================================================

    def farmer_exists(self, farmer_id):

        return farmer_id in self.farmers

    # =========================================================
    # GET FARMER
    # =========================================================

    def get_farmer(self, farmer_id):

        return self.farmers.get(
            farmer_id
        )

    # =========================================================
    # VERIFY PIN
    # =========================================================

    def verify_pin(
        self,
        farmer_id,
        pin
    ):

        # -----------------------------------------------------
        # Validate farmer
        # -----------------------------------------------------

        if not farmer_id:

            return {
                "success": False,
                "authenticated": False,
                "error": "Farmer ID is required."
            }

        if farmer_id not in self.farmers:

            return {
                "success": False,
                "authenticated": False,
                "error": "Farmer ID not found."
            }

        # -----------------------------------------------------
        # Check failed attempts
        # -----------------------------------------------------

        attempts = self.failed_attempts.get(
            farmer_id,
            0
        )

        if attempts >= self.MAX_FAILED_ATTEMPTS:

            return {
                "success": False,
                "authenticated": False,
                "error":
                    "Too many failed attempts. "
                    "Farmer account is temporarily locked."
            }

        # -----------------------------------------------------
        # Validate PIN format
        # -----------------------------------------------------

        if pin is None:

            return {
                "success": False,
                "authenticated": False,
                "error": "PIN is required."
            }

        pin = str(pin)

        if not pin.isdigit():

            return {
                "success": False,
                "authenticated": False,
                "error": "PIN must contain numbers only."
            }

        if len(pin) != 4:

            return {
                "success": False,
                "authenticated": False,
                "error": "PIN must contain exactly 4 digits."
            }

        # -----------------------------------------------------
        # Hash supplied PIN
        # -----------------------------------------------------

        supplied_hash = self.hash_pin(
            pin
        )

        stored_hash = self.farmers[
            farmer_id
        ]["pin_hash"]

        # -----------------------------------------------------
        # Secure comparison
        # -----------------------------------------------------

        if hmac.compare_digest(
            supplied_hash,
            stored_hash
        ):

            # Reset failed attempts after success.

            self.failed_attempts[
                farmer_id
            ] = 0

            return {

                "success": True,

                "authenticated": True,

                "farmer_id":
                    farmer_id,

                "farmer_name":
                    self.farmers[
                        farmer_id
                    ]["name"],

                "login_time":
                    time.time(),

                "message":
                    "Authentication successful."
            }

        # -----------------------------------------------------
        # Incorrect PIN
        # -----------------------------------------------------

        self.failed_attempts[
            farmer_id
        ] = attempts + 1

        remaining = (
            self.MAX_FAILED_ATTEMPTS
            - self.failed_attempts[farmer_id]
        )

        return {

            "success": False,

            "authenticated": False,

            "error":
                "Incorrect PIN.",

            "remaining_attempts":
                max(remaining, 0)
        }

    # =========================================================
    # CHECK SESSION
    # =========================================================

    def is_session_valid(
        self,
        login_time
    ):

        if login_time is None:

            return False

        current_time = time.time()

        session_age = (
            current_time
            - float(login_time)
        )

        return (
            session_age
            <= self.SESSION_TIMEOUT_SECONDS
        )

    # =========================================================
    # LOGOUT
    # =========================================================

    def logout(self):

        """
        Authentication itself is stateless.

        Flask session data will be cleared by app.py.

        This method exists to provide a clean security
        interface for future expansion.
        """

        return {

            "success": True,

            "authenticated": False,

            "message":
                "Farmer session terminated."
        }

    # =========================================================
    # SECURITY STATUS
    # =========================================================

    def security_status(
        self,
        farmer_id
    ):

        if not farmer_id:

            return {

                "authenticated": False,

                "farmer_id": None
            }

        return {

            "authenticated":
                farmer_id in self.farmers,

            "farmer_id":
                farmer_id
        }