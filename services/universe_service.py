from pathlib import Path
import csv
import json

from config.path_config import get_resource_path


class UniverseService:
    # ...
    VALID_CATEGORIES = {
        "MIDCAP",
        "SMALLCAP",
    }

    REQUIRED_COLUMNS = {
        "symbol",
        "company",
        "category",
        "enabled",
    }

    OPTIONAL_COLUMNS = {
        "exchange",
        "source",
        "as_of_date",
    }

    VALID_EXCHANGES = {
        "",
        "NSE",
        "BSE",
    }

    # --------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------

    def __init__(
        self,
        universe_file=None,
        metadata_file=None,
    ):
        self.project_root = get_resource_path("")

        if universe_file is None:
            self.universe_file = get_resource_path("data/universe/stock_universe.csv")
        else:
            self.universe_file = Path(universe_file)

        if metadata_file is None:
            self.metadata_file = get_resource_path("data/universe/universe_metadata.json")
        else:
            self.metadata_file = Path(metadata_file)

    # --------------------------------------------------
    # BOOLEAN CONVERTER
    # --------------------------------------------------

    def _to_bool(
        self,
        value,
    ):

        return (
            str(
                value
            )
            .strip()
            .lower()
            in {
                "true",
                "1",
                "yes",
                "y",
            }
        )

    # --------------------------------------------------
    # CLEAN TEXT
    # --------------------------------------------------

    def _clean_text(
        self,
        value,
    ):

        if value is None:

            return ""

        return str(
            value
        ).strip()

    # --------------------------------------------------
    # CLEAN SYMBOL
    # --------------------------------------------------

    def _clean_symbol(
        self,
        value,
    ):

        return (
            self._clean_text(
                value
            )
            .upper()
        )

    # --------------------------------------------------
    # LOAD METADATA
    # --------------------------------------------------

    def load_metadata(
        self,
    ):

        if not self.metadata_file.exists():

            return {
                "metadata": {},
                "errors": [
                    "Universe metadata file not found: "
                    f"{self.metadata_file}"
                ],
            }

        try:

            with self.metadata_file.open(
                "r",
                encoding="utf-8-sig",
            ) as file:

                metadata = json.load(
                    file
                )

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:

            return {
                "metadata": {},
                "errors": [
                    "Unable to load universe metadata: "
                    f"{error}"
                ],
            }

        if not isinstance(
            metadata,
            dict,
        ):

            return {
                "metadata": {},
                "errors": [
                    "Universe metadata must be "
                    "a JSON object"
                ],
            }

        errors = []

        # Basic metadata validation.

        if not metadata.get(
            "universe_name"
        ):

            errors.append(
                "Metadata missing universe_name"
            )

        if not metadata.get(
            "version"
        ):

            errors.append(
                "Metadata missing version"
            )

        categories = metadata.get(
            "categories",
            [],
        )

        if not isinstance(
            categories,
            list,
        ):

            errors.append(
                "Metadata categories must be a list"
            )

        else:

            metadata_categories = {

                str(
                    category
                )
                .strip()
                .upper()

                for category
                in categories
            }

            invalid_categories = (

                metadata_categories

                - self.VALID_CATEGORIES
            )

            if invalid_categories:

                errors.append(
                    "Metadata contains invalid categories: "
                    + ", ".join(
                        sorted(
                            invalid_categories
                        )
                    )
                )

        return {
            "metadata": metadata,
            "errors": errors,
        }

    # --------------------------------------------------
    # LOAD AND VALIDATE UNIVERSE
    # --------------------------------------------------

    def load_universe(
        self,
    ):

        if not self.universe_file.exists():

            return {
                "stocks": [],
                "invalid_rows": [],
                "errors": [
                    "Universe file not found: "
                    f"{self.universe_file}"
                ],
            }

        stocks = []

        invalid_rows = []

        errors = []

        seen_symbols = set()

        try:

            with self.universe_file.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:

                reader = csv.DictReader(
                    file
                )

                fieldnames = [
                    str(
                        column
                    ).strip()
                    for column
                    in (
                        reader.fieldnames
                        or []
                    )
                ]

                actual_columns = set(
                    fieldnames
                )

                missing_columns = (

                    self.REQUIRED_COLUMNS

                    - actual_columns
                )

                if missing_columns:

                    return {
                        "stocks": [],
                        "invalid_rows": [],
                        "errors": [
                            "Missing columns: "
                            + ", ".join(
                                sorted(
                                    missing_columns
                                )
                            )
                        ],
                    }

                # ------------------------------------------
                # PROCESS ROWS
                # ------------------------------------------

                for row_number, row in enumerate(
                    reader,
                    start=2,
                ):

                    symbol = (
                        self._clean_symbol(
                            row.get(
                                "symbol"
                            )
                        )
                    )

                    company = (
                        self._clean_text(
                            row.get(
                                "company"
                            )
                        )
                    )

                    category = (
                        self._clean_text(
                            row.get(
                                "category"
                            )
                        )
                        .upper()
                    )

                    enabled = (
                        self._to_bool(
                            row.get(
                                "enabled",
                                False,
                            )
                        )
                    )

                    exchange = (
                        self._clean_text(
                            row.get(
                                "exchange",
                                ""
                            )
                        )
                        .upper()
                    )

                    source = (
                        self._clean_text(
                            row.get(
                                "source",
                                ""
                            )
                        )
                    )

                    as_of_date = (
                        self._clean_text(
                            row.get(
                                "as_of_date",
                                ""
                            )
                        )
                    )

                    row_errors = []

                    # --------------------------------------
                    # SYMBOL VALIDATION
                    # --------------------------------------

                    if not symbol:

                        row_errors.append(
                            "missing symbol"
                        )

                    # --------------------------------------
                    # COMPANY VALIDATION
                    # --------------------------------------

                    if not company:

                        row_errors.append(
                            "missing company name"
                        )

                    # --------------------------------------
                    # CATEGORY VALIDATION
                    # --------------------------------------

                    if (
                        category
                        not in self.VALID_CATEGORIES
                    ):

                        row_errors.append(
                            "invalid category "
                            f"{category}"
                        )

                    # --------------------------------------
                    # EXCHANGE VALIDATION
                    # --------------------------------------

                    if (
                        exchange
                        not in self.VALID_EXCHANGES
                    ):

                        row_errors.append(
                            "invalid exchange "
                            f"{exchange}"
                        )

                    # --------------------------------------
                    # DUPLICATE SYMBOL VALIDATION
                    # --------------------------------------

                    if (
                        symbol
                        and symbol
                        in seen_symbols
                    ):

                        row_errors.append(
                            "duplicate symbol "
                            f"{symbol}"
                        )

                    # --------------------------------------
                    # QUARANTINE INVALID ROW
                    # --------------------------------------

                    if row_errors:

                        invalid_rows.append({

                            "row_number":
                                row_number,

                            "symbol":
                                symbol,

                            "company":
                                company,

                            "category":
                                category,

                            "enabled":
                                enabled,

                            "exchange":
                                exchange,

                            "source":
                                source,

                            "as_of_date":
                                as_of_date,

                            "reasons":
                                row_errors,
                        })

                        for reason in row_errors:

                            errors.append(
                                f"Row {row_number}: "
                                f"{reason}"
                            )

                        continue

                    # --------------------------------------
                    # ACCEPT VALID STOCK
                    # --------------------------------------

                    seen_symbols.add(
                        symbol
                    )

                    stocks.append({

                        "symbol":
                            symbol,

                        "company":
                            company,

                        "category":
                            category,

                        "enabled":
                            enabled,

                        "exchange":
                            exchange,

                        "source":
                            source,

                        "as_of_date":
                            as_of_date,
                    })

        except Exception as error:

            return {
                "stocks": [],
                "invalid_rows": [],
                "errors": [
                    str(
                        error
                    )
                ],
            }

        return {
            "stocks":
                stocks,

            "invalid_rows":
                invalid_rows,

            "errors":
                errors,
        }

    # --------------------------------------------------
    # GET ENABLED STOCKS
    # --------------------------------------------------

    def get_enabled_stocks(
        self,
        category=None,
    ):

        result = (
            self.load_universe()
        )

        stocks = result[
            "stocks"
        ]

        enabled = [

            stock

            for stock in stocks

            if stock.get(
                "enabled"
            )
        ]

        if category is not None:

            category = (
                str(
                    category
                )
                .strip()
                .upper()
            )

            if (
                category
                not in self.VALID_CATEGORIES
            ):

                return {
                    "stocks": [],
                    "invalid_rows":
                        result.get(
                            "invalid_rows",
                            [],
                        ),
                    "errors":
                        result.get(
                            "errors",
                            [],
                        )
                        + [
                            "Invalid requested category: "
                            f"{category}"
                        ],
                }

            enabled = [

                stock

                for stock in enabled

                if stock.get(
                    "category"
                ) == category
            ]

        return {
            "stocks":
                enabled,

            "invalid_rows":
                result.get(
                    "invalid_rows",
                    [],
                ),

            "errors":
                result.get(
                    "errors",
                    [],
                ),
        }

    # --------------------------------------------------
    # GET SYMBOLS
    #
    # Backward compatible with existing Research Radar.
    # --------------------------------------------------

    def get_symbols(
        self,
        category=None,
    ):

        result = (
            self.get_enabled_stocks(
                category
            )
        )

        symbols = [

            stock[
                "symbol"
            ]

            for stock
            in result[
                "stocks"
            ]
        ]

        return {
            "symbols":
                symbols,

            "errors":
                result.get(
                    "errors",
                    [],
                ),

            "invalid_rows":
                result.get(
                    "invalid_rows",
                    [],
                ),
        }

    # --------------------------------------------------
    # GET STOCK BY SYMBOL
    # --------------------------------------------------

    def get_stock(
        self,
        symbol,
    ):

        clean_symbol = (
            self._clean_symbol(
                symbol
            )
        )

        result = (
            self.load_universe()
        )

        for stock in result[
            "stocks"
        ]:

            if (
                stock.get(
                    "symbol"
                )
                == clean_symbol
            ):

                return {
                    "stock":
                        stock,

                    "errors":
                        result.get(
                            "errors",
                            [],
                        ),
                }

        return {
            "stock":
                None,

            "errors":
                result.get(
                    "errors",
                    [],
                )
                + [
                    "Symbol not found in universe: "
                    f"{clean_symbol}"
                ],
        }

    # --------------------------------------------------
    # GET SUMMARY
    # --------------------------------------------------

    def get_summary(
        self,
    ):

        universe_result = (
            self.load_universe()
        )

        metadata_result = (
            self.load_metadata()
        )

        stocks = universe_result[
            "stocks"
        ]

        enabled = [

            stock

            for stock in stocks

            if stock.get(
                "enabled"
            )
        ]

        disabled = [

            stock

            for stock in stocks

            if not stock.get(
                "enabled"
            )
        ]

        midcap = [

            stock

            for stock in enabled

            if stock.get(
                "category"
            ) == "MIDCAP"
        ]

        smallcap = [

            stock

            for stock in enabled

            if stock.get(
                "category"
            ) == "SMALLCAP"
        ]

        exchange_counts = {}

        for stock in enabled:

            exchange = (
                stock.get(
                    "exchange"
                )
                or "UNSPECIFIED"
            )

            exchange_counts[
                exchange
            ] = (

                exchange_counts.get(
                    exchange,
                    0,
                )

                + 1
            )

        metadata = (
            metadata_result.get(
                "metadata",
                {}
            )
        )

        combined_errors = (

            universe_result.get(
                "errors",
                [],
            )

            + metadata_result.get(
                "errors",
                [],
            )
        )

        return {

            "universe_name":
                metadata.get(
                    "universe_name"
                ),

            "version":
                metadata.get(
                    "version"
                ),

            "market":
                metadata.get(
                    "market"
                ),

            "categories":
                metadata.get(
                    "categories",
                    [],
                ),

            "total_records":
                len(
                    stocks
                ),

            "enabled_records":
                len(
                    enabled
                ),

            "disabled_records":
                len(
                    disabled
                ),

            "midcap_count":
                len(
                    midcap
                ),

            "smallcap_count":
                len(
                    smallcap
                ),

            "invalid_row_count":
                len(
                    universe_result.get(
                        "invalid_rows",
                        [],
                    )
                ),

            "exchange_counts":
                exchange_counts,

            "metadata":
                metadata,

            "invalid_rows":
                universe_result.get(
                    "invalid_rows",
                    [],
                ),

            "errors":
                combined_errors,
        }

    # --------------------------------------------------
    # VALIDATE UNIVERSE
    # --------------------------------------------------

    def validate_universe(
        self,
    ):

        summary = (
            self.get_summary()
        )

        validation_issues = list(
            summary.get(
                "errors",
                [],
            )
        )

        if (
            summary.get(
                "enabled_records",
                0,
            )
            == 0
        ):

            validation_issues.append(
                "No enabled stocks in universe"
            )

        if (
            summary.get(
                "midcap_count",
                0,
            )
            == 0
        ):

            validation_issues.append(
                "No enabled MIDCAP stocks"
            )

        if (
            summary.get(
                "smallcap_count",
                0,
            )
            == 0
        ):

            validation_issues.append(
                "No enabled SMALLCAP stocks"
            )

        validation_issues = list(
            dict.fromkeys(
                validation_issues
            )
        )

        return {

            "valid":
                len(
                    validation_issues
                )
                == 0,

            "issues":
                validation_issues,

            "summary":
                summary,
        }


# ==================================================
# CONVENIENCE FUNCTIONS
# ==================================================

def load_stock_universe(
    category=None,
):

    service = (
        UniverseService()
    )

    return (
        service.get_enabled_stocks(
            category
        )
    )


def get_universe_symbols(
    category=None,
):

    service = (
        UniverseService()
    )

    return (
        service.get_symbols(
            category
        )
    )


def get_universe_summary():

    service = (
        UniverseService()
    )

    return (
        service.get_summary()
    )


def validate_stock_universe():

    service = (
        UniverseService()
    )

    return (
        service.validate_universe()
    )