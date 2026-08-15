from datetime import datetime, timezone
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QProgressBar,
)

from services.universe_service import UniverseService
from services.production_radar_pipeline import ProductionRadarPipeline, load_production_radar_snapshot



# ==========================================================
# PRODUCTION RADAR BACKGROUND WORKER
# ==========================================================

class RadarWorker(QThread):

    finished_scan = Signal(dict)
    failed_scan = Signal(str)
    progress_update = Signal(dict)

    def __init__(
        self,
        force_refresh=False,
    ):
        super().__init__()

        self.force_refresh = force_refresh

    def run(self):

        try:

            pipeline = ProductionRadarPipeline(
                candidate_limit=120,
                radar_limit=30,
                screen_batch_size=100,
                deep_batch_size=10,
            )

            result = pipeline.run(
                force_refresh=self.force_refresh,
                resume=True,
                progress_callback=self._emit_progress,
            )

            self.finished_scan.emit(
                result
            )

        except Exception as exc:

            self.failed_scan.emit(
                str(exc)
            )

    def _emit_progress(
        self,
        state,
    ):

        if isinstance(
            state,
            dict,
        ):

            self.progress_update.emit(
                state
            )


# ==========================================================
# METRIC CARD
# ==========================================================

class MetricCard(QFrame):

    def __init__(
        self,
        title,
        value="0",
    ):
        super().__init__()

        self.setStyleSheet("""
            QFrame {
                background: #1f2937;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(
            self
        )

        self.value_label = QLabel(
            str(value)
        )

        self.value_label.setStyleSheet(
            "font-size: 24px;"
            "font-weight: bold;"
            "color: white;"
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            "font-size: 12px;"
            "color: #9ca3af;"
        )

        layout.addWidget(
            self.value_label
        )

        layout.addWidget(
            title_label
        )

    def set_value(
        self,
        value,
    ):

        self.value_label.setText(
            str(value)
        )


# ==========================================================
# RESEARCH RADAR SCREEN
# ==========================================================

class ResearchRadar(QWidget):

    def __init__(
        self,
    ):

        super().__init__()

        self.worker = None

        # Last successful production result.
        #
        # Top 30 / Alpha 12 / Reserve 8 views all use this
        # same in-memory result. Switching views therefore
        # never triggers another market-data scan.
        self.last_result = None

        self.universe_service = (
            UniverseService()
        )

        root = QVBoxLayout(
            self
        )

        # ==================================================
        # HEADER
        # ==================================================

        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel(
            "Research Radar"
        )

        title.setStyleSheet(
            "font-size: 28px;"
            "font-weight: bold;"
        )

        subtitle = QLabel(
            "400-stock Midcap + Smallcap production universe "
            "→ Pre-screen 120 → Deep Research → Global Top 30"
        )

        subtitle.setStyleSheet(
            "font-size: 14px;"
            "color: #6b7280;"
        )

        title_box.addWidget(
            title
        )

        title_box.addWidget(
            subtitle
        )

        header.addLayout(
            title_box
        )

        header.addStretch()

        self.scan_btn = QPushButton(
            "Run Production Radar"
        )

        self.refresh_btn = QPushButton(
            "Force Refresh"
        )

        for button in (
            self.scan_btn,
            self.refresh_btn,
        ):

            button.setMinimumHeight(
                40
            )

            button.setMinimumWidth(
                160
            )

        header.addWidget(
            self.scan_btn
        )

        header.addWidget(
            self.refresh_btn
        )

        root.addLayout(
            header
        )

        # ==================================================
        # STATUS
        # ==================================================

        self.status_label = QLabel(
            "Ready"
        )

        self.status_label.setStyleSheet(
            "padding: 8px;"
            "color: #374151;"
            "font-weight: 500;"
        )

        root.addWidget(
            self.status_label
        )

        # ==================================================
        # PROGRESS BAR
        # ==================================================

        self.progress_bar = QProgressBar()

        self.progress_bar.setMinimum(
            0
        )

        self.progress_bar.setMaximum(
            120
        )

        self.progress_bar.setValue(
            0
        )

        self.progress_bar.setFormat(
            "Ready"
        )

        self.progress_bar.setTextVisible(
            True
        )

        root.addWidget(
            self.progress_bar
        )

        # ==================================================
        # METRIC CARDS
        # ==================================================

        cards = QHBoxLayout()

        self.universe_card = MetricCard(
            "Universe"
        )

        self.candidate_card = MetricCard(
            "Pre-Screen Candidates"
        )

        self.analyzed_card = MetricCard(
            "Deep Analyzed"
        )

        self.eligible_card = MetricCard(
            "Production Eligible"
        )

        self.cache_card = MetricCard(
            "Fresh Cache"
        )

        self.error_card = MetricCard(
            "Errors"
        )

        for card in (
            self.universe_card,
            self.candidate_card,
            self.analyzed_card,
            self.eligible_card,
            self.cache_card,
            self.error_card,
        ):

            cards.addWidget(
                card
            )

        root.addLayout(
            cards
        )

        # ==================================================
        # RADAR VIEW SELECTOR
        # ==================================================

        view_bar = QHBoxLayout()

        self.top30_btn = QPushButton(
            "Research Radar Top 30"
        )

        self.alpha12_btn = QPushButton(
            "Alpha 12"
        )

        self.reserve8_btn = QPushButton(
            "Reserve 8"
        )

        for button in (
            self.top30_btn,
            self.alpha12_btn,
            self.reserve8_btn,
        ):

            button.setCheckable(
                True
            )

            button.setMinimumHeight(
                36
            )

            view_bar.addWidget(
                button
            )

        view_bar.addStretch()

        self.top30_btn.setChecked(
            True
        )

        root.addLayout(
            view_bar
        )

        # ==================================================
        # RADAR TABLE
        # ==================================================

        self.table = QTableWidget()

        columns = [

            "Rank",
            "Symbol",
            "Category",
            "Company",
            "Sector",
            "Fundamental",
            "Technical",
            "Composite",
            "Readiness",
            "Market Health",
            "Confidence",
            "Coverage",
            "Data Status",
            "Classification",

        ]

        self.table.setColumnCount(
            len(columns)
        )

        self.table.setHorizontalHeaderLabels(
            columns
        )

        header_view = (
            self.table.horizontalHeader()
        )

        header_view.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        header_view.setStretchLastSection(
            False
        )

        # --------------------------------------------------
        # PRODUCTION RADAR COLUMN WIDTHS
        #
        # Keep compact analytical columns readable while
        # giving company/classification useful space.
        # Horizontal scrolling remains available.
        # --------------------------------------------------

        column_widths = {

            0: 55,    # Rank
            1: 100,   # Symbol
            2: 90,    # Category
            3: 190,   # Company
            4: 145,   # Sector
            5: 105,   # Fundamental
            6: 95,    # Technical
            7: 95,    # Composite
            8: 95,    # Readiness
            9: 110,   # Market Health
            10: 95,   # Confidence
            11: 90,   # Coverage
            12: 110,  # Data Status
            13: 210,  # Classification

        }

        for (
            column_index,
            column_width,
        ) in column_widths.items():

            self.table.setColumnWidth(
                column_index,
                column_width,
            )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSortingEnabled(
            False
        )

        root.addWidget(
            self.table
        )

        # ==================================================
        # EVENTS
        # ==================================================

        self.scan_btn.clicked.connect(
            lambda: self.start_scan(
                False
            )
        )

        self.refresh_btn.clicked.connect(
            lambda: self.start_scan(
                True
            )
        )

        self.top30_btn.clicked.connect(
            lambda: self.show_result_view(
                "TOP30"
            )
        )

        self.alpha12_btn.clicked.connect(
            lambda: self.show_result_view(
                "ALPHA12"
            )
        )

        self.reserve8_btn.clicked.connect(
            lambda: self.show_result_view(
                "RESERVE8"
            )
        )

        # ==================================================
        # INITIAL UNIVERSE LOAD & PERSISTED SNAPSHOT RESTORE
        # ==================================================

        self.load_universe_summary()
        self.restore_persisted_snapshot()


    # ======================================================
    # RESTORE PERSISTED SNAPSHOT
    # ======================================================

    def restore_persisted_snapshot(self) -> bool:
        """Automatically load and display the last valid persisted production radar snapshot."""
        try:
            snapshot = load_production_radar_snapshot()
            if not snapshot:
                self.status_label.setText(
                    "Data Status: UNAVAILABLE | No persisted Production Radar snapshot. Click 'Run Production Radar' to scan."
                )
                return False

            self.last_result = snapshot
            data_status = snapshot.get("data_status", "READY")
            ts_str = snapshot.get("timestamp", "N/A")
            if ts_str != "N/A":
                try:
                    dt = datetime.fromisoformat(ts_str)
                    ts_display = dt.strftime("%Y-%m-%d %H:%M UTC")
                except Exception:
                    ts_display = ts_str
            else:
                ts_display = "N/A"

            self.scan_finished(snapshot)

            universe_count = snapshot.get("universe_count", 0)
            candidate_count = snapshot.get("candidate_count", 0)
            processed_count = snapshot.get("processed_count", 0)
            ranked = snapshot.get("ranked", [])
            error_count = snapshot.get("error_count", 0)

            self.status_label.setText(
                f"Last Production Radar: {ts_display} | Data Status: {data_status} | "
                f"Universe {universe_count} → Pre-screen {candidate_count} → Deep analyzed {processed_count} → Top {len(ranked)} | Errors {error_count}"
            )
            self.progress_bar.setValue(candidate_count)
            self.progress_bar.setFormat(f"Production Radar complete ({data_status})")
            return True
        except Exception as exc:
            self.status_label.setText(f"Snapshot restore warning: {exc}")
            return False



    # ======================================================
    # LOAD UNIVERSE SUMMARY
    # ======================================================

    def load_universe_summary(
        self,
    ):

        try:

            universe_result = (
                self.universe_service
                .get_enabled_stocks()
            )

            stocks = universe_result.get(
                "stocks",
                [],
            )

            midcap_count = sum(

                1

                for stock in stocks

                if stock.get(
                    "category"
                ) == "MIDCAP"

            )

            smallcap_count = sum(

                1

                for stock in stocks

                if stock.get(
                    "category"
                ) == "SMALLCAP"

            )

            self.universe_card.set_value(
                len(stocks)
            )

            self.status_label.setText(

                "Production universe ready | "

                f"{len(stocks)} stocks | "

                f"MIDCAP {midcap_count} | "

                f"SMALLCAP {smallcap_count}"

            )

        except Exception as exc:

            self.universe_card.set_value(
                0
            )

            self.status_label.setText(
                f"Universe load warning: {exc}"
            )


    # ======================================================
    # START PRODUCTION RADAR
    # ======================================================

    def start_scan(
        self,
        force_refresh=False,
    ):

        # --------------------------------------------------
        # PREVENT MULTIPLE SIMULTANEOUS SCANS
        # --------------------------------------------------

        if (
            self.worker
            and self.worker.isRunning()
        ):

            return

        # --------------------------------------------------
        # FORCE REFRESH WARNING
        #
        # Force Refresh can trigger fresh deep analysis
        # for all 120 shortlisted candidates.
        # --------------------------------------------------

        if force_refresh:

            answer = QMessageBox.question(

                self,

                "Force Refresh Production Radar",

                "Force Refresh will ignore fresh Research Radar "
                "cache and may perform live deep analysis for all "
                "120 shortlisted candidates.\n\n"
                "This can take significant time and depends on "
                "external free-data sources.\n\n"
                "Continue?",

                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,

                QMessageBox.StandardButton.No,

            )

            if (
                answer
                != QMessageBox.StandardButton.Yes
            ):

                return

        # --------------------------------------------------
        # VERIFY UNIVERSE
        # --------------------------------------------------

        try:

            universe_result = (
                self.universe_service
                .get_enabled_stocks()
            )

            stocks = universe_result.get(
                "stocks",
                [],
            )

            if not stocks:

                QMessageBox.warning(

                    self,

                    "Research Radar",

                    "No enabled stocks found "
                    "in the production universe.",

                )

                return

        except Exception as exc:

            QMessageBox.critical(

                self,

                "Universe Error",

                str(exc),

            )

            return

        # --------------------------------------------------
        # RESET UI
        # --------------------------------------------------

        self.scan_btn.setEnabled(
            False
        )

        self.refresh_btn.setEnabled(
            False
        )

        self.candidate_card.set_value(
            0
        )

        self.analyzed_card.set_value(
            0
        )

        self.eligible_card.set_value(
            0
        )

        self.cache_card.set_value(
            0
        )

        self.error_card.set_value(
            0
        )

        self.progress_bar.setMaximum(
            120
        )

        self.progress_bar.setValue(
            0
        )

        self.progress_bar.setFormat(
            "Starting production pipeline..."
        )

        self.table.setSortingEnabled(
            False
        )

        self.table.clearContents()

        self.table.setRowCount(
            0
        )

        mode = (

            "Force-refresh production scan"

            if force_refresh

            else "Production scan"

        )

        self.status_label.setText(

            f"{mode} starting | "
            f"Universe {len(stocks)}"

        )

        # --------------------------------------------------
        # START BACKGROUND WORKER
        # --------------------------------------------------

        self.worker = RadarWorker(
            force_refresh=
                force_refresh
        )

        self.worker.progress_update.connect(
            self.scan_progress
        )

        self.worker.finished_scan.connect(
            self.scan_complete
        )

        self.worker.failed_scan.connect(
            self.scan_failed
        )

        self.worker.start()


    # ======================================================
    # SCAN PROGRESS
    # ======================================================

    def scan_progress(
        self,
        state,
    ):

        stage = state.get(
            "stage",
            ""
        )

        message = state.get(
            "message",
            ""
        )

        # --------------------------------------------------
        # UNIVERSE
        # --------------------------------------------------

        if stage == "UNIVERSE":

            self.status_label.setText(
                "Loading 400-stock production universe..."
            )

            self.progress_bar.setValue(
                0
            )

            self.progress_bar.setFormat(
                "Loading universe..."
            )

        # --------------------------------------------------
        # PRE-SCREEN
        # --------------------------------------------------

        elif stage == "PRE_SCREEN":

            universe_count = state.get(
                "universe_count",
                0,
            )

            self.universe_card.set_value(
                universe_count
            )

            self.status_label.setText(

                f"Market pre-screen running | "
                f"Universe {universe_count}"

            )

            self.progress_bar.setValue(
                0
            )

            self.progress_bar.setFormat(
                "Pre-screening production universe..."
            )

        # --------------------------------------------------
        # DEEP SCAN START
        # --------------------------------------------------

        elif stage == "DEEP_SCAN_START":

            candidate_count = state.get(
                "candidate_count",
                0,
            )

            cache_fresh = state.get(
                "cache_fresh",
                0,
            )

            cache_expired = state.get(
                "cache_expired",
                0,
            )

            cache_missing = state.get(
                "cache_missing",
                0,
            )

            self.candidate_card.set_value(
                candidate_count
            )

            self.cache_card.set_value(
                cache_fresh
            )

            self.progress_bar.setMaximum(
                max(
                    candidate_count,
                    1,
                )
            )

            self.progress_bar.setValue(
                0
            )

            self.progress_bar.setFormat(

                f"Deep analysis 0/"
                f"{candidate_count}"

            )

            self.status_label.setText(

                f"Pre-screen complete | "
                f"Candidates {candidate_count} | "
                f"Fresh cache {cache_fresh} | "
                f"Expired {cache_expired} | "
                f"Live needed {cache_missing}"

            )

        # --------------------------------------------------
        # DEEP SCAN PROGRESS
        # --------------------------------------------------

        elif stage == "DEEP_SCAN":

            processed = state.get(
                "processed_count",
                0,
            )

            total = state.get(
                "total_count",
                0,
            )

            remaining = state.get(
                "remaining_count",
                0,
            )

            self.analyzed_card.set_value(
                processed
            )

            self.progress_bar.setMaximum(
                max(
                    total,
                    1,
                )
            )

            self.progress_bar.setValue(
                min(
                    processed,
                    max(
                        total,
                        1,
                    ),
                )
            )

            self.progress_bar.setFormat(

                f"Deep analysis "
                f"{processed}/{total}"

            )

            self.status_label.setText(

                f"Deep Research Radar running | "
                f"Processed {processed}/{total} | "
                f"Remaining {remaining}"

            )

        # --------------------------------------------------
        # COMPLETE
        # --------------------------------------------------

        elif stage == "COMPLETE":

            candidate_count = state.get(
                "candidate_count",
                0,
            )

            processed_count = state.get(
                "processed_count",
                candidate_count,
            )

            ranked_count = state.get(
                "ranked_count",
                0,
            )

            self.progress_bar.setMaximum(
                max(
                    candidate_count,
                    1,
                )
            )

            self.progress_bar.setValue(
                max(
                    processed_count,
                    candidate_count,
                )
            )

            self.progress_bar.setFormat(
                "Production Radar complete"
            )

            self.status_label.setText(

                f"Production Radar complete | "
                f"Top candidates {ranked_count}"

            )

        elif message:

            self.status_label.setText(
                str(message)
            )


    # ======================================================
    # SCAN COMPLETE
    # ======================================================

    def scan_complete(
        self,
        result,
    ):

        self.scan_btn.setEnabled(
            True
        )

        self.refresh_btn.setEnabled(
            True
        )

        # --------------------------------------------------
        # PIPELINE ERROR RESULT
        # --------------------------------------------------

        if (
            result.get(
                "status"
            )
            != "OK"
        ):

            error = result.get(
                "error",
                "Unknown production pipeline error.",
            )

            self.status_label.setText(
                "Production Radar failed."
            )

            QMessageBox.critical(

                self,

                "Production Radar Error",

                str(error),

            )

            return

        # --------------------------------------------------
        # STORE SUCCESSFUL PRODUCTION RESULT
        # --------------------------------------------------

        self.last_result = result

        # --------------------------------------------------
        # SUMMARY METRICS
        # --------------------------------------------------

        universe_count = result.get(
            "universe_count",
            0,
        )

        candidate_count = result.get(
            "candidate_count",
            0,
        )

        processed_count = result.get(
            "processed_count",
            0,
        )

        eligible_count = result.get(
            "eligible_count",
            0,
        )

        error_count = result.get(
            "error_count",
            0,
        )

        cache_summary = result.get(
            "cache_summary",
            {},
        )

        cache_fresh = cache_summary.get(
            "fresh_count",
            0,
        )

        self.universe_card.set_value(
            universe_count
        )

        self.candidate_card.set_value(
            candidate_count
        )

        self.analyzed_card.set_value(
            processed_count
        )

        self.eligible_card.set_value(
            eligible_count
        )

        self.cache_card.set_value(
            cache_fresh
        )

        self.error_card.set_value(
            error_count
        )

        # --------------------------------------------------
        # GLOBAL TOP-30
        # --------------------------------------------------

        ranked = result.get(
            "ranked",
            [],
        )

        self._set_active_view_button(
            "TOP30"
        )

        self.populate_table(
            ranked
        )

        # --------------------------------------------------
        # FINAL PROGRESS
        # --------------------------------------------------

        self.progress_bar.setMaximum(
            max(
                candidate_count,
                1,
            )
        )

        self.progress_bar.setValue(
            candidate_count
        )

        self.progress_bar.setFormat(
            "Production Radar complete"
        )

        # --------------------------------------------------
        # CATEGORY COUNTS
        # --------------------------------------------------

        midcap_candidates = result.get(
            "candidate_midcap_count",
            0,
        )

        smallcap_candidates = result.get(
            "candidate_smallcap_count",
            0,
        )

        # --------------------------------------------------
        # STATUS SUMMARY
        # --------------------------------------------------

        self.status_label.setText(

            "Production Radar complete | "

            f"Universe {universe_count} → "

            f"Pre-screen {candidate_count} "
            f"(M {midcap_candidates} / "
            f"S {smallcap_candidates}) → "

            f"Deep analyzed {processed_count} → "

            f"Top {len(ranked)} | "

            f"Errors {error_count}"

        )


    # ======================================================
    # SCAN FAILED
    # ======================================================

    def scan_failed(
        self,
        error,
    ):

        self.scan_btn.setEnabled(
            True
        )

        self.refresh_btn.setEnabled(
            True
        )

        self.progress_bar.setFormat(
            "Production Radar failed"
        )

        self.status_label.setText(
            "Production Radar scan failed."
        )

        QMessageBox.critical(

            self,

            "Research Radar Error",

            str(error),

        )


    # ======================================================
    # RESULT VIEW MANAGEMENT
    # ======================================================

    def _set_active_view_button(
        self,
        view_name,
    ):

        self.top30_btn.setChecked(
            view_name == "TOP30"
        )

        self.alpha12_btn.setChecked(
            view_name == "ALPHA12"
        )

        self.reserve8_btn.setChecked(
            view_name == "RESERVE8"
        )


    def show_result_view(
        self,
        view_name,
    ):

        if not isinstance(
            self.last_result,
            dict,
        ):

            self.status_label.setText(
                "Run Production Radar first."
            )

            self._set_active_view_button(
                "TOP30"
            )

            return

        self._set_active_view_button(
            view_name
        )

        if view_name == "ALPHA12":

            rows = self.last_result.get(
                "alpha12",
                [],
            )

            self.populate_alpha12_table(
                rows,
                reserve=False,
            )

            self.status_label.setText(
                f"Alpha 12 | "
                f"{len(rows)} selected investment candidates"
            )

            return

        if view_name == "RESERVE8":

            rows = self.last_result.get(
                "alpha12_reserves",
                [],
            )

            self.populate_alpha12_table(
                rows,
                reserve=True,
            )

            self.status_label.setText(
                f"Alpha 12 Reserve Pool | "
                f"{len(rows)} replacement candidates"
            )

            return

        rows = self.last_result.get(
            "ranked",
            [],
        )

        self.populate_table(
            rows
        )

        self.status_label.setText(
            f"Research Radar Top {len(rows)}"
        )


    # ======================================================
    # POPULATE ALPHA 12 / RESERVE TABLE
    # ======================================================

    def populate_alpha12_table(
        self,
        rows,
        reserve=False,
    ):

        self.table.setSortingEnabled(
            False
        )

        self.table.clearContents()

        if reserve:

            columns = [

                "Reserve Rank",
                "Radar Rank",
                "Symbol",
                "Category",
                "Company",
                "Sector",
                "Composite",
                "Alpha Base",
                "Sector Penalty",
                "Adjusted Alpha",
                "Reason",

            ]

            rank_field = (
                "reserve_rank"
            )

        else:

            columns = [

                "Alpha Rank",
                "Radar Rank",
                "Symbol",
                "Category",
                "Company",
                "Sector",
                "Composite",
                "Alpha Base",
                "Sector Penalty",
                "Adjusted Alpha",
                "Reason",

            ]

            rank_field = (
                "alpha12_rank"
            )

        fields = [

            rank_field,
            "radar_rank",
            "symbol",
            "category",
            "company_name",
            "sector",
            "composite_score",
            "alpha12_base_score",
            "sector_concentration_penalty",
            "alpha12_selection_score",
            "selection_reason",

        ]

        self.table.setColumnCount(
            len(columns)
        )

        self.table.setHorizontalHeaderLabels(
            columns
        )

        self.table.setRowCount(
            len(rows)
        )

        column_widths = {

            0: 90,
            1: 85,
            2: 105,
            3: 95,
            4: 200,
            5: 150,
            6: 100,
            7: 100,
            8: 115,
            9: 115,
            10: 360,

        }

        for (
            column_index,
            column_width,
        ) in column_widths.items():

            self.table.setColumnWidth(
                column_index,
                column_width,
            )

        numeric_columns = {

            0,
            1,
            6,
            7,
            8,
            9,

        }

        for row_index, stock in enumerate(
            rows
        ):

            for column_index, field in enumerate(
                fields
            ):

                value = stock.get(
                    field,
                    "",
                )

                # ------------------------------------------
                # COMPANY FALLBACK
                # ------------------------------------------

                if field == "company_name":

                    company_text = (
                        str(value).strip()
                        if value is not None
                        else ""
                    )

                    if (
                        not company_text
                        or company_text.upper()
                        in {
                            "N/A",
                            "NA",
                            "NONE",
                            "NULL",
                            "-",
                        }
                    ):

                        value = stock.get(
                            "universe_company",
                            "",
                        )

                # ------------------------------------------
                # REASON FALLBACK
                # ------------------------------------------

                if (
                    field
                    == "selection_reason"
                    and not value
                ):

                    value = stock.get(
                        "reserve_reason",
                        "",
                    )

                if value is None:

                    value = ""

                elif isinstance(
                    value,
                    float,
                ):

                    value = (
                        f"{value:.2f}"
                    )

                item = QTableWidgetItem(
                    str(value)
                )

                if (
                    column_index
                    in numeric_columns
                ):

                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.table.setItem(

                    row_index,

                    column_index,

                    item,

                )

        self.table.setSortingEnabled(
            True
        )


    # ======================================================
    # POPULATE GLOBAL TOP-30 TABLE
    # ======================================================

    def populate_table(
        self,
        ranked,
    ):

        self.table.setSortingEnabled(
            False
        )

        self.table.clearContents()

        columns = [

            "Rank",
            "Symbol",
            "Category",
            "Company",
            "Sector",
            "Fundamental",
            "Technical",
            "Composite",
            "Readiness",
            "Market Health",
            "Confidence",
            "Coverage",
            "Data Status",
            "Classification",

        ]

        self.table.setColumnCount(
            len(columns)
        )

        self.table.setHorizontalHeaderLabels(
            columns
        )

        column_widths = {

            0: 55,
            1: 100,
            2: 90,
            3: 190,
            4: 145,
            5: 105,
            6: 95,
            7: 95,
            8: 95,
            9: 110,
            10: 95,
            11: 90,
            12: 110,
            13: 210,

        }

        for (
            column_index,
            column_width,
        ) in column_widths.items():

            self.table.setColumnWidth(
                column_index,
                column_width,
            )

        self.table.setRowCount(
            len(ranked)
        )

        fields = [

            "rank",
            "symbol",
            "category",
            "company_name",
            "sector",
            "fundamental_score",
            "technical_score",
            "composite_score",
            "readiness_score",
            "market_health_score",
            "data_confidence",
            "coverage_score",
            "data_status",
            "classification",

        ]

        numeric_columns = {

            0,
            5,
            6,
            7,
            8,
            9,
            11,

        }

        for row, stock in enumerate(
            ranked
        ):

            for column, field in enumerate(
                fields
            ):

                value = stock.get(
                    field,
                    "",
                )

                # ------------------------------------------
                # COMPANY FALLBACK
                # ------------------------------------------

                if (
                    field
                    == "company_name"
                ):

                    company_text = (
                        str(value).strip()
                        if value is not None
                        else ""
                    )

                    if (
                        not company_text
                        or company_text.upper()
                        in {
                            "N/A",
                            "NA",
                            "NONE",
                            "NULL",
                            "-",
                        }
                    ):

                        universe_company = (
                            stock.get(
                                "universe_company",
                                ""
                            )
                        )

                        universe_company_text = (
                            str(
                                universe_company
                            ).strip()
                            if universe_company
                            is not None
                            else ""
                        )

                        if universe_company_text:

                            value = (
                                universe_company_text
                            )

                # ------------------------------------------
                # CLASSIFICATION MAY BE STRUCTURED
                # ------------------------------------------

                if (
                    field
                    == "classification"
                    and isinstance(
                        value,
                        dict,
                    )
                ):

                    value = (

                        value.get(
                            "label"
                        )

                        or value.get(
                            "classification"
                        )

                        or str(
                            value
                        )

                    )

                if value is None:

                    value = ""

                elif isinstance(
                    value,
                    float,
                ):

                    value = (
                        f"{value:.2f}"
                    )

                item = QTableWidgetItem(
                    str(value)
                )

                if (
                    column
                    in numeric_columns
                ):

                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if column == 2:

                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.table.setItem(

                    row,

                    column,

                    item,

                )

        self.table.setSortingEnabled(
            True
        )