from datetime import datetime
import uuid


class SettlementEngine:
    """
    Settlement engine for RainGuard.

    Responsible for:
    - Receiving verified oracle results
    - Evaluating the insurance policy
    - Triggering or rejecting payouts
    - Creating an explainable settlement record

    Important:
    The engine NEVER settles a claim when the
    oracle result is disputed or insufficient.
    """

    def __init__(self, policy_engine):

        self.policy_engine = policy_engine


    # ==================================================
    # CREATE SETTLEMENT ID
    # ==================================================

    def _generate_settlement_id(self):

        return (
            "SET-"
            + uuid.uuid4().hex[:12].upper()
        )


    # ==================================================
    # SETTLE CLAIM
    # ==================================================

    def settle(
        self,
        oracle_result,
        product_code,
        farmer_id="DEMO-FARMER-001"
    ):

        settlement_time = datetime.now()


        # ==================================================
        # CHECK ORACLE DECISION
        # ==================================================

        oracle_decision = oracle_result.get(
            "decision"
        )


        # --------------------------------------------------
        # DISPUTED DATA
        # --------------------------------------------------

        if oracle_decision == "DISPUTE":

            return {

                "success": False,

                "settlement_id":
                    self._generate_settlement_id(),

                "status":
                    "SETTLEMENT_BLOCKED",

                "payout_amount":
                    0,

                "farmer_id":
                    farmer_id,

                "product_code":
                    product_code,

                "trusted_rainfall_mm":
                    None,

                "reason":
                    "Settlement blocked because "
                    "rainfall sources disagree.",

                "oracle_decision":
                    oracle_decision,

                "settled_at":
                    settlement_time.isoformat()
            }


        # --------------------------------------------------
        # INSUFFICIENT DATA
        # --------------------------------------------------

        if oracle_decision == "INSUFFICIENT_DATA":

            return {

                "success": False,

                "settlement_id":
                    self._generate_settlement_id(),

                "status":
                    "SETTLEMENT_BLOCKED",

                "payout_amount":
                    0,

                "farmer_id":
                    farmer_id,

                "product_code":
                    product_code,

                "trusted_rainfall_mm":
                    None,

                "reason":
                    "Settlement blocked because "
                    "there are not enough valid "
                    "rainfall sources.",

                "oracle_decision":
                    oracle_decision,

                "settled_at":
                    settlement_time.isoformat()
            }


        # --------------------------------------------------
        # UNKNOWN ORACLE RESULT
        # --------------------------------------------------

        if oracle_decision != "TRUSTED":

            return {

                "success": False,

                "settlement_id":
                    self._generate_settlement_id(),

                "status":
                    "SETTLEMENT_BLOCKED",

                "payout_amount":
                    0,

                "farmer_id":
                    farmer_id,

                "product_code":
                    product_code,

                "trusted_rainfall_mm":
                    None,

                "reason":
                    "Settlement blocked because "
                    "rainfall data could not be trusted.",

                "oracle_decision":
                    oracle_decision,

                "settled_at":
                    settlement_time.isoformat()
            }


        # ==================================================
        # GET TRUSTED RAINFALL
        # ==================================================

        trusted_rainfall = oracle_result.get(
            "trusted_rainfall_mm"
        )


        if trusted_rainfall is None:

            return {

                "success": False,

                "settlement_id":
                    self._generate_settlement_id(),

                "status":
                    "SETTLEMENT_BLOCKED",

                "payout_amount":
                    0,

                "farmer_id":
                    farmer_id,

                "product_code":
                    product_code,

                "trusted_rainfall_mm":
                    None,

                "reason":
                    "Trusted rainfall value is missing.",

                "oracle_decision":
                    oracle_decision,

                "settled_at":
                    settlement_time.isoformat()
            }


        # ==================================================
        # RUN POLICY ENGINE
        # ==================================================

        policy_result = (
            self.policy_engine.evaluate_policy(
                product_code,
                trusted_rainfall
            )
        )


        if not policy_result.get("success"):

            return {

                "success": False,

                "settlement_id":
                    self._generate_settlement_id(),

                "status":
                    "SETTLEMENT_BLOCKED",

                "payout_amount":
                    0,

                "farmer_id":
                    farmer_id,

                "product_code":
                    product_code,

                "trusted_rainfall_mm":
                    trusted_rainfall,

                "reason":
                    policy_result.get(
                        "error",
                        "Policy evaluation failed."
                    ),

                "oracle_decision":
                    oracle_decision,

                "settled_at":
                    settlement_time.isoformat()
            }


        # ==================================================
        # PAYOUT TRIGGERED
        # ==================================================

        if policy_result["status"] == "PAYOUT_TRIGGERED":

            payout_amount = (
                policy_result["payout_amount"]
            )

            return {

                "success": True,

                "settlement_id":
                    self._generate_settlement_id(),

                "status":
                    "PAYOUT_SETTLED",

                "payout_amount":
                    payout_amount,

                "currency":
                    "INR",

                "farmer_id":
                    farmer_id,

                "product_code":
                    product_code,

                "product_name":
                    policy_result[
                        "product_name"
                    ],

                "crop":
                    policy_result[
                        "crop"
                    ],

                "trusted_rainfall_mm":
                    trusted_rainfall,

                "threshold_mm":
                    policy_result[
                        "threshold_mm"
                    ],

                "payout_percentage":
                    policy_result[
                        "payout_percentage"
                    ],

                "coverage_amount":
                    policy_result[
                        "coverage_amount"
                    ],

                "oracle_decision":
                    oracle_decision,

                "trusted_sources":
                    oracle_result.get(
                        "trusted_sources",
                        []
                    ),

                "reason":
                    policy_result[
                        "reason"
                    ],

                "settled_at":
                    settlement_time.isoformat()
            }


        # ==================================================
        # NO PAYOUT
        # ==================================================

        return {

            "success": True,

            "settlement_id":
                self._generate_settlement_id(),

            "status":
                "NO_PAYOUT",

            "payout_amount":
                0,

            "currency":
                "INR",

            "farmer_id":
                farmer_id,

            "product_code":
                product_code,

            "product_name":
                policy_result[
                    "product_name"
                ],

            "crop":
                policy_result[
                    "crop"
                ],

            "trusted_rainfall_mm":
                trusted_rainfall,

            "threshold_mm":
                policy_result[
                    "threshold_mm"
                ],

            "oracle_decision":
                oracle_decision,

            "trusted_sources":
                oracle_result.get(
                    "trusted_sources",
                    []
                ),

            "reason":
                policy_result[
                    "reason"
                ],

            "settled_at":
                settlement_time.isoformat()
        }