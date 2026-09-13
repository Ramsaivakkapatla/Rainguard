import hashlib
import secrets
import time


class DeviceSecurity:
    """
    Shared-device trust boundary.

    Protects:
    - farmer identity
    - wallet access
    - policy binding
    - payout authorization

    The device stores only a hashed PIN.
    """

    SESSION_TIMEOUT = 300


    def __init__(self):

        self._users = {}

        self._sessions = {}


    # ========================================================
    # REGISTER FARMER
    # ========================================================

    def register_farmer(
        self,
        farmer_id,
        pin
    ):

        if not farmer_id:
            raise ValueError(
                "Farmer ID is required."
            )

        if not pin:
            raise ValueError(
                "PIN is required."
            )

        if farmer_id in self._users:
            raise ValueError(
                "Farmer already registered."
            )

        salt = secrets.token_hex(16)

        password_hash = self._hash_pin(
            pin,
            salt
        )

        self._users[farmer_id] = {

            "salt": salt,

            "pin_hash": password_hash
        }

        return True


    # ========================================================
    # HASH PIN
    # ========================================================

    def _hash_pin(
        self,
        pin,
        salt
    ):

        return hashlib.sha256(
            (
                salt + str(pin)
            ).encode("utf-8")
        ).hexdigest()


    # ========================================================
    # LOGIN
    # ========================================================

    def login(
        self,
        farmer_id,
        pin
    ):

        user = self._users.get(
            farmer_id
        )

        if user is None:

            return {
                "success": False,
                "reason": "Unknown farmer"
            }


        calculated_hash = (
            self._hash_pin(
                pin,
                user["salt"]
            )
        )


        if calculated_hash != user[
            "pin_hash"
        ]:

            return {
                "success": False,
                "reason": "Invalid PIN"
            }


        session_token = (
            secrets.token_urlsafe(24)
        )


        self._sessions[
            session_token
        ] = {

            "farmer_id":
                farmer_id,

            "created_at":
                time.time()
        }


        return {

            "success": True,

            "session_token":
                session_token,

            "farmer_id":
                farmer_id
        }


    # ========================================================
    # VALIDATE SESSION
    # ========================================================

    def validate_session(
        self,
        session_token,
        farmer_id
    ):

        session = self._sessions.get(
            session_token
        )

        if session is None:

            return False


        # ----------------------------------------------------
        # Check session timeout
        # ----------------------------------------------------

        age = (
            time.time()
            - session["created_at"]
        )


        if age > self.SESSION_TIMEOUT:

            self.logout(
                session_token
            )

            return False


        # ----------------------------------------------------
        # CRITICAL TRUST BOUNDARY
        # ----------------------------------------------------

        return (
            session["farmer_id"]
            == farmer_id
        )


    # ========================================================
    # AUTHORIZE WALLET
    # ========================================================

    def authorize_wallet(
        self,
        session_token,
        farmer_id
    ):

        if not self.validate_session(
            session_token,
            farmer_id
        ):

            raise PermissionError(
                "Wallet access denied."
            )

        return True


    # ========================================================
    # AUTHORIZE POLICY BINDING
    # ========================================================

    def authorize_policy_binding(
        self,
        session_token,
        farmer_id
    ):

        if not self.validate_session(
            session_token,
            farmer_id
        ):

            raise PermissionError(
                "Policy binding denied."
            )

        return True


    # ========================================================
    # AUTHORIZE PAYOUT
    # ========================================================

    def authorize_payout(
        self,
        session_token,
        farmer_id
    ):

        if not self.validate_session(
            session_token,
            farmer_id
        ):

            raise PermissionError(
                "Payout access denied."
            )

        return True


    # ========================================================
    # LOGOUT
    # ========================================================

    def logout(
        self,
        session_token
    ):

        self._sessions.pop(
            session_token,
            None
        )

        return True


    # ========================================================
    # LOGOUT ALL
    # ========================================================

    def logout_all(self):

        self._sessions.clear()

        return True