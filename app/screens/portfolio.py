from PySide6.QtCore import Qt
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
)

from services.portfolio_application_service import (
    create_portfolio_application_service,
)

from services.stock_service import (
    get_stock_data,
)



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

        self._build_ui()

        self.initial_investment_btn = QPushButton(
            "Create Investment Plan"
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

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            24,
            20,
            24,
            20,
        )

        root.setSpacing(
            16
        )

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

        header.addWidget(
            self.refresh_button
        )

        root.addLayout(
            header
        )

        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        self.status_label = QLabel(
            ""
        )

        self.status_label.setObjectName(
            "pageSubtitle"
        )

        root.addWidget(
            self.status_label
        )

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
            "SNAPSHOTS"
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
            "No Active Portfolio"
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

        self.table.setColumnCount(
            12
        )

        self.table.setHorizontalHeaderLabels([
            "Rank",
            "Symbol",
            "Qty",
            "Avg Cost",
            "Actual Purchase Value",
            "Price",
            "Market Value",
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
            "Loading portfolio state..."
        )

        try:

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

        self.snapshots_value.setText(
            str(
                summary.get(
                    "snapshot_count",
                    0,
                )
            )
        )

        if not portfolio_exists:

            self.empty_frame.show()

            self.holdings_frame.hide()

            self.table.setRowCount(
                0
            )

            self.status_label.setText(
                "No persistent portfolio state found."
            )

            return

        self.empty_frame.hide()

        self.holdings_frame.show()

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
            self._populate_table(positions)
            return

        status = str(intelligence.get("status", "")).upper()

        if status == "OK":
            portfolio_score = intelligence.get("portfolio_score")

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

            self.status_label.setText(
                f"Portfolio loaded | Last updated: {updated_at}"
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

            for column_index, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    value
                )

                if column_index not in (
                    1,
                    10,
                    11,
                ):

                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

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

        QMessageBox.warning(
            self,
            "AlphaForge Portfolio",
            message,
        )
