import json
from pathlib import Path


class PolicyEngine:
    """
    Declarative policy engine for RainGuard.

    Insurance rules are loaded from products.json.
    The payout logic is therefore data-driven rather
    than hard-coded into the application.
    """

    def __init__(self, product_file=None):

        if product_file is None:
            base_dir = Path(__file__).resolve().parent.parent

            product_file = (
                base_dir /
                "data" /
                "products.json"
            )

        self.product_file = Path(product_file)

        self.products = self._load_products()


    # --------------------------------------------------
    # LOAD PRODUCTS
    # --------------------------------------------------

    def _load_products(self):

        if not self.product_file.exists():

            raise FileNotFoundError(
                f"Product configuration not found: "
                f"{self.product_file}"
            )

        with open(
            self.product_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data.get("products", [])


    # --------------------------------------------------
    # GET ALL ACTIVE PRODUCTS
    # --------------------------------------------------

    def get_active_products(self):

        return [
            product
            for product in self.products
            if product.get("active", False)
        ]


    # --------------------------------------------------
    # FIND PRODUCT
    # --------------------------------------------------

    def get_product(self, product_code):

        for product in self.products:

            if product.get("product_code") == product_code:

                return product

        return None


    # --------------------------------------------------
    # CALCULATE PAYOUT
    # --------------------------------------------------

    def evaluate_policy(
        self,
        product_code,
        rainfall_mm
    ):

        product = self.get_product(product_code)

        if product is None:

            return {
                "success": False,
                "error": "Insurance product not found."
            }


        if not product.get("active", False):

            return {
                "success": False,
                "error": "Insurance product is inactive."
            }


        policy = product["policy"]

        payout_config = product["payout"]


        threshold = policy[
            "rainfall_threshold_mm"
        ]

        coverage = payout_config[
            "coverage_amount"
        ]

        percentage = payout_config[
            "payout_percentage"
        ]


        # ------------------------------------------
        # PARAMETRIC TRIGGER
        # ------------------------------------------

        trigger = rainfall_mm < threshold


        # ------------------------------------------
        # PAYOUT CALCULATION
        # ------------------------------------------

        if trigger:

            payout_amount = (
                coverage * percentage / 100
            )

            status = "PAYOUT_TRIGGERED"

            reason = (
                f"Rainfall of {rainfall_mm} mm "
                f"is below the threshold of "
                f"{threshold} mm."
            )

        else:

            payout_amount = 0

            status = "NO_PAYOUT"

            reason = (
                f"Rainfall of {rainfall_mm} mm "
                f"is equal to or above the "
                f"threshold of {threshold} mm."
            )


        return {

            "success": True,

            "product_code":
                product["product_code"],

            "product_name":
                product["product_name"],

            "crop":
                product["crop"],

            "rainfall_mm":
                rainfall_mm,

            "threshold_mm":
                threshold,

            "coverage_amount":
                coverage,

            "payout_percentage":
                percentage,

            "payout_amount":
                payout_amount,

            "status":
                status,

            "reason":
                reason
        }