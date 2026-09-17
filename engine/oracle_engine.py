import json
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median


class OracleEngine:
    """
    RainGuard Multi-Oracle Rainfall Engine.

    Features:
    - Multiple rainfall sources
    - Source validation
    - Responding/non-responding detection
    - Stale data detection
    - Invalid rainfall detection
    - Outlier/manipulation detection
    - Median trusted rainfall
    - TRUSTED / DISPUTE / INSUFFICIENT_DATA
    - Backward compatibility with existing tests
    """

    def __init__(self, data_file=None):

        if data_file is None:
            base_dir = Path(__file__).resolve().parent.parent
            data_file = base_dir / "data" / "oracle_data.json"

        self.data_file = Path(data_file)

        if not self.data_file.exists():
            raise FileNotFoundError(
                f"Oracle data file not found: {self.data_file}"
            )

        with open(
            self.data_file,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        self.config = data.get(
            "oracle_config",
            {}
        )

        # IMPORTANT:
        # Keep sources publicly accessible.
        # Tests and demo simulations modify them directly.
        self.sources = data.get(
            "sources",
            []
        )

    # =====================================================
    # TIMESTAMP
    # =====================================================

    def _parse_timestamp(self, timestamp):

        if not timestamp:
            return None

        try:
            return datetime.fromisoformat(
                timestamp
            )

        except (
            TypeError,
            ValueError
        ):
            return None

    # =====================================================
    # FRESHNESS CHECK
    # =====================================================

    def _is_fresh(
        self,
        source,
        evaluation_time
    ):

        timestamp = self._parse_timestamp(
            source.get("timestamp")
        )

        if timestamp is None:
            return False

        stale_after_hours = float(
            self.config.get(
                "stale_after_hours",
                24
            )
        )

        age = (
            evaluation_time - timestamp
        )

        # Future timestamps are considered fresh
        # for the demo environment.
        if age.total_seconds() < 0:
            return True

        return age <= timedelta(
            hours=stale_after_hours
        )

    # =====================================================
    # BUILD SOURCE STATUS
    # =====================================================

    def _process_sources(
        self,
        evaluation_time
    ):
        """
        Process ALL sources.

        Unlike the old implementation, this method keeps
        stale and non-responding sources in the result so
        the dashboard/tests can see what happened to them.
        """

        processed = []
        valid = []

        for source in self.sources:

            source_result = dict(source)

            rainfall = source.get(
                "rainfall_mm"
            )

            # -------------------------------------------------
            # NON-RESPONDING
            # -------------------------------------------------

            if not source.get(
                "responding",
                False
            ):

                source_result["status"] = (
                    "NON_RESPONDING"
                )

                source_result["valid"] = False

                processed.append(
                    source_result
                )

                continue

            # -------------------------------------------------
            # INVALID RAINFALL
            # -------------------------------------------------

            if rainfall is None:

                source_result["status"] = (
                    "INVALID_DATA"
                )

                source_result["valid"] = False

                processed.append(
                    source_result
                )

                continue

            try:
                rainfall = float(rainfall)

            except (
                TypeError,
                ValueError
            ):

                source_result["status"] = (
                    "INVALID_DATA"
                )

                source_result["valid"] = False

                processed.append(
                    source_result
                )

                continue

            source_result["rainfall_mm"] = rainfall

            # -------------------------------------------------
            # NEGATIVE RAINFALL
            # -------------------------------------------------

            if rainfall < 0:

                source_result["status"] = (
                    "INVALID_DATA"
                )

                source_result["valid"] = False

                processed.append(
                    source_result
                )

                continue

            # -------------------------------------------------
            # STALE SOURCE
            # -------------------------------------------------

            if not self._is_fresh(
                source,
                evaluation_time
            ):

                source_result["status"] = (
                    "STALE"
                )

                source_result["valid"] = False

                processed.append(
                    source_result
                )

                continue

            # -------------------------------------------------
            # VALID SOURCE
            # -------------------------------------------------

            source_result["status"] = (
                "VALID"
            )

            source_result["valid"] = True

            processed.append(
                source_result
            )

            valid.append(
                source_result
            )

        return processed, valid

    # =====================================================
    # EVALUATE
    # =====================================================

    def evaluate(
        self,
        evaluation_time=None
    ):
        """
        Evaluate rainfall data.

        Supports both:

            engine.evaluate()

        and:

            engine.evaluate(evaluation_time)
        """

        if evaluation_time is None:
            evaluation_time = datetime.now()

        # -------------------------------------------------
        # PROCESS ALL SOURCES
        # -------------------------------------------------

        all_sources, valid_sources = (
            self._process_sources(
                evaluation_time
            )
        )

        minimum_required = int(
            self.config.get(
                "minimum_required_sources",
                2
            )
        )

        tolerance = float(
            self.config.get(
                "agreement_tolerance_mm",
                5
            )
        )

        # =================================================
        # INSUFFICIENT DATA
        # =================================================

        if len(valid_sources) < minimum_required:

            return {
                "decision": "INSUFFICIENT_DATA",

                "trusted_rainfall_mm": None,

                "valid_sources": len(
                    valid_sources
                ),

                "valid_source_count": len(
                    valid_sources
                ),

                "required_sources":
                    minimum_required,

                "required_source_count":
                    minimum_required,

                # ALL sources are returned
                "sources": all_sources,

                "all_sources": all_sources,

                "trusted_sources": [],

                "rejected_sources": [],

                "reason": (
                    "There are not enough valid "
                    "rainfall sources to make a "
                    "trusted decision."
                )
            }

        # -------------------------------------------------
        # RAINFALL VALUES
        # -------------------------------------------------

        rainfall_values = [
            source["rainfall_mm"]
            for source in valid_sources
        ]

        # -------------------------------------------------
        # INITIAL MEDIAN
        # -------------------------------------------------

        initial_median = float(
            median(
                rainfall_values
            )
        )

        # -------------------------------------------------
        # FIND AGREEMENT
        # -------------------------------------------------

        trusted_sources = []
        rejected_sources = []

        for source in valid_sources:

            difference = abs(
                source["rainfall_mm"]
                - initial_median
            )

            if difference <= tolerance:

                trusted_sources.append(
                    source
                )

            else:

                rejected_sources.append(
                    source
                )

        # -------------------------------------------------
        # MARK OUTLIERS IN COMPLETE SOURCE LIST
        # -------------------------------------------------

        trusted_ids = {
            source["source_id"]
            for source in trusted_sources
        }

        rejected_ids = {
            source["source_id"]
            for source in rejected_sources
        }

        for source in all_sources:

            source_id = source.get(
                "source_id"
            )

            if source_id in trusted_ids:

                source["status"] = "TRUSTED"

            elif source_id in rejected_ids:

                source["status"] = "OUTLIER"

        # =================================================
        # DISPUTE
        # =================================================

        if len(trusted_sources) < minimum_required:

            return {
                "decision": "DISPUTE",

                "trusted_rainfall_mm": None,

                "valid_sources": len(
                    valid_sources
                ),

                "valid_source_count": len(
                    valid_sources
                ),

                "required_sources":
                    minimum_required,

                "required_source_count":
                    minimum_required,

                "sources": all_sources,

                "all_sources": all_sources,

                "trusted_sources": [],

                "rejected_sources":
                    rejected_sources,

                "reason": (
                    "Rainfall sources disagree "
                    "beyond the allowed tolerance."
                )
            }

        # =================================================
        # TRUSTED MEDIAN
        # =================================================

        trusted_values = [
            source["rainfall_mm"]
            for source in trusted_sources
        ]

        trusted_rainfall = float(
            median(
                trusted_values
            )
        )

        trusted_ids_list = [
            source["source_id"]
            for source in trusted_sources
        ]

        # =================================================
        # TRUSTED RESULT
        # =================================================

        return {
            "decision": "TRUSTED",

            "trusted_rainfall_mm":
                trusted_rainfall,

            "valid_sources":
                len(valid_sources),

            "valid_source_count":
                len(valid_sources),

            "required_sources":
                minimum_required,

            "required_source_count":
                minimum_required,

            # IMPORTANT:
            # Return ALL sources so the admin dashboard
            # and tests can inspect every oracle.
            "sources":
                all_sources,

            "all_sources":
                all_sources,

            "trusted_sources":
                trusted_ids_list,

            "trusted_source_records":
                trusted_sources,

            "rejected_sources":
                rejected_sources,

            "reason": (
                "Rainfall sources agree "
                "within the allowed tolerance."
            )
        }