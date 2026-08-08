from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.screens.sidebar import Sidebar


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

        self._dashboard = None
        self._stock_explorer = None
        self._research_radar = None
        self._portfolio = None
        self._portfolio_health = None
        self._action_center = None
        self._watchtower = None
        self._settings = None

        # Build initial screen (Dashboard)
        self.navigate_to("dashboard")

        # ---------------- Layout ----------------

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages)

        # ---------------- Navigation ----------------

        self.sidebar.dashboard_btn.clicked.connect(
            lambda: self.navigate_to("dashboard")
        )

        self.sidebar.stock_btn.clicked.connect(
            lambda: self.navigate_to("stock_explorer")
        )

        self.sidebar.research_btn.clicked.connect(
            lambda: self.navigate_to("research_radar")
        )

        self.sidebar.portfolio_btn.clicked.connect(
            lambda: self.navigate_to("portfolio")
        )

        self.sidebar.health_btn.clicked.connect(
            lambda: self.navigate_to("portfolio_health")
        )

        self.sidebar.action_center_btn.clicked.connect(
            lambda: self.navigate_to("action_center")
        )

        self.sidebar.watchtower_btn.clicked.connect(
            lambda: self.navigate_to("watchtower")
        )

        self.sidebar.settings_btn.clicked.connect(
            lambda: self.navigate_to("settings")
        )

    @property
    def dashboard(self):
        if self._dashboard is None:
            from app.screens.dashboard import Dashboard
            self._dashboard = Dashboard()
            self.pages.addWidget(self._dashboard)
        return self._dashboard

    @property
    def stock_explorer(self):
        if self._stock_explorer is None:
            from app.screens.stock_explorer import StockExplorer
            self._stock_explorer = StockExplorer()
            self.pages.addWidget(self._stock_explorer)
        return self._stock_explorer

    @property
    def research_radar(self):
        if self._research_radar is None:
            from app.screens.research_radar import ResearchRadar
            self._research_radar = ResearchRadar()
            self.pages.addWidget(self._research_radar)
        return self._research_radar

    @property
    def portfolio(self):
        if self._portfolio is None:
            from app.screens.portfolio import Portfolio
            self._portfolio = Portfolio(
                alpha12_provider=self._current_alpha12
            )
            self.pages.addWidget(self._portfolio)
        return self._portfolio

    @property
    def portfolio_health(self):
        if self._portfolio_health is None:
            from app.screens.portfolio_health import PortfolioHealth
            self._portfolio_health = PortfolioHealth()
            self.pages.addWidget(self._portfolio_health)
        return self._portfolio_health

    @property
    def action_center(self):
        if self._action_center is None:
            from app.screens.portfolio_action_center import PortfolioActionCenter
            self._action_center = PortfolioActionCenter()
            self.pages.addWidget(self._action_center)
        return self._action_center

    @property
    def watchtower(self):
        if self._watchtower is None:
            from app.screens.watchtower import Watchtower
            self._watchtower = Watchtower()
            self.pages.addWidget(self._watchtower)
        return self._watchtower

    @property
    def settings(self):
        if self._settings is None:
            from app.screens.settings import Settings
            self._settings = Settings()
            self.pages.addWidget(self._settings)
        return self._settings

    def navigate_to(self, target: str) -> None:
        screen_map = {
            "dashboard": lambda: self.dashboard,
            "stock_explorer": lambda: self.stock_explorer,
            "research_radar": lambda: self.research_radar,
            "portfolio": lambda: self.portfolio,
            "portfolio_health": lambda: self.portfolio_health,
            "action_center": lambda: self.action_center,
            "watchtower": lambda: self.watchtower,
            "settings": lambda: self.settings,
        }
        getter = screen_map.get(target)
        if getter is not None:
            screen = getter()
            self.pages.setCurrentWidget(screen)

    def _current_alpha12(self):
        radar = self.research_radar
        result = getattr(
            radar,
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
