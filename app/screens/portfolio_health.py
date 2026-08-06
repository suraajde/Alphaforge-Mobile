from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QScrollArea,
)

from services.portfolio_health_service import (
    PortfolioHealthResult,
    PortfolioHealthService,
    PortfolioHealthSnapshot,
)


class PortfolioHealth(QWidget):

    def __init__(
        self,
        service: Optional[PortfolioHealthService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.service = service if service is not None else PortfolioHealthService()
        self._build_ui()
        self.refresh_data()

    def refresh_data(self) -> None:
        """Fetch and bind live portfolio health snapshot and evaluation data."""
        if self.service is not None:
            snapshot = None
            if hasattr(self.service, "build_snapshot"):
                try:
                    snapshot = self.service.build_snapshot()
                    self.load_snapshot(snapshot)
                except Exception:
                    pass

            if hasattr(self.service, "evaluate"):
                try:
                    result = self.service.evaluate(snapshot)
                    self.load_result(result)
                except Exception:
                    pass

    def load_snapshot(self, snapshot: Optional[PortfolioHealthSnapshot] = None) -> None:
        """Bind live snapshot metrics to the metric cards."""
        if snapshot is None:
            return

        if "Position Count" in self.cards:
            self.cards["Position Count"].setText(str(snapshot.position_count))

        if "Cash Allocation" in self.cards:
            val = snapshot.cash_allocation_pct
            val_str = f"{val:.1f}%" if (val % 1 != 0) else f"{int(val)}%"
            self.cards["Cash Allocation"].setText(val_str)

        if "Largest Position" in self.cards:
            self.cards["Largest Position"].setText(str(snapshot.largest_position))

    def load_result(self, result: Optional[PortfolioHealthResult] = None) -> None:
        """Bind live PortfolioHealthResult metrics to score, diversification, and concentration cards."""
        if result is None:
            return

        if "Overall Health Score" in self.cards:
            grade_suffix = f" ({result.grade})" if getattr(result, "grade", None) else ""
            self.cards["Overall Health Score"].setText(f"{result.score} / 100{grade_suffix}")

        if "Diversification" in self.cards:
            self.cards["Diversification"].setText(str(result.diversification_rating))

        if "Concentration" in self.cards:
            self.cards["Concentration"].setText(str(result.concentration_rating))

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

            QFrame#metricCard {
                background-color: white;
                border: 1px solid #dce3ed;
                border-radius: 10px;
            }

            QLabel#cardTitle {
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
            }

            QLabel#cardValue {
                font-size: 22px;
                font-weight: 700;
                color: #173b67;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        content_widget = QWidget()
        root_layout = QVBoxLayout(content_widget)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(20)

        # Header Title
        title_box = QVBoxLayout()
        header_title = QLabel("Portfolio Health")
        header_title.setObjectName("pageTitle")

        header_subtitle = QLabel("Overview of key health and risk metrics for your portfolio")
        header_subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(header_title)
        title_box.addWidget(header_subtitle)
        root_layout.addLayout(title_box)

        # Metric Cards Grid Layout
        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)

        cards_spec = [
            ("Overall Health Score", "85 / 100", 0, 0),
            ("Diversification", "GOOD", 0, 1),
            ("Concentration", "MODERATE", 0, 2),
            ("Position Count", "12", 1, 0),
            ("Cash Allocation", "5%", 1, 1),
            ("Largest Position", "KPITTECH", 1, 2),
        ]

        self.cards = {}
        for title, value, row, col in cards_spec:
            card_frame, val_lbl = self._create_metric_card(title, value)
            cards_grid.addWidget(card_frame, row, col)
            self.cards[title] = val_lbl

        root_layout.addLayout(cards_grid)
        root_layout.addStretch()

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

    def _create_metric_card(self, title: str, value: str):
        card = QFrame()
        card.setObjectName("metricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        t_lbl = QLabel(title.upper())
        t_lbl.setObjectName("cardTitle")

        val_lbl = QLabel(value)
        val_lbl.setObjectName("cardValue")

        layout.addWidget(t_lbl)
        layout.addWidget(val_lbl)
        return card, val_lbl
