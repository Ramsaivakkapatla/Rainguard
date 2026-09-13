import uuid
import json

from database.database import (
    save_audit_record,
    get_audit_records,
    get_claim,
    get_rainfall_evidence
)


class AuditEngine:
    """
    RainGuard Audit and Reconstruction Engine.

    Creates a permanent explanation of:

    - What happened
    - Which farmer/policy was involved
    - Which rainfall data was used
    - Which oracle sources were trusted
    - When the data was recorded
    - What decision was made
    - How much was paid
    """


    # ========================================================
    # GENERATE AUDIT ID
    # ========================================================

    def _generate_audit_id(self):

        return (
            "AUD-"
            + uuid.uuid4().hex[:12].upper()
        )


    # ========================================================
    # RECORD SETTLEMENT
    # ========================================================

    def record_settlement(
        self,
        settlement,
        oracle_result
    ):

        audit_id = (
            self._generate_audit_id()
        )


        # ----------------------------------------------------
        # Extract rainfall source information
        # ----------------------------------------------------

        sources = oracle_result.get(
            "sources",
            []
        )


        # ----------------------------------------------------
        # Create reconstruction data
        # ----------------------------------------------------

        reconstruction = {

            "settlement_id":
                settlement.get(
                    "settlement_id"
                ),

            "farmer_id":
                settlement.get(
                    "farmer_id"
                ),

            "product_code":
                settlement.get(
                    "product_code"
                ),

            "status":
                settlement.get(
                    "status"
                ),

            "payout_amount":
                settlement.get(
                    "payout_amount",
                    0
                ),

            "trusted_rainfall_mm":
                settlement.get(
                    "trusted_rainfall_mm"
                ),

            "threshold_mm":
                settlement.get(
                    "threshold_mm"
                ),

            "oracle_decision":
                settlement.get(
                    "oracle_decision"
                ),

            "reason":
                settlement.get(
                    "reason"
                ),

            "trusted_sources":
                settlement.get(
                    "trusted_sources",
                    []
                ),

            "rainfall_sources":
                sources,

            "settled_at":
                settlement.get(
                    "settled_at"
                )
        }


        # ----------------------------------------------------
        # Save audit record
        # ----------------------------------------------------

        save_audit_record(

            audit_id=audit_id,

            claim_id=settlement.get(
                "claim_id"
            ),

            event_type="SETTLEMENT_RECONSTRUCTION",

            event_data=reconstruction
        )


        return audit_id


    # ========================================================
    # GET RECONSTRUCTION
    # ========================================================

    def reconstruct(
        self,
        claim_id
    ):

        claim = get_claim(
            claim_id
        )

        audit_records = (
            get_audit_records(
                claim_id
            )
        )


        return {

            "claim": claim,

            "audit_records":
                audit_records,

            "reconstructed":
                claim is not None
                and len(audit_records) > 0
        }


    # ========================================================
    # EXPLAIN DECISION
    # ========================================================

    def explain(
        self,
        claim_id
    ):

        reconstruction = (
            self.reconstruct(
                claim_id
            )
        )


        if not reconstruction[
            "reconstructed"
        ]:

            return (
                "No reconstruction data "
                "is available for this claim."
            )


        claim = reconstruction[
            "claim"
        ]


        rainfall = claim.get(
            "trusted_rainfall_mm"
        )

        threshold = claim.get(
            "threshold_mm"
        )

        payout = claim.get(
            "payout_amount",
            0
        )

        status = claim.get(
            "status"
        )

        reason = claim.get(
            "reason"
        )


        if status == "PAYOUT_SETTLED":

            return (
                f"Payout of ₹{payout:.0f} "
                f"was triggered because trusted "
                f"rainfall was {rainfall} mm, "
                f"below the policy threshold "
                f"of {threshold} mm. "
                f"Reason: {reason}"
            )


        if status == "NO_PAYOUT":

            return (
                f"No payout was triggered. "
                f"Trusted rainfall was "
                f"{rainfall} mm and the policy "
                f"threshold was {threshold} mm. "
                f"Reason: {reason}"
            )


        return (
            f"Settlement status: {status}. "
            f"Reason: {reason}"
        )


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":

    audit_engine = AuditEngine()

    print(
        "RainGuard Audit Engine ready."
    )