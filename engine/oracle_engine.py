import json
from pathlib import Path
from datetime import datetime


class OracleEngine:
    """
    Multi-oracle rainfall verification engine.

    Purpose:
    - Validate multiple rainfall sources.
    - Detect stale sources.
    - Detect non-responding sources.
    - Detect outliers/manipulated sources.
    - Handle disagreement between sources.
    - Produce a trusted rainfall value.
    - Provide an explainable decision.
    """

    def __init__(self, oracle_file=None):

        if oracle_file is None:

            base_dir = Path(__file__).resolve().parent.parent

            oracle_file = (
                base_dir
                / "data"
                / "oracle_data.json"
            )

        self.oracle_file = Path(oracle_file)

        self.data = self._load_data()

        self.config = self.data.get(
            "oracle_config",
            {}
        )

        self.sources = self.data.get(
            "sources",
            []
        )


    # ==================================================
    # LOAD ORACLE DATA
    # ==================================================

    def _load_data(self):

        if not self.oracle_file.exists():

            raise FileNotFoundError(
                f"Oracle data file not found: "
                f"{self.oracle_file}"
            )

        with open(
            self.oracle_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)


    # ==================================================
    # PARSE TIMESTAMP
    # ==================================================

    def _parse_timestamp(self, timestamp):

        return datetime.fromisoformat(
            timestamp
        )


    # ==================================================
    # CHECK WHETHER SOURCE IS STALE
    # ==================================================

    def _is_stale(
        self,
        source,
        evaluation_time
    ):

        timestamp = self._parse_timestamp(
            source["timestamp"]
        )

        age_hours = (
            evaluation_time - timestamp
        ).total_seconds() / 3600

        stale_limit = self.config.get(
            "stale_after_hours",
            24
        )

        return age_hours > stale_limit


    # ==================================================
    # VALIDATE SOURCES
    # ==================================================

    def validate_sources(
        self,
        evaluation_time
    ):

        validated = []

        for source in self.sources:

            source_copy = source.copy()

            # ------------------------------------------
            # NON-RESPONDING SOURCE
            # ------------------------------------------

            if not source.get(
                "responding",
                False
            ):

                source_copy["status"] = (
                    "NON_RESPONDING"
                )

                validated.append(source_copy)

                continue


            # ------------------------------------------
            # STALE SOURCE
            # ------------------------------------------

            if self._is_stale(
                source,
                evaluation_time
            ):

                source_copy["status"] = "STALE"

                validated.append(source_copy)

                continue


            # ------------------------------------------
            # VALID SOURCE
            # ------------------------------------------

            rainfall = source.get(
                "rainfall_mm"
            )

            if rainfall is None:

                source_copy["status"] = (
                    "INVALID"
                )

            else:

                source_copy["status"] = (
                    "VALID"
                )

            validated.append(source_copy)


        return validated


    # ==================================================
    # FIND AGREEMENT
    # ==================================================

    def _find_agreement(
        self,
        valid_sources
    ):

        tolerance = self.config.get(
            "agreement_tolerance_mm",
            5
        )

        best_group = []

        for source in valid_sources:

            group = [
                other
                for other in valid_sources

                if abs(
                    source["rainfall_mm"]
                    - other["rainfall_mm"]
                ) <= tolerance
            ]

            if len(group) > len(best_group):

                best_group = group


        return best_group


    # ==================================================
    # EVALUATE ORACLES
    # ==================================================

    def evaluate(
        self,
        evaluation_time=None
    ):

        if evaluation_time is None:

            evaluation_time = datetime.now()


        # ------------------------------------------
        # STEP 1: VALIDATE SOURCES
        # ------------------------------------------

        validated = self.validate_sources(
            evaluation_time
        )


        valid_sources = [
            source
            for source in validated

            if source["status"] == "VALID"
        ]


        # ------------------------------------------
        # STEP 2: CHECK MINIMUM SOURCES
        # ------------------------------------------

        minimum_sources = self.config.get(
            "minimum_required_sources",
            2
        )


        if len(valid_sources) < minimum_sources:

            return {

                "decision": "INSUFFICIENT_DATA",

                "trusted_rainfall_mm": None,

                "valid_sources": len(
                    valid_sources
                ),

                "sources": validated,

                "reason":
                    "Not enough valid rainfall "
                    "sources are available."
            }


        # ------------------------------------------
        # STEP 3: FIND AGREEMENT
        # ------------------------------------------

        agreement_group = self._find_agreement(
            valid_sources
        )


        # ------------------------------------------
        # STEP 4: TWO OR MORE SOURCES AGREE
        # ------------------------------------------

        if len(agreement_group) >= minimum_sources:

            rainfall_values = [
                source["rainfall_mm"]

                for source in agreement_group
            ]


            # Median-style aggregation
            # prevents one extreme value from
            # dominating the trusted result.

            sorted_values = sorted(
                rainfall_values
            )

            middle = len(sorted_values) // 2

            if len(sorted_values) % 2 == 1:

                trusted_rainfall = (
                    sorted_values[middle]
                )

            else:

                trusted_rainfall = (
                    sorted_values[middle - 1]
                    + sorted_values[middle]
                ) / 2


            trusted_ids = [
                source["source_id"]

                for source in agreement_group
            ]


            # --------------------------------------
            # IDENTIFY OUTLIERS
            # --------------------------------------

            trusted_set = set(
                trusted_ids
            )

            for source in validated:

                if (
                    source["status"] == "VALID"
                    and
                    source["source_id"]
                    not in trusted_set
                ):

                    source["status"] = (
                        "OUTLIER"
                    )


            return {

                "decision": "TRUSTED",

                "trusted_rainfall_mm":
                    trusted_rainfall,

                "trusted_sources":
                    trusted_ids,

                "valid_sources":
                    len(valid_sources),

                "sources":
                    validated,

                "reason":
                    "At least two independent "
                    "valid sources agree within "
                    f"{self.config.get('agreement_tolerance_mm', 5)} mm."
            }


        # ------------------------------------------
        # STEP 5: TWO-WAY DISAGREEMENT
        # ------------------------------------------

        return {

            "decision": "DISPUTE",

            "trusted_rainfall_mm": None,

            "trusted_sources": [],

            "valid_sources":
                len(valid_sources),

            "sources":
                validated,

            "reason":
                "Valid rainfall sources disagree "
                "beyond the permitted tolerance. "
                "Settlement is paused pending resolution."
        }