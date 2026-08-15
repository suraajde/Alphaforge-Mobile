from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QMainWindow,
    QStackedWidget,
    QWidget,
)


from app.screens.sidebar import Sidebar


class ErrorFallbackWidget(QWidget):
    """Fallback UI container shown when a screen fails to initialize, preventing blank screens."""

    def __init__(self, screen_name: str, error_message: str, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #1f2937;
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 24px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        icon_lbl = QLabel("⚠️")
        icon_lbl.setStyleSheet("font-size: 48px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel(f"Unable to Load {screen_name}")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #f87171;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg_lbl = QLabel(
            f"An unexpected error occurred while initializing this screen:\n\n{error_message}\n\n"
            "Please check system logs or run Production Radar to refresh application state."
        )
        msg_lbl.setStyleSheet("font-size: 14px; color: #d1d5db;")
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(icon_lbl)
        card_layout.addWidget(title_lbl)
        card_layout.addWidget(msg_lbl)

        layout.addWidget(card)


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
            try:
                from app.screens.dashboard import Dashboard
                self._dashboard = Dashboard()
                self.pages.addWidget(self._dashboard)
            except Exception as exc:
                fallback = ErrorFallbackWidget("Dashboard", str(exc))
                self.pages.addWidget(fallback)
                return fallback
        return self._dashboard

    @property
    def stock_explorer(self):
        if self._stock_explorer is None:
            try:
                from app.screens.stock_explorer import StockExplorer
                self._stock_explorer = StockExplorer()
                self.pages.addWidget(self._stock_explorer)
            except Exception as exc:
                fallback = ErrorFallbackWidget("Stock Explorer", str(exc))
                self.pages.addWidget(fallback)
                return fallback
        return self._stock_explorer

    @property
    def research_radar(self):
        if self._research_radar is None:
            try:
                from app.screens.research_radar import ResearchRadar
                self._research_radar = ResearchRadar()
                self.pages.addWidget(self._research_radar)
            except Exception as exc:
                fallback = ErrorFallbackWidget("Research Radar", str(exc))
                self.pages.addWidget(fallback)
                return fallback
        return self._research_radar

    @property
    def portfolio(self):
        if self._portfolio is None:
            try:
                from app.screens.portfolio import Portfolio
                self._portfolio = Portfolio(
                    alpha12_provider=self._current_alpha12
                )
                self.pages.addWidget(self._portfolio)
            except Exception as exc:
                fallback = ErrorFallbackWidget("Portfolio", str(exc))
                self.pages.addWidget(fallback)
                return fallback
        return self._portfolio

    @property
    def portfolio_health(self):
        if self._portfolio_health is None:
            try:
                from app.screens.portfolio_health import PortfolioHealth
                self._portfolio_health = PortfolioHealth(
                    alpha12_provider=self._current_alpha12
                )
                self.pages.addWidget(self._portfolio_health)
            except Exception as exc:
                fallback = ErrorFallbackWidget("Portfolio Health", str(exc))
                self.pages.addWidget(fallback)
                return fallback
        return self._portfolio_health

    @property
    def action_center(self):
        if self._action_center is None:
            try:
                from app.screens.portfolio_action_center import PortfolioActionCenter
                self._action_center = PortfolioActionCenter(
                    alpha12_provider=self._current_alpha12
                )
                self.pages.addWidget(self._action_center)
            except Exception as exc:
                fallback = ErrorFallbackWidget("Portfolio Action Center", str(exc))
                self.pages.addWidget(fallback)
                return fallback
        return self._action_center

    @property
    def watchtower(self):
        if self._watchtower is None:
            try:
                from app.screens.watchtower import Watchtower
                from services.alpha12_mapping_service import Alpha12MappingService
                from services.alpha12_stability_service import Alpha12StabilityService
                m_svc = Alpha12MappingService(alpha12_provider=self._current_alpha12)
                s_svc = Alpha12StabilityService(alpha12_mapping_service=m_svc)
                self._watchtower = Watchtower(stability_service=s_svc)
                self.pages.addWidget(self._watchtower)
            except Exception as exc:
                fallback = ErrorFallbackWidget("Watchtower", str(exc))
                self.pages.addWidget(fallback)
                return fallback
        return self._watchtower

    @property
    def settings(self):
        if self._settings is None:
            try:
                from app.screens.settings import Settings
                self._settings = Settings()
                self.pages.addWidget(self._settings)
            except Exception as exc:
                fallback = ErrorFallbackWidget("Settings", str(exc))
                self.pages.addWidget(fallback)
                return fallback
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
            try:
                screen = getter()
                if screen is not None:
                    self.pages.setCurrentWidget(screen)
            except Exception as exc:
                fallback = ErrorFallbackWidget(target.replace("_", " ").title(), str(exc))
                self.pages.addWidget(fallback)
                self.pages.setCurrentWidget(fallback)


    def _current_alpha12(self):
        radar = self.research_radar
        result = getattr(
            radar,
            "last_result",
            None,
        )

        if not isinstance(result, dict) or not result.get("alpha12"):
            from services.production_radar_pipeline import load_production_radar_snapshot
            snapshot = load_production_radar_snapshot()
            if isinstance(snapshot, dict) and snapshot.get("alpha12"):
                if hasattr(radar, "restore_persisted_snapshot"):
                    radar.restore_persisted_snapshot()
                result = snapshot

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
