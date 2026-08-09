from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QSpinBox,
    QLineEdit,
    QScrollArea,
)

from services.portfolio_application_service import (
    create_portfolio_application_service,
)

from services.stock_service import (
    get_stock_data,
)

from app.widgets.portfolio_action_center import PortfolioActionCenter
from services.portfolio_action_service import PortfolioActionService
from app.widgets.recommendation_detail_panel import RecommendationDetailPanel


class Portfolio(QWidget):

    def __init__(
        self,
        alpha12_provider=None,
    ):
        super().__init__()

        self.alpha12_provider = (
            alpha12_provider
        )

        self.pending_initial_recommendation = None

        self.portfolio_service = (
            create_portfolio_application_service()
        )

        from services.portfolio_benchmark_service import (
            PortfolioBenchmarkService,
        )

        self.benchmark_service = (
            PortfolioBenchmarkService()
        )

        from services.portfolio_performance_service import (
            PortfolioPerformanceService,
        )

        self.performance_service = (
            PortfolioPerformanceService()
        )

        self._build_ui()

        self.initial_investment_btn = QPushButton(
            "+ Create Portfolio"
        )

        self.initial_investment_btn.setMinimumHeight(
            42
        )

        self.initial_investment_btn.setStyleSheet(
            "font-size: 14px;"
            "font-weight: bold;"
            "padding: 8px 18px;"
        )

        self.initial_investment_btn.clicked.connect(
            self.prepare_initial_investment
        )

        if hasattr(
            self,
            "empty_layout",
        ):

            self.empty_layout.addWidget(
                self.initial_investment_btn,
                alignment=Qt.AlignCenter,
            )


        self.load_portfolio()

    # ======================================================
    # UI CONSTRUCTION
    # ======================================================

    def _build_ui(self):

        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fb;
                color: #1f2937;
                font-family: Segoe UI;
            }

            QLabel#pageTitle {
                font-size: 28px;
                font-weight: 700;
                color: #173b67;
            }

            QLabel#pageSubtitle {
                font-size: 14px;
                color: #64748b;
            }

            QLabel#statusLabel {
                font-size: 13px;
                font-weight: 600;
                color: #1e3a5f;
                background-color: #eef2f7;
                border: 1px solid #d0dbe9;
                border-radius: 6px;
                padding: 6px 12px;
                margin-top: 6px;
            }

            QLabel#sectionTitle {
                font-size: 17px;
                font-weight: 700;
                color: #173b67;
            }

            QFrame#metricCard {
                background-color: white;
                border: 1px solid #dce3ed;
                border-radius: 10px;
            }

            QLabel#metricTitle {
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
            }

            QLabel#metricValue {
                font-size: 22px;
                font-weight: 700;
                color: #173b67;
            }

            QLabel#emptyTitle {
                font-size: 24px;
                font-weight: 700;
                color: #334155;
            }

            QLabel#emptyText {
                font-size: 14px;
                color: #64748b;
            }

            QPushButton {
                background-color: #173b67;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 18px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #24558d;
            }

            QTableWidget {
                background-color: white;
                alternate-background-color: #f8fafc;
                border: 1px solid #dce3ed;
                border-radius: 8px;
                gridline-color: #e5e7eb;
                font-size: 12px;
            }

            QHeaderView::section {
                background-color: #173b67;
                color: white;
                padding: 8px;
                border: none;
                font-weight: 600;
            }
        """)

        # Create a scrollable content area so the portfolio page can grow vertically
        content_widget = QWidget()
        root = QVBoxLayout(content_widget)

        root.setContentsMargins(
            24,
            20,
            24,
            20,
        )

        root.setSpacing(
            16
        )

        # Outer layout holds the scroll area (attach this to self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        # Ensure horizontal scrolling is disabled and visual chrome is removed
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(content_widget)

        outer.addWidget(scroll)

        # --------------------------------------------------
        # HEADER
        # --------------------------------------------------

        header = QHBoxLayout()

        title_box = QVBoxLayout()

        self.title_label = QLabel(
            "AlphaForge Portfolio"
        )

        self.title_label.setObjectName(
            "pageTitle"
        )

        self.subtitle_label = QLabel(
            "Persistent Alpha 12 portfolio monitoring"
        )

        self.subtitle_label.setObjectName(
            "pageSubtitle"
        )

        title_box.addWidget(
            self.title_label
        )

        title_box.addWidget(
            self.subtitle_label
        )

        header.addLayout(
            title_box
        )

        header.addStretch()

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.refresh_button.clicked.connect(
            self.load_portfolio
        )

        self.reset_button = QPushButton(
            "Reset Portfolio"
        )
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 18px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        self.reset_button.clicked.connect(
            self._on_reset_portfolio_clicked
        )

        header.addWidget(
            self.refresh_button
        )
        header.addWidget(
            self.reset_button
        )

        root.addLayout(
            header
        )

        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        self.status_label = QLabel(
            "Portfolio loaded."
        )

        self.status_label.setObjectName(
            "statusLabel"
        )

        self.status_label.setStyleSheet("""
            background-color: #dbeafe;
            color: #173b67;
            border: 1px solid #93c5fd;
            border-radius: 6px;
            padding: 10px 14px;
            font-size: 13px;
            font-weight: 700;
            min-height: 20px;
        """)

        root.addWidget(self.status_label)

        # --------------------------------------------------
        # METRICS
        # --------------------------------------------------

        self.metrics_frame = QFrame()

        metrics_layout = QGridLayout(
            self.metrics_frame
        )

        metrics_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        metrics_layout.setSpacing(
            12
        )

        (
            self.portfolio_value_card,
            self.portfolio_value_value,
        ) = self._create_metric_card(
            "PORTFOLIO VALUE"
        )

        (
            self.invested_value_card,
            self.invested_value_value,
        ) = self._create_metric_card(
            "INVESTED MARKET VALUE"
        )

        (
            self.cash_balance_card,
            self.cash_balance_value,
        ) = self._create_metric_card(
            "CASH BALANCE"
        )

        (
            self.positions_card,
            self.positions_value,
        ) = self._create_metric_card(
            "POSITIONS"
        )

        (
            self.transactions_card,
            self.transactions_value,
        ) = self._create_metric_card(
            "TRANSACTIONS"
        )

        (
            self.snapshots_card,
            self.snapshots_value,
        ) = self._create_metric_card(
            "GROWTH MULTIPLE"
        )

        metrics_layout.addWidget(
            self.portfolio_value_card,
            0,
            0,
        )

        metrics_layout.addWidget(
            self.invested_value_card,
            0,
            1,
        )

        metrics_layout.addWidget(
            self.cash_balance_card,
            0,
            2,
        )

        metrics_layout.addWidget(
            self.positions_card,
            1,
            0,
        )

        metrics_layout.addWidget(
            self.transactions_card,
            1,
            1,
        )

        metrics_layout.addWidget(
            self.snapshots_card,
            1,
            2,
        )

        root.addWidget(
            self.metrics_frame
        )

        # --------------------------------------------------
        # PORTFOLIO VS NIFTY 50 SCORECARD
        # --------------------------------------------------
        self.benchmark_frame = QFrame()
        self.benchmark_frame.setObjectName("metricCard")
        benchmark_layout = QVBoxLayout(self.benchmark_frame)
        benchmark_layout.setContentsMargins(16, 14, 16, 14)
        benchmark_layout.setSpacing(10)

        benchmark_title = QLabel("Portfolio vs Nifty 50")
        benchmark_title.setObjectName("sectionTitle")
        benchmark_layout.addWidget(benchmark_title)

        bm_metrics = QHBoxLayout()
        bm_metrics.setSpacing(12)

        (
            self.bm_portfolio_return_card,
            self.bm_portfolio_return_value,
        ) = self._create_metric_card("ABSOLUTE RETURN")

        (
            self.bm_nifty_return_card,
            self.bm_nifty_return_value,
        ) = self._create_metric_card("BENCHMARK RETURN")

        (
            self.bm_alpha_return_card,
            self.bm_alpha_return_value,
        ) = self._create_metric_card("ALPHA")

        (
            self.bm_status_card,
            self.bm_status_value,
        ) = self._create_metric_card("STATUS")

        bm_metrics.addWidget(self.bm_portfolio_return_card)
        bm_metrics.addWidget(self.bm_nifty_return_card)
        bm_metrics.addWidget(self.bm_alpha_return_card)
        bm_metrics.addWidget(self.bm_status_card)

        benchmark_layout.addLayout(bm_metrics)

        root.addWidget(self.benchmark_frame)

        # --------------------------------------------------
        # PORTFOLIO INTELLIGENCE (read-only display)
        # --------------------------------------------------

        from services.portfolio_intelligence_score_service import (
            PortfolioIntelligenceScore,
        )

        self.intelligence_frame = QFrame()
        intelligence_layout = QVBoxLayout(self.intelligence_frame)
        intelligence_layout.setContentsMargins(0, 0, 0, 0)
        intelligence_layout.setSpacing(8)

        intelligence_title = QLabel("Portfolio Intelligence")
        intelligence_title.setObjectName("sectionTitle")
        intelligence_layout.addWidget(intelligence_title)

        # Overall metric cards: Overall Score | Grade | Health Score
        pi_metrics = QHBoxLayout()
        (
            self.portfolio_score_card,
            self.portfolio_score_value,
        ) = self._create_metric_card("OVERALL SCORE")

        (
            self.portfolio_grade_card,
            self.portfolio_grade_value,
        ) = self._create_metric_card("GRADE")

        (
            self.portfolio_health_card,
            self.portfolio_health_value,
        ) = self._create_metric_card("HEALTH SCORE")

        pi_metrics.addWidget(self.portfolio_score_card)
        pi_metrics.addWidget(self.portfolio_grade_card)
        pi_metrics.addWidget(self.portfolio_health_card)

        intelligence_layout.addLayout(pi_metrics)

        # Component scores (explicit fields)
        comps_layout = QGridLayout()
        comps_layout.setContentsMargins(0, 6, 0, 6)
        comps_layout.setHorizontalSpacing(24)
        comps_layout.setVerticalSpacing(6)

        # Left column
        div_title = QLabel("Diversification")
        div_title.setObjectName("metricTitle")
        self.pi_diversification_value = QLabel("-")
        self.pi_diversification_value.setObjectName("metricValue")
        comps_layout.addWidget(div_title, 0, 0)
        comps_layout.addWidget(self.pi_diversification_value, 1, 0)

        pos_title = QLabel("Position Sizing")
        pos_title.setObjectName("metricTitle")
        self.pi_position_sizing_value = QLabel("-")
        self.pi_position_sizing_value.setObjectName("metricValue")
        comps_layout.addWidget(pos_title, 2, 0)
        comps_layout.addWidget(self.pi_position_sizing_value, 3, 0)

        # Right column
        conc_title = QLabel("Concentration")
        conc_title.setObjectName("metricTitle")
        self.pi_concentration_value = QLabel("-")
        self.pi_concentration_value.setObjectName("metricValue")
        comps_layout.addWidget(conc_title, 0, 1)
        comps_layout.addWidget(self.pi_concentration_value, 1, 1)

        weight_title = QLabel("Weight Balance")
        weight_title.setObjectName("metricTitle")
        self.pi_weight_balance_value = QLabel("-")
        self.pi_weight_balance_value.setObjectName("metricValue")
        comps_layout.addWidget(weight_title, 2, 1)
        comps_layout.addWidget(self.pi_weight_balance_value, 3, 1)

        # Structure (span full width)
        struct_title = QLabel("Structure")
        struct_title.setObjectName("metricTitle")
        self.pi_structure_value = QLabel("-")
        self.pi_structure_value.setObjectName("metricValue")
        comps_layout.addWidget(struct_title, 4, 0, 1, 2)
        comps_layout.addWidget(self.pi_structure_value, 5, 0, 1, 2)

        intelligence_layout.addLayout(comps_layout)

        # Strengths / Weaknesses / Warnings / Summary
        lists_layout = QHBoxLayout()

        strengths_box = QVBoxLayout()
        strengths_title = QLabel("Strengths")
        strengths_title.setObjectName("metricTitle")
        self.pi_strengths_label = QLabel("No data available.")
        self.pi_strengths_label.setWordWrap(True)
        strengths_box.addWidget(strengths_title)
        strengths_box.addWidget(self.pi_strengths_label)

        weaknesses_box = QVBoxLayout()
        weaknesses_title = QLabel("Weaknesses")
        weaknesses_title.setObjectName("metricTitle")
        self.pi_weaknesses_label = QLabel("No data available.")
        self.pi_weaknesses_label.setWordWrap(True)
        weaknesses_box.addWidget(weaknesses_title)
        weaknesses_box.addWidget(self.pi_weaknesses_label)

        warnings_box = QVBoxLayout()
        warnings_title = QLabel("Warnings")
        warnings_title.setObjectName("metricTitle")
        self.pi_warnings_label = QLabel("No data available.")
        self.pi_warnings_label.setWordWrap(True)
        warnings_box.addWidget(warnings_title)
        warnings_box.addWidget(self.pi_warnings_label)

        summary_box = QVBoxLayout()
        summary_title = QLabel("Summary")
        summary_title.setObjectName("metricTitle")
        self.pi_summary_label = QLabel("No data available.")
        self.pi_summary_label.setWordWrap(True)
        summary_box.addWidget(summary_title)
        summary_box.addWidget(self.pi_summary_label)

        lists_layout.addLayout(strengths_box)
        lists_layout.addLayout(weaknesses_box)
        lists_layout.addLayout(warnings_box)
        lists_layout.addLayout(summary_box)

        intelligence_layout.addLayout(lists_layout)

        # --------------------------------------------------
        # PORTFOLIO ACTION CENTER (presentation-only)
        # Inserted into the existing intelligence layout beneath the lists
        # --------------------------------------------------
        self.action_center = PortfolioActionCenter(self)
        # Initialize with empty actions
        self.action_center.load_actions({
            "status": "OK",
            "buy": [],
            "reduce": [],
            "hold": [],
            "watch": [],
        })
        intelligence_layout.addWidget(self.action_center)

        # Recommendation detail panel (visual-only, starts cleared)
        self.recommendation_detail_panel = RecommendationDetailPanel(self)
        self.recommendation_detail_panel.clear()
        intelligence_layout.addWidget(self.recommendation_detail_panel)

        # Connect action center item clicks & selection changes to recommendation detail panel display
        try:
            for lw in (
                self.action_center.buy_list,
                self.action_center.reduce_list,
                self.action_center.hold_list,
                self.action_center.watch_list,
            ):
                lw.itemClicked.connect(self._show_recommendation_details)
                lw.currentItemChanged.connect(
                    lambda current, previous: self._show_recommendation_details(current)
                )
        except Exception:
            # Defensive: if any list is missing or connection fails, ignore
            pass

        self.allocation_frame = self._build_investment_allocation_ui()
        root.addWidget(self.allocation_frame)

        root.addWidget(self.intelligence_frame)

        # --------------------------------------------------
        # EMPTY STATE
        # --------------------------------------------------

        self.empty_frame = QFrame()

        self.empty_layout = QVBoxLayout(
            self.empty_frame
        )

        self.empty_layout.setAlignment(
            Qt.AlignCenter
        )

        self.empty_layout.setSpacing(
            10
        )

        self.empty_title = QLabel(
            "No portfolio created yet."
        )

        self.empty_title.setObjectName(
            "emptyTitle"
        )

        self.empty_title.setAlignment(
            Qt.AlignCenter
        )

        self.empty_text = QLabel(
            "Alpha 12 research selections are not holdings until "
            "an investment recommendation is explicitly confirmed."
        )

        self.empty_text.setObjectName(
            "emptyText"
        )

        self.empty_text.setWordWrap(
            True
        )

        self.empty_text.setAlignment(
            Qt.AlignCenter
        )

        self.empty_layout.addStretch()

        self.empty_layout.addWidget(
            self.empty_title
        )

        self.empty_layout.addWidget(
            self.empty_text
        )

        self.empty_layout.addStretch()

        root.addWidget(
            self.empty_frame,
            1,
        )

        # --------------------------------------------------
        # HOLDINGS
        # --------------------------------------------------

        self.holdings_frame = QFrame()

        holdings_layout = QVBoxLayout(
            self.holdings_frame
        )

        holdings_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        holdings_layout.setSpacing(
            10
        )

        holdings_title = QLabel(
            "Portfolio Holdings"
        )

        holdings_title.setObjectName(
            "sectionTitle"
        )

        holdings_header = QHBoxLayout()

        holdings_header.addWidget(
            holdings_title
        )

        holdings_header.addStretch()

        self.correct_purchase_button = QPushButton(
            "Correct Purchase Entry"
        )

        self.correct_purchase_button.setEnabled(
            False
        )

        self.correct_purchase_button.clicked.connect(
            self.correct_selected_purchase
        )

        holdings_header.addWidget(
            self.correct_purchase_button
        )

        holdings_layout.addLayout(
            holdings_header
        )

        self.table = QTableWidget()

        self.table.setMinimumHeight(420)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.table.setColumnCount(
            14
        )

        self.table.setHorizontalHeaderLabels([
            "Rank",
            "Symbol",
            "Qty",
            "Avg Cost",
            "Actual Purchase Value",
            "Price",
            "Market Value",
            "P/L",
            "P/L %",
            "Target %",
            "Actual %",
            "Drift %",
            "Sector",
            "Category",
        ])

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.itemSelectionChanged.connect(
            self._update_correction_button
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header_view = (
            self.table.horizontalHeader()
        )

        header_view.setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        header_view.setStretchLastSection(
            True
        )

        holdings_layout.addWidget(
            self.table,
            1,
        )

        root.addWidget(
            self.holdings_frame,
            1,
        )

        self.holdings_frame.hide()

    def _show_recommendation_details(self, item) -> None:
        """Display the full recommendation in the detail panel when an item is clicked or selected.

        The method is defensive and ignores placeholder rows and malformed data.
        """
        try:
            if item is None:
                return

            text = item.text() if hasattr(item, "text") else None
            if text == "Nothing to display":
                return

            recommendation = item.data(Qt.UserRole) if hasattr(item, "data") else None

            if recommendation is not None:
                self.recommendation_detail_panel.load_recommendation(recommendation)
        except Exception:
            # Swallow exceptions to keep UI responsive
            pass

    def _select_first_recommendation(self) -> None:
        """Automatically select the first available recommendation item after data load."""
        try:
            for lw in (
                self.action_center.buy_list,
                self.action_center.reduce_list,
                self.action_center.hold_list,
                self.action_center.watch_list,
            ):
                if lw.count() > 0:
                    first_item = lw.item(0)
                    if first_item and first_item.text() != "Nothing to display":
                        lw.setCurrentItem(first_item)
                        self._show_recommendation_details(first_item)
                        break
        except Exception:
            pass

    # ======================================================
    # METRIC CARD
    # ======================================================


    # ======================================================
    # INITIAL INVESTMENT WORKFLOW
    # ======================================================

    def set_alpha12_provider(
        self,
        provider,
    ):

        self.alpha12_provider = (
            provider
        )

    def _current_alpha12(
        self,
    ):

        if not callable(
            self.alpha12_provider
        ):

            return []

        try:

            rows = (
                self.alpha12_provider()
            )

        except Exception:

            return []

        if not isinstance(
            rows,
            list,
        ):

            return []

        return rows

    def prepare_initial_investment(
        self,
    ):

        alpha12 = (
            self._current_alpha12()
        )

        if len(alpha12) != 12:

            QMessageBox.information(
                self,
                "AlphaForge Portfolio",
                "No current Alpha 12 production result is "
                "available.\n\n"
                "Run Production Radar first, review the "
                "Alpha 12 selection, then return to Portfolio.",
            )

            return

        capital, accepted = (
            QInputDialog.getDouble(
                self,
                "Initial Investment",
                "Enter investment capital (₹):",
                500000.0,
                1.0,
                1000000000.0,
                2,
            )
        )

        if not accepted:

            return

        price_map = {}

        missing_prices = []

        price_errors = {}

        # --------------------------------------------------
        # MARKET PRICE BRIDGE
        #
        # Alpha 12 remains authoritative for stock selection.
        # Market data is used only to obtain execution prices.
        #
        # 1. Prefer any valid price already carried by the
        #    production Alpha 12 result.
        #
        # 2. Fetch only missing prices through AlphaForge's
        #    existing stock_service.
        #
        # 3. Require all 12 prices before capital deployment.
        # --------------------------------------------------

        for row in alpha12:

            if not isinstance(
                row,
                dict,
            ):

                continue

            symbol = str(
                row.get(
                    "symbol",
                    "",
                )
            ).strip().upper()

            if not symbol:

                continue

            embedded_price = self._safe_float(

                row.get(
                    "current_price",
                    row.get(
                        "price",
                        row.get(
                            "ltp",
                            0.0,
                        ),
                    ),
                ),

                0.0,

            )

            if embedded_price > 0:

                price_map[
                    symbol
                ] = embedded_price

                continue

            # ----------------------------------------------
            # Existing AlphaForge market-data service
            # ----------------------------------------------

            try:

                stock_data = (
                    get_stock_data(
                        symbol
                    )
                )

            except Exception as exc:

                missing_prices.append(
                    symbol
                )

                price_errors[
                    symbol
                ] = str(
                    exc
                )

                continue

            if not isinstance(
                stock_data,
                dict,
            ):

                missing_prices.append(
                    symbol
                )

                price_errors[
                    symbol
                ] = (
                    "Invalid market-data response"
                )

                continue

            if stock_data.get(
                "error"
            ):

                missing_prices.append(
                    symbol
                )

                price_errors[
                    symbol
                ] = str(
                    stock_data.get(
                        "error"
                    )
                )

                continue

            fetched_price = (
                self._safe_float(
                    stock_data.get(
                        "price",
                        0.0,
                    ),
                    0.0,
                )
            )

            if fetched_price <= 0:

                missing_prices.append(
                    symbol
                )

                price_errors[
                    symbol
                ] = (
                    "No valid current market price"
                )

                continue

            price_map[
                symbol
            ] = fetched_price

        # --------------------------------------------------
        # STRICT 12 / 12 VALIDATION
        # --------------------------------------------------

        alpha12_symbols = [

            str(
                row.get(
                    "symbol",
                    "",
                )
            ).strip().upper()

            for row in alpha12

            if isinstance(
                row,
                dict,
            )

            and str(
                row.get(
                    "symbol",
                    "",
                )
            ).strip()

        ]

        unresolved = [

            symbol

            for symbol in alpha12_symbols

            if (
                symbol not in price_map
                or self._safe_float(
                    price_map.get(
                        symbol,
                        0.0,
                    ),
                    0.0,
                ) <= 0
            )

        ]

        # Preserve order and remove duplicates.

        unresolved = list(
            dict.fromkeys(
                unresolved
            )
        )

        if (
            len(alpha12_symbols) != 12
            or len(price_map) != 12
            or unresolved
        ):

            details = []

            for symbol in unresolved:

                error = price_errors.get(
                    symbol,
                    "Price unavailable",
                )

                details.append(
                    f"{symbol}: {error}"
                )

            detail_text = (
                "\n".join(
                    details
                )
                if details
                else
                "Unknown market-price validation failure."
            )

            QMessageBox.warning(
                self,
                "AlphaForge Portfolio",
                "Unable to prepare the investment plan "
                "because AlphaForge could not obtain a valid "
                "current market price for all 12 Alpha stocks."
                "\n\n"
                "No portfolio has been created."
                "\n"
                "No stock has been substituted."
                "\n\n"
                "Unresolved market prices:"
                "\n"
                + detail_text,
            )

            return

        try:

            result = (
                self.portfolio_service
                .prepare_initial_investment(

                    alpha12=
                        alpha12,

                    capital=
                        capital,

                    price_map=
                        price_map,

                )
            )

        except Exception as exc:

        
            self._show_error(
                str(exc)
            )

            return

        if (
            not isinstance(
                result,
                dict,
            )
            or result.get(
                "status"
            ) != "OK"
        ):

            QMessageBox.warning(
                self,
                "AlphaForge Portfolio",
                str(
                    result.get(
                        "error",
                        "Initial investment recommendation failed.",
                    )
                    if isinstance(
                        result,
                        dict,
                    )
                    else
                    "Initial investment recommendation failed."
                ),
            )

            return

        self.pending_initial_recommendation = (
            result
        )

        self._show_initial_recommendation(
            result
        )

    def _show_initial_recommendation(
        self,
        recommendation,
    ):

        allocations = (
            recommendation.get(
                "allocations",
                [],
            )
        )

        if not isinstance(
            allocations,
            list,
        ):

            allocations = []

        invested = self._safe_float(

            recommendation.get(
                "recommended_investment",
                recommendation.get(
                    "invested_amount",
                    0.0,
                ),
            ),

            0.0,

        )

        cash = self._safe_float(

            recommendation.get(
                "recommended_cash",
                recommendation.get(
                    "cash_remaining",
                    0.0,
                ),
            ),

            0.0,

        )

        message = (

            "AlphaForge has prepared an initial investment "
            "recommendation.\n\n"

            f"Stocks: {len(allocations)}\n"
            f"Recommended investment: Rs {invested:,.2f}\n"
            f"Recommended cash remaining: Rs {cash:,.2f}\n\n"

            "The next screen lets you record the ACTUAL "
            "execution.\n\n"

            "Recommended quantity and price are preserved "
            "for reference. Edit Actual Qty or Actual Buy "
            "Price only when your real purchase differs "
            "from the recommendation.\n\n"

            "No holdings are created until final confirmation."
        )

        answer = QMessageBox.question(

            self,

            "Review Initial Investment",

            message,

            QMessageBox.Yes
            | QMessageBox.No,

            QMessageBox.Yes,

        )

        if answer != QMessageBox.Yes:

            self.status_label.setText(
                "Initial investment recommendation "
                "prepared but not confirmed."
            )

            return

        confirmed_buys = (
            self._show_execution_dialog(
                recommendation
            )
        )

        if confirmed_buys is None:

            self.status_label.setText(
                "Actual execution review cancelled. "
                "No portfolio was created."
            )

            return

        self.confirm_initial_investment(
            confirmed_buys=
                confirmed_buys
        )

    def _show_execution_dialog(
        self,
        recommendation,
    ):

        allocations = (
            recommendation.get(
                "allocations",
                [],
            )
        )

        if not isinstance(
            allocations,
            list,
        ):

            allocations = []

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Confirm Actual Initial Execution"
        )

        dialog.resize(
            1150,
            650,
        )

        root = QVBoxLayout(
            dialog
        )

        title = QLabel(
            "Review Actual Purchase Execution"
        )

        title.setObjectName(
            "sectionTitle"
        )

        root.addWidget(
            title
        )

        help_text = QLabel(

            "AlphaForge recommendation is shown on the left. "
            "Actual Qty and Actual Buy Price are editable. "
            "Actual Purchase Value is calculated automatically. "
            "Use zero quantity for a stock that was not actually purchased."

        )

        help_text.setWordWrap(
            True
        )

        root.addWidget(
            help_text
        )

        table = QTableWidget()

        table.setColumnCount(
            7
        )

        table.setHorizontalHeaderLabels([

            "Symbol",
            "Recommended Qty",
            "Reference Price",
            "Recommended Value",
            "Actual Qty",
            "Actual Buy Price",
            "Actual Purchase Value",

        ])

        table.setRowCount(
            len(
                allocations
            )
        )

        table.setAlternatingRowColors(
            True
        )

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        editors = []

        for row_index, row in enumerate(
            allocations
        ):

            if not isinstance(
                row,
                dict,
            ):

                row = {}

            symbol = str(
                row.get(
                    "symbol",
                    "",
                )
            ).strip().upper()

            recommended_qty = int(
                self._safe_float(
                    row.get(
                        "quantity",
                        row.get(
                            "buy_quantity",
                            row.get(
                                "allocated_quantity",
                                0,
                            ),
                        ),
                    ),
                    0.0,
                )
            )

            reference_price = self._safe_float(
                row.get(
                    "price",
                    0.0,
                ),
                0.0,
            )

            recommended_value = self._safe_float(

                row.get(
                    "allocated_amount",
                    row.get(
                        "amount",
                        (
                            recommended_qty
                            * reference_price
                        ),
                    ),
                ),

                0.0,

            )

            symbol_item = QTableWidgetItem(
                symbol
            )

            symbol_item.setFlags(
                symbol_item.flags()
                & ~Qt.ItemIsEditable
            )

            table.setItem(
                row_index,
                0,
                symbol_item,
            )

            recommended_qty_item = QTableWidgetItem(
                str(
                    recommended_qty
                )
            )

            recommended_qty_item.setTextAlignment(
                Qt.AlignCenter
            )

            recommended_qty_item.setFlags(
                recommended_qty_item.flags()
                & ~Qt.ItemIsEditable
            )

            table.setItem(
                row_index,
                1,
                recommended_qty_item,
            )

            reference_price_item = QTableWidgetItem(
                self._money(
                    reference_price
                )
            )

            reference_price_item.setTextAlignment(
                Qt.AlignCenter
            )

            reference_price_item.setFlags(
                reference_price_item.flags()
                & ~Qt.ItemIsEditable
            )

            table.setItem(
                row_index,
                2,
                reference_price_item,
            )

            recommended_value_item = QTableWidgetItem(
                self._money(
                    recommended_value
                )
            )

            recommended_value_item.setTextAlignment(
                Qt.AlignCenter
            )

            recommended_value_item.setFlags(
                recommended_value_item.flags()
                & ~Qt.ItemIsEditable
            )

            table.setItem(
                row_index,
                3,
                recommended_value_item,
            )

            qty_editor = QSpinBox()

            qty_editor.setRange(
                0,
                100000000,
            )

            qty_editor.setValue(
                max(
                    recommended_qty,
                    0,
                )
            )

            table.setCellWidget(
                row_index,
                4,
                qty_editor,
            )

            # ==================================================
            # DIRECT ACTUAL BUY PRICE ENTRY
            #
            # Broker execution prices should behave like a
            # normal data-entry field rather than a spin box.
            #
            # Actual Purchase Value remains calculated from:
            #
            #     Actual Qty * Actual Buy Price
            #
            # ==================================================

            price_editor = QLineEdit()

            price_editor.setText(
                f"{max(reference_price, 0.0):.2f}"
            )

            price_editor.setAlignment(
                Qt.AlignCenter
            )

            price_editor.setToolTip(
                "Enter the exact actual broker purchase price. "
                "Example: 2398.75"
            )

            price_editor.setPlaceholderText(
                "0.00"
            )

            table.setCellWidget(
                row_index,
                5,
                price_editor,
            )

            actual_value_item = QTableWidgetItem(
                self._money(
                    recommended_qty
                    * reference_price
                )
            )

            actual_value_item.setTextAlignment(
                Qt.AlignCenter
            )

            actual_value_item.setFlags(
                actual_value_item.flags()
                & ~Qt.ItemIsEditable
            )

            table.setItem(
                row_index,
                6,
                actual_value_item,
            )

            editors.append({

                "symbol":
                    symbol,

                "qty":
                    qty_editor,

                "price":
                    price_editor,

                "value_item":
                    actual_value_item,

            })

            def update_value(
                _value=None,
                qty_widget=qty_editor,
                price_widget=price_editor,
                value_widget=actual_value_item,
            ):

                actual_price = self._safe_float(
                    price_widget.text(),
                    0.0,
                )

                actual_value = (

                    qty_widget.value()
                    * actual_price

                )

                value_widget.setText(
                    self._money(
                        actual_value
                    )
                )

            qty_editor.valueChanged.connect(
                update_value
            )

            price_editor.textChanged.connect(
                update_value
            )

        root.addWidget(
            table
        )

        summary_label = QLabel(
            ""
        )

        summary_label.setWordWrap(
            True
        )

        root.addWidget(
            summary_label
        )

        def refresh_summary():

            total_actual = 0.0

            for editor in editors:

                total_actual += (

                    editor[
                        "qty"
                    ].value()

                    * self._safe_float(
                        editor[
                            "price"
                        ].text(),
                        0.0,
                    )

                )

            capital = self._safe_float(
                recommendation.get(
                    "capital",
                    0.0,
                ),
                0.0,
            )

            remaining = (
                capital
                - total_actual
            )

            summary_label.setText(

                f"Actual purchase total: "
                f"{self._money(total_actual)}    |    "

                f"Capital: "
                f"{self._money(capital)}    |    "

                f"Cash after execution: "
                f"{self._money(remaining)}"

            )

        for editor in editors:

            editor[
                "qty"
            ].valueChanged.connect(
                refresh_summary
            )

            editor[
                "price"
            ].textChanged.connect(
                refresh_summary
            )

        refresh_summary()

        buttons = QDialogButtonBox(

            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel

        )

        buttons.button(
            QDialogButtonBox.Ok
        ).setText(
            "Confirm Actual Execution"
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        root.addWidget(
            buttons
        )

        if dialog.exec() != QDialog.Accepted:

            return None

        confirmed_buys = []

        total_actual = 0.0

        for editor in editors:

            symbol = editor[
                "symbol"
            ]

            quantity = editor[
                "qty"
            ].value()

            price = self._safe_float(
                editor[
                    "price"
                ].text(),
                0.0,
            )

            if quantity <= 0:

                continue

            if price <= 0:

                QMessageBox.warning(

                    self,

                    "Invalid Actual Execution",

                    f"{symbol} has a positive quantity "
                    "but no valid actual purchase price.",

                )

                return None

            amount = (
                quantity
                * price
            )

            total_actual += (
                amount
            )

            confirmed_buys.append({

                "symbol":
                    symbol,

                "quantity":
                    quantity,

                "price":
                    price,

                "amount":
                    round(
                        amount,
                        2,
                    ),

            })

        capital = self._safe_float(
            recommendation.get(
                "capital",
                0.0,
            ),
            0.0,
        )

        if total_actual > (
            capital
            + 0.01
        ):

            QMessageBox.warning(

                self,

                "Actual Execution Exceeds Capital",

                "Actual purchases exceed the available "
                "initial investment capital.\n\n"

                f"Capital: {self._money(capital)}\n"
                f"Actual purchases: {self._money(total_actual)}",

            )

            return None

        answer = QMessageBox.question(

            self,

            "Final Execution Confirmation",

            "Create the persistent AlphaForge portfolio "
            "using these ACTUAL executions?\n\n"

            f"Actual invested: {self._money(total_actual)}\n"
            f"Cash remaining: "
            f"{self._money(capital - total_actual)}\n\n"

            "After confirmation, these quantities and "
            "purchase prices become the authoritative "
            "portfolio holdings.",

            QMessageBox.Yes
            | QMessageBox.No,

            QMessageBox.No,

        )

        if answer != QMessageBox.Yes:

            return None

        return confirmed_buys

    def confirm_initial_investment(
        self,
        confirmed_buys=None,
    ):

        recommendation = (
            self.pending_initial_recommendation
        )

        if not isinstance(
            recommendation,
            dict,
        ):

            return

        try:

            result = (
                self.portfolio_service
                .confirm_initial_investment(

                    recommendation=
                        recommendation,

                    confirmed_buys=
                        confirmed_buys,

                )
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "AlphaForge Portfolio",
                str(exc),
            )

            return

        if (
            not isinstance(
                result,
                dict,
            )
            or result.get(
                "status"
            ) != "OK"
        ):

            QMessageBox.warning(
                self,
                "AlphaForge Portfolio",
                str(
                    result.get(
                        "error",
                        "Investment confirmation failed.",
                    )
                    if isinstance(
                        result,
                        dict,
                    )
                    else
                    "Investment confirmation failed."
                ),
            )

            return

        self.pending_initial_recommendation = None

        QMessageBox.information(
            self,
            "AlphaForge Portfolio",
            "Initial investment confirmed.\n\n"
            "The portfolio is now persistent and "
            "the confirmed positions are real holdings "
            "inside AlphaForge.",
        )

        self.load_portfolio()

    def _create_metric_card(
        self,
        title,
    ):

        frame = QFrame()

        frame.setObjectName(
            "metricCard"
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "metricTitle"
        )

        value_label = QLabel(
            "-"
        )

        value_label.setObjectName(
            "metricValue"
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        return (
            frame,
            value_label,
        )

    # ======================================================
    # FORMATTERS
    # ======================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
    ):

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return default

    @staticmethod
    def _format_timestamp(
        raw_ts,
    ):
        if not raw_ts:
            return ""
        try:
            from datetime import datetime
            ts_str = str(raw_ts).strip()
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            return dt.strftime("%d %b %Y %H:%M")
        except Exception:
            return str(raw_ts)

    @staticmethod
    def _money(
        value,
    ):

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            value = 0.0

        return (
            f"Rs {value:,.2f}"
        )

    @staticmethod
    def _number(
        value,
        decimals=2,
    ):

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            value = 0.0

        return (
            f"{value:,.{decimals}f}"
        )

    # ======================================================
    # DATA LOAD
    # ======================================================

    # ======================================================
    # CONTROLLED PURCHASE ENTRY CORRECTION
    #
    # This workflow corrects historical execution data only.
    # It does NOT represent a new BUY, SELL, SIP or rebalance.
    # ======================================================

    def _update_correction_button(
        self,
    ):

        if not hasattr(
            self,
            "correct_purchase_button",
        ):

            return

        self.correct_purchase_button.setEnabled(
            self.table.currentRow() >= 0
        )

    def _selected_portfolio_symbol(
        self,
    ):

        row = self.table.currentRow()

        if row < 0:

            return ""

        item = self.table.item(
            row,
            1,
        )

        if item is None:

            return ""

        return str(
            item.text()
        ).strip().upper()

    def correct_selected_purchase(
        self,
    ):

        symbol = (
            self._selected_portfolio_symbol()
        )

        if not symbol:

            QMessageBox.information(
                self,
                "Correct Purchase Entry",
                "Select a portfolio holding first.",
            )

            return

        result = (
            self.portfolio_service
            .get_purchase_transactions(
                symbol
            )
        )

        if (
            not isinstance(
                result,
                dict,
            )
            or result.get(
                "status"
            ) != "OK"
        ):

            QMessageBox.warning(
                self,
                "Correct Purchase Entry",
                str(
                    result.get(
                        "error",
                        "Unable to load purchase history.",
                    )
                    if isinstance(
                        result,
                        dict,
                    )
                    else
                    "Unable to load purchase history."
                ),
            )

            return

        purchases = result.get(
            "purchases",
            [],
        )

        if not isinstance(
            purchases,
            list,
        ):

            purchases = []

        if not purchases:

            QMessageBox.information(
                self,
                "Correct Purchase Entry",
                f"No BUY transaction was found for {symbol}.",
            )

            return

        purchase = None

        if len(
            purchases
        ) == 1:

            purchase = purchases[
                0
            ]

        else:

            labels = []

            purchase_map = {}

            for purchase_row in purchases:

                transaction_index = int(
                    self._safe_float(
                        purchase_row.get(
                            "transaction_index",
                            -1,
                        ),
                        -1,
                    )
                )

                quantity = int(
                    self._safe_float(
                        purchase_row.get(
                            "quantity",
                            0,
                        ),
                        0.0,
                    )
                )

                price = self._safe_float(
                    purchase_row.get(
                        "price",
                        0.0,
                    ),
                    0.0,
                )

                amount = self._safe_float(
                    purchase_row.get(
                        "amount",
                        quantity * price,
                    ),
                    0.0,
                )

                timestamp = str(
                    purchase_row.get(
                        "timestamp",
                        "",
                    )
                )

                source = str(
                    purchase_row.get(
                        "source",
                        "BUY",
                    )
                )

                label = (
                    f"{timestamp} | "
                    f"{source} | "
                    f"{quantity} shares @ "
                    f"Rs {price:,.2f} | "
                    f"Rs {amount:,.2f}"
                )

                labels.append(
                    label
                )

                purchase_map[
                    label
                ] = purchase_row

            selected_label, accepted = (
                QInputDialog.getItem(
                    self,
                    "Select Purchase Entry",
                    (
                        f"{symbol} has multiple BUY "
                        "transactions.\n"
                        "Select the exact purchase "
                        "you want to correct:"
                    ),
                    labels,
                    0,
                    False,
                )
            )

            if not accepted:

                return

            purchase = purchase_map.get(
                selected_label
            )

        if not isinstance(
            purchase,
            dict,
        ):

            return

        self._show_purchase_correction_dialog(
            symbol=
                symbol,

            purchase=
                purchase,
        )

    def _show_purchase_correction_dialog(
        self,
        symbol,
        purchase,
    ):

        transaction_index = int(
            self._safe_float(
                purchase.get(
                    "transaction_index",
                    -1,
                ),
                -1,
            )
        )

        old_quantity = int(
            self._safe_float(
                purchase.get(
                    "quantity",
                    0,
                ),
                0.0,
            )
        )

        old_price = self._safe_float(
            purchase.get(
                "price",
                0.0,
            ),
            0.0,
        )

        old_amount = self._safe_float(
            purchase.get(
                "amount",
                old_quantity * old_price,
            ),
            0.0,
        )

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            f"Correct Purchase Entry - {symbol}"
        )

        dialog.setMinimumWidth(
            620
        )

        layout = QVBoxLayout(
            dialog
        )

        notice = QLabel(
            "This corrects a saved execution entry only. "
            "It does not create a new trade or rebalance."
        )

        notice.setWordWrap(
            True
        )

        layout.addWidget(
            notice
        )

        details = QLabel(
            f"Symbol: {symbol}\n"
            f"Original Qty: {old_quantity}\n"
            f"Original Buy Price: Rs {old_price:,.2f}\n"
            f"Original Purchase Value: Rs {old_amount:,.2f}"
        )

        details.setWordWrap(
            True
        )

        layout.addWidget(
            details
        )

        form = QGridLayout()

        form.addWidget(
            QLabel(
                "Correct Qty"
            ),
            0,
            0,
        )

        quantity_editor = QSpinBox()

        quantity_editor.setRange(
            0,
            100000000,
        )

        quantity_editor.setValue(
            old_quantity
        )

        form.addWidget(
            quantity_editor,
            0,
            1,
        )

        form.addWidget(
            QLabel(
                "Correct Buy Price"
            ),
            1,
            0,
        )

        price_editor = QLineEdit()

        price_editor.setText(
            f"{old_price:.2f}"
        )

        price_editor.setClearButtonEnabled(
            True
        )

        price_editor.selectAll()

        form.addWidget(
            price_editor,
            1,
            1,
        )

        form.addWidget(
            QLabel(
                "Corrected Purchase Value"
            ),
            2,
            0,
        )

        new_value_label = QLabel(
            "-"
        )

        form.addWidget(
            new_value_label,
            2,
            1,
        )

        form.addWidget(
            QLabel(
                "Cash Adjustment"
            ),
            3,
            0,
        )

        cash_delta_label = QLabel(
            "-"
        )

        form.addWidget(
            cash_delta_label,
            3,
            1,
        )

        layout.addLayout(
            form
        )

        def values():

            quantity = (
                quantity_editor.value()
            )

            price = self._safe_float(
                price_editor.text(),
                -1.0,
            )

            amount = (
                quantity
                * price
                if price >= 0
                else -1.0
            )

            cash_delta = (
                old_amount
                - amount
                if amount >= 0
                else 0.0
            )

            return (
                quantity,
                price,
                amount,
                cash_delta,
            )

        def refresh_preview():

            (
                quantity,
                price,
                amount,
                cash_delta,
            ) = values()

            if (
                quantity > 0
                and price <= 0
            ):

                new_value_label.setText(
                    "Enter a valid positive price"
                )

                cash_delta_label.setText(
                    "-"
                )

                return

            if (
                quantity == 0
                and price < 0
            ):

                new_value_label.setText(
                    "Enter a valid price"
                )

                cash_delta_label.setText(
                    "-"
                )

                return

            new_value_label.setText(
                self._money(
                    max(
                        amount,
                        0.0,
                    )
                )
            )

            if cash_delta > 0:

                cash_delta_label.setText(
                    f"+{self._money(cash_delta)} "
                    "returned to portfolio cash"
                )

            elif cash_delta < 0:

                cash_delta_label.setText(
                    f"-{self._money(abs(cash_delta))} "
                    "consumed from portfolio cash"
                )

            else:

                cash_delta_label.setText(
                    self._money(
                        0.0
                    )
                )

        quantity_editor.valueChanged.connect(
            refresh_preview
        )

        price_editor.textChanged.connect(
            refresh_preview
        )

        refresh_preview()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )

        buttons.button(
            QDialogButtonBox.Ok
        ).setText(
            "Review Correction"
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        layout.addWidget(
            buttons
        )

        if dialog.exec() != QDialog.Accepted:

            return

        (
            new_quantity,
            new_price,
            new_amount,
            cash_delta,
        ) = values()

        if new_quantity < 0:

            QMessageBox.warning(
                self,
                "Correct Purchase Entry",
                "Correct quantity cannot be negative.",
            )

            return

        if (
            new_quantity > 0
            and new_price <= 0
        ):

            QMessageBox.warning(
                self,
                "Correct Purchase Entry",
                "Correct buy price must be positive.",
            )

            return

        if (
            new_quantity == 0
            and new_price < 0
        ):

            QMessageBox.warning(
                self,
                "Correct Purchase Entry",
                "Correct buy price cannot be negative.",
            )

            return

        if (
            new_quantity == old_quantity
            and abs(
                new_price
                - old_price
            ) < 0.000001
        ):

            QMessageBox.information(
                self,
                "Correct Purchase Entry",
                "No change was entered.",
            )

            return

        if cash_delta > 0:

            cash_text = (
                f"Rs {cash_delta:,.2f} will be "
                "returned to portfolio cash."
            )

        elif cash_delta < 0:

            cash_text = (
                f"Rs {abs(cash_delta):,.2f} will be "
                "consumed from portfolio cash."
            )

        else:

            cash_text = (
                "Portfolio cash will not change."
            )

        confirmation = (
            "REVIEW PURCHASE ENTRY CORRECTION\n\n"
            f"Symbol: {symbol}\n\n"
            "OLD EXECUTION\n"
            f"Qty: {old_quantity}\n"
            f"Buy Price: Rs {old_price:,.2f}\n"
            f"Purchase Value: Rs {old_amount:,.2f}\n\n"
            "CORRECTED EXECUTION\n"
            f"Qty: {new_quantity}\n"
            f"Buy Price: Rs {new_price:,.2f}\n"
            f"Purchase Value: Rs {new_amount:,.2f}\n\n"
            f"{cash_text}\n\n"
            "This is an accounting correction only. "
            "It is not a new BUY, SELL or rebalance.\n\n"
            "Apply this correction?"
        )

        answer = QMessageBox.question(
            self,
            "Confirm Purchase Correction",
            confirmation,
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        result = (
            self.portfolio_service
            .correct_confirmed_buy(

                transaction_index=
                    transaction_index,

                quantity=
                    new_quantity,

                price=
                    new_price,

                reason=
                    "USER_CORRECTED_PURCHASE_ENTRY",

            )
        )

        if (
            not isinstance(
                result,
                dict,
            )
            or result.get(
                "status"
            ) != "OK"
        ):

            QMessageBox.warning(
                self,
                "Correct Purchase Entry",
                str(
                    result.get(
                        "error",
                        "Purchase correction failed.",
                    )
                    if isinstance(
                        result,
                        dict,
                    )
                    else
                    "Purchase correction failed."
                ),
            )

            return

        QMessageBox.information(
            self,
            "Correct Purchase Entry",
            (
                f"{symbol} purchase entry was corrected "
                "successfully.\n\n"
                "Portfolio cost, average cost and cash "
                "have been reconciled automatically."
            ),
        )

        self.load_portfolio()


    def load_portfolio(
        self,
    ):

        self.refresh_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Refreshing live market prices..."
        )

        try:

            refresh_res = (
                self.portfolio_service
                .refresh_portfolio()
            )

            if (
                isinstance(
                    refresh_res,
                    dict,
                )
                and refresh_res.get(
                    "status"
                )
                == "ERROR"
            ):

                raise RuntimeError(
                    refresh_res.get(
                        "error",
                        "Failed to refresh live market prices",
                    )
                )

            summary = (
                self.portfolio_service
                .get_portfolio_summary()
            )

            if (
                not isinstance(
                    summary,
                    dict,
                )
            ):

                raise ValueError(
                    "Portfolio service returned invalid data"
                )

            if (
                summary.get(
                    "status"
                )
                != "OK"
            ):

                error = summary.get(
                    "error",
                    "Unable to load portfolio state",
                )

                raise RuntimeError(
                    str(
                        error
                    )
                )

            self._render_summary(
                summary
            )

        except Exception as exc:


        
            self._show_error(
                str(
                    exc
                )
            )

        finally:

            self.refresh_button.setEnabled(
                True
            )

    # ======================================================
    # BENCHMARK RENDER
    # ======================================================

    def _render_performance_snapshot(self, snapshot) -> None:
        """Render PortfolioPerformanceSnapshot capital metrics into the metrics grid."""
        # Growth Multiple (replaces SNAPSHOTS card value)
        if snapshot is not None and hasattr(snapshot, "growth_multiple"):
            self.snapshots_value.setText(f"{snapshot.growth_multiple:.2f}x")

    def _render_benchmark_summary(self, bm_summary: dict, summary: Optional[dict] = None) -> None:
        """Render BenchmarkService scorecard and PortfolioPerformanceService capital metrics."""
        if not isinstance(bm_summary, dict):
            bm_summary = {}

        GREEN = "#16a34a"
        RED = "#dc2626"
        NEUTRAL = "#64748b"

        # ----------------------------------------------------
        # 1. Benchmark Scorecard (Source: BenchmarkService)
        # ----------------------------------------------------
        status_raw = str(bm_summary.get("status", "UNKNOWN")).upper()
        port_ret_1y = self._safe_float(bm_summary.get("portfolio_return_1y"), 0.0)
        nifty_ret_1y = self._safe_float(bm_summary.get("benchmark_return_1y"), 0.0)
        alpha_1y = self._safe_float(bm_summary.get("alpha_return_1y"), 0.0)

        fmt = "+.2f" if summary is not None else "+.1f"

        # Portfolio Return (1Y)
        if status_raw == "UNKNOWN" and port_ret_1y == 0.0:
            self.bm_portfolio_return_value.setText("N/A")
            self.bm_portfolio_return_value.setStyleSheet(f"color: {NEUTRAL}; font-weight: 700; font-size: 20px;")
        else:
            self.bm_portfolio_return_value.setText(f"{port_ret_1y:{fmt}}%")
            color = GREEN if port_ret_1y > 0 else (RED if port_ret_1y < 0 else NEUTRAL)
            self.bm_portfolio_return_value.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 20px;")

        # Benchmark Return (1Y)
        if status_raw == "UNKNOWN" and nifty_ret_1y == 0.0:
            self.bm_nifty_return_value.setText("N/A")
            self.bm_nifty_return_value.setStyleSheet(f"color: {NEUTRAL}; font-weight: 700; font-size: 20px;")
        else:
            self.bm_nifty_return_value.setText(f"{nifty_ret_1y:{fmt}}%")
            color = GREEN if nifty_ret_1y > 0 else (RED if nifty_ret_1y < 0 else NEUTRAL)
            self.bm_nifty_return_value.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 20px;")

        # Alpha (1Y)
        if status_raw == "UNKNOWN" and alpha_1y == 0.0:
            self.bm_alpha_return_value.setText("N/A")
            self.bm_alpha_return_value.setStyleSheet(f"color: {NEUTRAL}; font-weight: 700; font-size: 20px;")
        else:
            self.bm_alpha_return_value.setText(f"{alpha_1y:{fmt}}%")
            color = GREEN if alpha_1y > 0 else (RED if alpha_1y < 0 else NEUTRAL)
            self.bm_alpha_return_value.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 20px;")

        # Status Mapping
        if summary is not None:
            if alpha_1y > 0:
                bm_status_text = "OUTPERFORMING"
                bm_status_color = GREEN
            elif alpha_1y < 0:
                bm_status_text = "UNDERPERFORMING"
                bm_status_color = RED
            else:
                bm_status_text = "INLINE"
                bm_status_color = NEUTRAL
        else:
            if status_raw == "UNKNOWN" and alpha_1y == 0.0 and port_ret_1y == 0.0 and nifty_ret_1y == 0.0:
                bm_status_text = "Benchmark Data Unavailable"
                bm_status_color = NEUTRAL
            elif status_raw == "BEATING_BENCHMARK" or alpha_1y > 0:
                bm_status_text = "✓ Outperforming Nifty 50"
                bm_status_color = GREEN
            elif status_raw == "LAGGING_BENCHMARK" or alpha_1y < 0:
                bm_status_text = "⚠ Underperforming Nifty 50"
                bm_status_color = RED
            else:
                bm_status_text = "Benchmark Data Unavailable"
                bm_status_color = NEUTRAL

        self.bm_status_value.setText(bm_status_text)
        self.bm_status_value.setStyleSheet(f"color: {bm_status_color}; font-weight: 700; font-size: 15px;")

        # ----------------------------------------------------
        # 2. Capital Metrics (Source: PortfolioPerformanceService)
        # ----------------------------------------------------
        invested = 0.0
        current = 0.0
        if isinstance(summary, dict):
            invested = self._safe_float(summary.get("total_cost", summary.get("invested_market_value", 0.0)), 0.0)
            current = self._safe_float(summary.get("portfolio_value", 0.0), 0.0)

        snapshot = self.performance_service.calculate_performance(
            initial_value=invested,
            current_value=current,
        )

        self._render_performance_snapshot(snapshot)

    # ======================================================
    # RENDER
    # ======================================================

    def _render_summary(
        self,
        summary,
    ):

        portfolio_exists = bool(
            summary.get(
                "portfolio_exists",
                False,
            )
        )

        self.portfolio_value_value.setText(
            self._money(
                summary.get(
                    "portfolio_value",
                    0.0,
                )
            )
        )

        self.invested_value_value.setText(
            self._money(
                summary.get(
                    "invested_market_value",
                    0.0,
                )
            )
        )

        self.cash_balance_value.setText(
            self._money(
                summary.get(
                    "cash_balance",
                    0.0,
                )
            )
        )

        self.positions_value.setText(
            str(
                summary.get(
                    "position_count",
                    0,
                )
            )
        )

        self.transactions_value.setText(
            str(
                summary.get(
                    "transaction_count",
                    0,
                )
            )
        )

        # --------------------------------------------
        # Benchmark Intelligence Scorecard & Performance
        # --------------------------------------------
        try:
            bm_summary = self.benchmark_service.get_benchmark_summary(summary if portfolio_exists else None)
            self._render_benchmark_summary(bm_summary, summary)
        except Exception:
            self._render_benchmark_summary({
                "portfolio_return_1y": 0.0,
                "benchmark_return_1y": 0.0,
                "alpha_return_1y": 0.0,
                "status": "UNKNOWN",
                "portfolio_symbol_count": 0,
                "benchmark_symbol": "^NSEI",
            }, summary)

        if not portfolio_exists:

            self.empty_frame.show()

            self.holdings_frame.hide()

            self.intelligence_frame.hide()

            if hasattr(self, "allocation_frame"):
                self.allocation_frame.hide()

            self.table.setRowCount(
                0
            )

            self.status_label.setText(
                "No portfolio created yet."
            )

            self.subtitle_label.setText(
                "Persistent Alpha 12 portfolio monitoring"
            )

            return

        self.empty_frame.hide()

        self.holdings_frame.show()

        self.intelligence_frame.show()

        if hasattr(self, "allocation_frame"):
            self.allocation_frame.show()

        self.subtitle_label.setText(
            "Persistent Alpha 12 portfolio monitoring | Active Portfolio: Primary Portfolio"
        )

        self.status_label.setText(
            "Active Portfolio: Primary Portfolio"
        )

        positions = summary.get(
            "positions",
            [],
        )



        if not isinstance(
            positions,
            list,
        ):

            positions = []
            # --------------------------------------------
            # Portfolio Analytics
            # --------------------------------------------

        # --------------------------------------------
        # Portfolio Intelligence (from orchestration)
        # --------------------------------------------

        intelligence = self.portfolio_service.get_portfolio_intelligence()

        # Defaults
        self.portfolio_score_value.setText("-")
        self.portfolio_grade_value.setText("-")
        self.portfolio_health_value.setText("-")

        self.pi_diversification_value.setText("-")
        self.pi_concentration_value.setText("-")
        self.pi_position_sizing_value.setText("-")
        self.pi_weight_balance_value.setText("-")
        self.pi_structure_value.setText("-")

        self.pi_strengths_label.setText("No data available.")
        self.pi_weaknesses_label.setText("No data available.")
        self.pi_warnings_label.setText("No data available.")
        self.pi_summary_label.setText("No data available.")

        if not isinstance(intelligence, dict):
            # Unexpected response
            pass

        status = str(intelligence.get("status", "")).upper()

        if status == "OK":
            portfolio_score = intelligence.get("portfolio_score")

            # Build and render action buckets from recommendations (defensive)
            recommendations = intelligence.get("recommendations")
            _empty_actions = {"status": "OK", "buy": [], "reduce": [], "hold": [], "watch": []}
            try:
                action_service = PortfolioActionService()
                actions = action_service.build_actions(recommendations)
            except Exception:
                actions = _empty_actions

            try:
                self.action_center.load_actions(actions)
                self._select_first_recommendation()
            except Exception:
                # UI must remain resilient; ignore action center failures
                pass

            # Must be a PortfolioIntelligenceScore instance per contract
            from services.portfolio_intelligence_score_service import PortfolioIntelligenceScore

            if isinstance(portfolio_score, PortfolioIntelligenceScore):
                # Overall score
                overall = portfolio_score.overall_score
                self.portfolio_score_value.setText(str(int(round(float(overall)))))

                # Grade
                self.portfolio_grade_value.setText(str(portfolio_score.investment_grade))

                # Health score (component)
                comp = portfolio_score.component_scores
                health_val = comp["health_overall"]
                self.portfolio_health_value.setText(str(int(round(float(health_val)))))

                # Other component scores
                self.pi_diversification_value.setText(str(int(round(float(comp["diversification"])))) )
                self.pi_concentration_value.setText(str(int(round(float(comp["concentration"])))) )
                self.pi_position_sizing_value.setText(str(int(round(float(comp["position_sizing"])))) )
                self.pi_weight_balance_value.setText(str(int(round(float(comp["weight_balance"])))) )
                self.pi_structure_value.setText(str(int(round(float(comp["structure"])))) )

                # Lists
                strengths = portfolio_score.strengths or []
                weaknesses = portfolio_score.weaknesses or []
                warnings = portfolio_score.warnings or []
                portfolio_summary_text = portfolio_score.summary or ""

                if strengths:
                    self.pi_strengths_label.setText("\n".join([f"• {s}" for s in strengths]))
                else:
                    self.pi_strengths_label.setText("No data available.")

                if weaknesses:
                    self.pi_weaknesses_label.setText("\n".join([f"• {w}" for w in weaknesses]))
                else:
                    self.pi_weaknesses_label.setText("No data available.")

                if warnings:
                    self.pi_warnings_label.setText("\n".join([f"• {w}" for w in warnings]))
                else:
                    self.pi_warnings_label.setText("No data available.")

                # Summary: display exactly as returned
                self.pi_summary_label.setText(
                portfolio_summary_text if portfolio_summary_text else "No data available."
                )
            else:
                # portfolio_score missing or wrong type
                self.portfolio_score_value.setText("-")
                self.portfolio_grade_value.setText("-")
                self.portfolio_health_value.setText("-")

        elif status == "NOT_FOUND":
            # No persistent portfolio
            self.portfolio_score_value.setText("-")
            self.portfolio_grade_value.setText("-")
            self.portfolio_health_value.setText("-")
            self.pi_strengths_label.setText("No data available.")
            self.pi_weaknesses_label.setText("No data available.")
            self.pi_warnings_label.setText("No data available.")
            self.pi_summary_label.setText("No data available.")
            self.status_label.setText("No persistent portfolio state found.")

        else:
            # ERROR
            self.portfolio_score_value.setText("-")
            self.portfolio_grade_value.setText("-")
            self.portfolio_health_value.setText("-")
            self.pi_strengths_label.setText("No data available.")
            self.pi_weaknesses_label.setText("No data available.")
            self.pi_warnings_label.setText("No data available.")
            self.pi_summary_label.setText("No data available.")
            err = intelligence.get("error")
            if err:
                self.status_label.setText(f"Portfolio intelligence unavailable: {err}")



        self._populate_table(
            positions
        )

        updated_at = summary.get(
            "updated_at"
        )

        if updated_at:
            formatted_ts = self._format_timestamp(updated_at)
            self.status_label.setText(
                f"Portfolio loaded | Last updated: {formatted_ts}"
            )

        else:

            self.status_label.setText(
                "Portfolio loaded."
            )

    # ======================================================
    # TABLE
    # ======================================================

    def _populate_table(
        self,
        positions,
    ):



        self.table.setRowCount(
            len(
                positions
            )
        )

        for row_index, row in enumerate(
            positions
        ):



            rank = row.get(
                "alpha12_rank",
                row.get(
                    "rank",
                    "",
                ),
            )

            symbol = row.get(
                "symbol",
                "",
            )

            quantity = row.get(
                "quantity",
                0,
            )

            average_cost = row.get(
                "average_cost",
                0.0,
            )

            invested_cost = row.get(
                "invested_cost",
                0.0,
            )

            current_price = row.get(
                "current_price",
                0.0,
            )

            market_value = row.get(
                "market_value",
                row.get(
                    "current_value",
                    0.0,
                ),
            )

            target_weight = row.get(
                "target_weight",
                0.0,
            )

            actual_weight = row.get(
                "actual_weight",
                0.0,
            )

            drift_pct = row.get(
                "drift_pct",
                0.0,
            )

            sector = row.get(
                "sector",
                "",
            )

            category = row.get(
                "category",
                "",
            )

            # Calculate P/L from displayed values
            try:
                pl_value = float(market_value) - float(invested_cost)
            except (TypeError, ValueError):
                pl_value = 0.0

            try:
                inv = float(invested_cost)
                pl_pct = (pl_value / inv) * 100.0 if inv != 0.0 else 0.0
            except (TypeError, ValueError, ZeroDivisionError):
                pl_pct = 0.0

            values = [
                str(
                    rank
                ),
                str(
                    symbol
                ),
                str(
                    quantity
                ),
                self._number(
                    average_cost
                ),
                self._money(
                    invested_cost
                ),
                self._number(
                    current_price
                ),
                self._money(
                    market_value
                ),
                self._money(
                    pl_value
                ),
                self._number(
                    pl_pct
                ),
                self._number(
                    target_weight
                ),
                self._number(
                    actual_weight
                ),
                self._number(
                    drift_pct
                ),
                str(
                    sector
                ),
                str(
                    category
                ),
            ]

            # Color definitions for P/L columns
            _green = QBrush(QColor("#4CAF50"))
            _red = QBrush(QColor("#F44336"))

            for column_index, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    value
                )

                if column_index not in (
                    1,
                    12,
                    13,
                ):

                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

                # Apply green/red coloring to P/L (col 7) and P/L % (col 8)
                if column_index in (7, 8):
                    if pl_value > 0:
                        item.setForeground(_green)
                    elif pl_value < 0:
                        item.setForeground(_red)

                # Apply green/red coloring to Drift % (col 11)
                elif column_index == 11:
                    try:
                        drift_val = float(drift_pct)
                        if drift_val > 0:
                            item.setForeground(_green)
                        elif drift_val < 0:
                            item.setForeground(_red)
                    except (TypeError, ValueError):
                        pass

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )



    # ======================================================
    # ERROR STATE
    # ======================================================

    def _show_error(
        self,
        message,
    ):

        self.empty_frame.show()

        self.holdings_frame.hide()

        self.empty_title.setText(
            "Portfolio Unavailable"
        )

        self.empty_text.setText(
            message
        )

        self.status_label.setText(
            "Portfolio state could not be loaded."
        )

    # ======================================================
    # PORTFOLIO RESET & INVESTMENT ALLOCATION (Sprint 14.1.1)
    # ======================================================

    def _on_reset_portfolio_clicked(self) -> None:
        """Handle double-confirmation Portfolio Reset action (Requirement 3)."""
        from PySide6.QtWidgets import QMessageBox
        from services.portfolio_administration_service import PortfolioAdministrationService

        summary = self.portfolio_service.get_portfolio_summary()
        if not summary.get("portfolio_exists", False):
            QMessageBox.information(
                self,
                "No Portfolio to Reset",
                "There is currently no active portfolio to reset.",
            )
            return

        # Confirmation 1
        reply1 = QMessageBox.warning(
            self,
            "Reset Portfolio?",
            "This will remove the current AlphaForge portfolio and all portfolio-derived analytical state.\n\nDo you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply1 != QMessageBox.Yes:
            return

        # Confirmation 2
        reply2 = QMessageBox.warning(
            self,
            "Confirm Portfolio Reset",
            "I understand that the current portfolio data will be removed and cannot be undone without restoring a backup.\n\nAre you absolutely sure you want to reset?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply2 != QMessageBox.Yes:
            return

        # Execute Reset
        admin_svc = PortfolioAdministrationService()
        res = admin_svc.reset_portfolio_holdings()

        if res.get("status") == "OK":
            QMessageBox.information(
                self,
                "Portfolio Reset Complete",
                "The portfolio has been successfully reset. A backup was saved prior to reset."
            )
            self.load_portfolio()
        else:
            QMessageBox.critical(
                self,
                "Reset Failed",
                f"Failed to reset portfolio: {res.get('error', 'Unknown error')}"
            )

    def _build_investment_allocation_ui(self) -> QFrame:
        """Build the Investment Allocation UI (Requirements 7, 8, 9, 10, 11)."""
        from PySide6.QtWidgets import (
            QLineEdit, QFormLayout, QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem
        )

        frame = QFrame()
        frame.setObjectName("metricCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        title = QLabel("INVESTMENT ALLOCATION (NEW MONEY DEPLOYMENT)")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #173b67;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Propose new-money deployment across current Alpha 12 candidates without selling existing holdings."
        )
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(subtitle)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(20)

        # Box 1: Monthly Investment
        monthly_box = QFrame()
        monthly_box.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; }")
        mb_layout = QVBoxLayout(monthly_box)
        mb_layout.setSpacing(6)

        lbl_mb_title = QLabel("MONTHLY INVESTMENT")
        lbl_mb_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #16a34a;")
        mb_layout.addWidget(lbl_mb_title)

        lbl_mb_desc = QLabel("Enter total monthly contribution (₹):")
        lbl_mb_desc.setStyleSheet("font-size: 12px; color: #475569;")
        mb_layout.addWidget(lbl_mb_desc)

        self.monthly_input = QLineEdit()
        self.monthly_input.setPlaceholderText("e.g. 30000")
        self.monthly_input.setText("30000")
        self.monthly_input.setStyleSheet("QLineEdit { background: white; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; font-size: 13px; font-weight: 600; color: #0f172a; }")
        mb_layout.addWidget(self.monthly_input)

        btn_gen_monthly = QPushButton("Generate Monthly Allocation")
        btn_gen_monthly.setStyleSheet("QPushButton { background-color: #16a34a; color: white; border: none; border-radius: 6px; padding: 8px 14px; font-size: 13px; font-weight: 600; } QPushButton:hover { background-color: #15803d; }")
        btn_gen_monthly.clicked.connect(self._on_generate_monthly_allocation)
        mb_layout.addWidget(btn_gen_monthly)

        ctrl_layout.addWidget(monthly_box)

        # Box 2: Lump-Sum Investment
        lump_box = QFrame()
        lump_box.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; }")
        lb_layout = QVBoxLayout(lump_box)
        lb_layout.setSpacing(6)

        lbl_lb_title = QLabel("LUMP-SUM INVESTMENT")
        lbl_lb_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #2563eb;")
        lb_layout.addWidget(lbl_lb_title)

        lbl_lb_desc = QLabel("Enter lump-sum investment (₹):")
        lbl_lb_desc.setStyleSheet("font-size: 12px; color: #475569;")
        lb_layout.addWidget(lbl_lb_desc)

        self.lump_input = QLineEdit()
        self.lump_input.setPlaceholderText("e.g. 100000")
        self.lump_input.setText("100000")
        self.lump_input.setStyleSheet("QLineEdit { background: white; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; font-size: 13px; font-weight: 600; color: #0f172a; }")
        lb_layout.addWidget(self.lump_input)

        btn_gen_lump = QPushButton("Generate Lump-Sum Allocation")
        btn_gen_lump.setStyleSheet("QPushButton { background-color: #2563eb; color: white; border: none; border-radius: 6px; padding: 8px 14px; font-size: 13px; font-weight: 600; } QPushButton:hover { background-color: #1d4ed8; }")
        btn_gen_lump.clicked.connect(self._on_generate_lump_sum_allocation)
        lb_layout.addWidget(btn_gen_lump)

        ctrl_layout.addWidget(lump_box)
        layout.addLayout(ctrl_layout)

        self.lbl_alloc_summary = QLabel("Enter an investment amount above and click Generate Allocation.")
        self.lbl_alloc_summary.setStyleSheet("font-size: 13px; font-weight: 700; color: #173b67; padding: 4px 0px;")
        layout.addWidget(self.lbl_alloc_summary)

        self.alloc_table = QTableWidget(0, 10)
        self.alloc_table.setHorizontalHeaderLabels([
            "Alpha 12 Rank", "Symbol", "Company Name", "Conviction", "Current Weight", "Target Weight", "Expected Weight", "Suggested Amount (₹)", "Allocation %", "Reason"
        ])
        self.alloc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alloc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.alloc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.alloc_table.setMinimumHeight(220)
        layout.addWidget(self.alloc_table)

        lbl_disclaimer = QLabel("Note: This is an analytical allocation proposal. No transaction is executed automatically.")
        lbl_disclaimer.setStyleSheet("font-size: 11px; color: #64748b; font-style: italic;")
        layout.addWidget(lbl_disclaimer)

        return frame

    def _on_generate_monthly_allocation(self) -> None:
        """Generate Monthly Investment Allocation."""
        from PySide6.QtWidgets import QMessageBox
        from services.investment_allocation_service import InvestmentAllocationService

        txt = self.monthly_input.text().strip()
        try:
            amt = float(txt)
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid numeric monthly investment amount.")
            return

        svc = InvestmentAllocationService()
        res = svc.allocate_monthly_investment(amt)
        if res.total_allocated_amount <= 0:
            QMessageBox.warning(self, "Allocation Error", res.summary_rationale)
            return

        self._render_allocation_results(res)

    def _on_generate_lump_sum_allocation(self) -> None:
        """Generate Lump-Sum Investment Allocation."""
        from PySide6.QtWidgets import QMessageBox
        from services.investment_allocation_service import InvestmentAllocationService

        txt = self.lump_input.text().strip()
        try:
            amt = float(txt)
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid numeric lump-sum investment amount.")
            return

        svc = InvestmentAllocationService()
        res = svc.allocate_lump_sum_investment(amt)
        if res.total_allocated_amount <= 0:
            QMessageBox.warning(self, "Allocation Error", res.summary_rationale)
            return

        self._render_allocation_results(res)

    def _render_allocation_results(self, res) -> None:
        """Render InvestmentAllocationResult items into alloc_table."""
        from PySide6.QtWidgets import QTableWidgetItem

        alloc_type = "Monthly Investment" if res.allocation_type == "MONTHLY" else "Lump-Sum Investment"
        self.lbl_alloc_summary.setText(
            f"USER INPUT: {alloc_type} ₹{res.total_input_amount:,.2f}  |  ALPHAFORGE RECOMMENDATION: Recommended deployment: ₹{res.total_allocated_amount:,.2f}"
        )
        self.lbl_alloc_summary.setStyleSheet("font-size: 13px; font-weight: 700; color: #15803d; padding: 4px 0px;")

        self.alloc_table.setRowCount(0)
        for i, item in enumerate(res.allocations):
            self.alloc_table.insertRow(i)
            self.alloc_table.setItem(i, 0, QTableWidgetItem(f"#{item.alpha12_rank}"))
            self.alloc_table.setItem(i, 1, QTableWidgetItem(item.symbol))
            self.alloc_table.setItem(i, 2, QTableWidgetItem(item.company_name))
            self.alloc_table.setItem(i, 3, QTableWidgetItem(f"{item.conviction:.1f}%"))
            self.alloc_table.setItem(i, 4, QTableWidgetItem(f"{item.current_weight_pct:.1f}%"))
            self.alloc_table.setItem(i, 5, QTableWidgetItem(f"{item.target_weight_pct:.1f}%"))
            self.alloc_table.setItem(i, 6, QTableWidgetItem(f"{item.expected_weight_pct:.1f}%"))
            self.alloc_table.setItem(i, 7, QTableWidgetItem(f"₹{item.suggested_amount:,.2f}"))
            self.alloc_table.setItem(i, 8, QTableWidgetItem(f"{item.suggested_pct:.1f}%"))
            self.alloc_table.setItem(i, 9, QTableWidgetItem(item.reason))

        QMessageBox.warning(
            self,
            "AlphaForge Portfolio",
            message,
        )
