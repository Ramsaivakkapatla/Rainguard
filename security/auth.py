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

import os
import hashlib
import hmac
import time


class AuthManager:

    # =========================================================
    # CONFIGURATION
    # =========================================================

    MAX_FAILED_ATTEMPTS = 5

    SESSION_TIMEOUT_SECONDS = 10 * 60

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "ramsai016")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "luffyzoro")

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
    # DATABASE LOOKUP
    # =========================================================

    def _lookup_db_farmer(self, farmer_id):
        if not farmer_id:
            return None
        try:
            from database.database import get_farmer
            record = get_farmer(farmer_id)
            if record:
                farmer_data = {
                    "name": record.get("name", "Farmer"),
                    "pin_hash": record.get("pin_hash") or "",
                    "phone": record.get("phone", ""),
                    "location": record.get("location", ""),
                    "crop": record.get("crop", "")
                }
                self.farmers[farmer_id] = farmer_data
                return farmer_data
        except Exception:
            pass
        return None

    # =========================================================
    # ADMIN AUTHENTICATION
    # =========================================================

    @classmethod
    def verify_admin(cls, username, password):
        if not username or not password:
            return False
        user_match = hmac.compare_digest(
            str(username).strip(),
            cls.ADMIN_USERNAME
        )
        pass_match = hmac.compare_digest(
            str(password).strip(),
            cls.ADMIN_PASSWORD
        )
        return user_match and pass_match

    # =========================================================
    # REGISTER FARMER
    # =========================================================

    def register_farmer(
        self,
        farmer_id,
        name,
        pin,
        phone="",
        location="Demo District",
        crop="Rice"
    ):
        if not farmer_id:
            return {
                "success": False,
                "error": "Farmer ID is required."
            }

        farmer_id = str(farmer_id).strip()

        if not name or not str(name).strip():
            return {
                "success": False,
                "error": "Farmer name is required."
            }

        name = str(name).strip()

        if self.farmer_exists(farmer_id):
            return {
                "success": False,
                "error": f"Farmer ID '{farmer_id}' is already registered."
            }

        pin_str = str(pin or "").strip()
        if not pin_str.isdigit():
            return {
                "success": False,
                "error": "PIN must contain numbers only."
            }

        if len(pin_str) != 4:
            return {
                "success": False,
                "error": "PIN must contain exactly 4 digits."
            }

        hashed = self.hash_pin(pin_str)

        self.farmers[farmer_id] = {
            "name": name,
            "pin_hash": hashed,
            "phone": phone,
            "location": location,
            "crop": crop
        }

        try:
            from database.database import save_farmer
            save_farmer(
                farmer_id=farmer_id,
                name=name,
                phone=phone,
                location=location,
                crop=crop,
                pin_hash=hashed
            )
        except Exception as error:
            return {
                "success": False,
                "error": f"Failed to save farmer record: {error}"
            }

        return {
            "success": True,
            "farmer_id": farmer_id,
            "name": name,
            "message": "Farmer registered successfully."
        }

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

        if not farmer_id:
            return False

        if farmer_id in self.farmers:
            return True

        return self._lookup_db_farmer(farmer_id) is not None

    # =========================================================
    # GET FARMER
    # =========================================================

    def get_farmer(self, farmer_id):

        if not farmer_id:
            return None

        return self.farmers.get(
            farmer_id
        ) or self._lookup_db_farmer(farmer_id)

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
            db_farmer = self._lookup_db_farmer(farmer_id)
            if not db_farmer:
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