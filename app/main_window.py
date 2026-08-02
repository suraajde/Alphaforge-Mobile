from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
)

from app.screens.sidebar import Sidebar
from app.screens.dashboard import Dashboard
from app.screens.stock_explorer import StockExplorer
from app.screens.research_radar import ResearchRadar
from app.screens.portfolio import Portfolio
from app.screens.portfolio_action_center import PortfolioActionCenter
from app.screens.settings import Settings


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AlphaForge")
        self.resize(1600, 900)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # ---------------- Sidebar ----------------

        self.sidebar = Sidebar()

        # ---------------- Pages ----------------

        self.pages = QStackedWidget()

        self.dashboard = Dashboard()
        self.stock_explorer = StockExplorer()
        self.research_radar = ResearchRadar()
        self.portfolio = Portfolio(
            alpha12_provider=
                self._current_alpha12
        )
        self.action_center = PortfolioActionCenter()
        self.settings = Settings()

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.stock_explorer)
        self.pages.addWidget(self.research_radar)
        self.pages.addWidget(self.portfolio)
        self.pages.addWidget(self.action_center)
        self.pages.addWidget(self.settings)

        # ---------------- Layout ----------------

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages)

        # ---------------- Navigation ----------------

        self.sidebar.dashboard_btn.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.dashboard)
        )

        self.sidebar.stock_btn.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.stock_explorer)
        )

        self.sidebar.research_btn.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.research_radar)
        )

        self.sidebar.portfolio_btn.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.portfolio)
        )

        self.sidebar.action_center_btn.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.action_center)
        )

        self.sidebar.settings_btn.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.settings)
        )

    def _current_alpha12(
        self,
    ):

        result = getattr(
            self.research_radar,
            "last_result",
            None,
        )

        if not isinstance(
            result,
            dict,
        ):

            return []

        alpha12 = result.get(
            "alpha12",
            [],
        )

        if not isinstance(
            alpha12,
            list,
        ):

            return []

        return alpha12
