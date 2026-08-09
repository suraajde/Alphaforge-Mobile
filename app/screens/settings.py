"""Settings Screen Foundation for AlphaForge (Sprint 14.0.0).

Provides application administration, governance policy parameters, data directory status, and system configuration.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


from config.path_config import get_base_data_dir, get_data_path, get_resource_path
from core.version import APP_VERSION


class Settings(QWidget):
    """Portfolio Administration and application configuration settings screen."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        root_layout = QVBoxLayout(content_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(16)

        # Header Title
        header_card = QFrame()
        header_card.setObjectName("metricCard")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(16, 14, 16, 14)

        title_lbl = QLabel("SETTINGS & PORTFOLIO ADMINISTRATION")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e3a8a;")

        subtitle_lbl = QLabel(
            "System configuration, governance policy parameters, and storage directory status."
        )
        subtitle_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

        header_layout.addWidget(title_lbl)
        header_layout.addWidget(subtitle_lbl)
        root_layout.addWidget(header_card)

        # Section 1: System & Developer Info
        sys_card = QFrame()
        sys_card.setObjectName("metricCard")
        sys_layout = QVBoxLayout(sys_card)
        sys_layout.setContentsMargins(16, 14, 16, 14)
        sys_layout.setSpacing(8)

        lbl_sys_title = QLabel("APPLICATION & DEVELOPER INFORMATION")
        lbl_sys_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")

        sys_info = (
            "• Application Name: AlphaForge — AI Portfolio Construction Engine\n"
            f"• Release Version: v{APP_VERSION} (Stable Release)\n"
            "• Release Status: Version 1.0.0 Stable Release (Chapter 20 Completed)\n"
            "• Developed By: Suraj Dev\n"
            "• Contact Email: suraajde@gmail.com\n"
            '• LinkedIn: <a href="https://www.linkedin.com/in/suraaj-de-81336932/">suraaj-de-81336932</a>\n'
            '• GitHub: <a href="https://github.com/suraajde">github.com/suraajde</a>'
        )
        lbl_sys_body = QLabel(sys_info)
        lbl_sys_body.setStyleSheet("font-size: 13px; color: #334155; line-height: 1.5;")
        lbl_sys_body.setOpenExternalLinks(True)

        sys_layout.addWidget(lbl_sys_title)
        sys_layout.addWidget(lbl_sys_body)
        root_layout.addWidget(sys_card)

        # Section 2: License & Investment Disclaimer
        lic_card = QFrame()
        lic_card.setObjectName("metricCard")
        lic_card.setStyleSheet("QFrame#metricCard { background-color: #f8fafc; border: 1px solid #cbd5e1; }")
        lic_layout = QVBoxLayout(lic_card)
        lic_layout.setContentsMargins(16, 14, 16, 14)
        lic_layout.setSpacing(8)

        lbl_lic_title = QLabel("PERSONAL USE LICENSE & INVESTMENT DISCLAIMER")
        lbl_lic_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a;")

        lic_info = (
            "<b>Personal Use License:</b><br>"
            "AlphaForge is provided under a personal use software license for individual analytical and research purposes. "
            "It requires no activation keys, paid subscriptions, or online license server validation.<br><br>"
            "<b>Educational Investment Disclaimer:</b><br>"
            "AlphaForge is analytical and educational software. Its outputs are provided for informational and research purposes only "
            "and do not constitute personalized investment, financial, legal, tax, or securities advice. "
            "Users are solely responsible for their own investment decisions and should conduct their own research and, where appropriate, "
            "consult a qualified financial professional before investing."
        )
        lbl_lic_body = QLabel(lic_info)
        lbl_lic_body.setWordWrap(True)
        lbl_lic_body.setStyleSheet("font-size: 12px; color: #334155; line-height: 1.5;")

        lic_layout.addWidget(lbl_lic_title)
        lic_layout.addWidget(lbl_lic_body)
        root_layout.addWidget(lic_card)

        # Section 3: Alpha 12 Governance Parameters
        gov_card = QFrame()
        gov_card.setObjectName("metricCard")
        gov_layout = QVBoxLayout(gov_card)
        gov_layout.setContentsMargins(16, 14, 16, 14)
        gov_layout.setSpacing(8)

        lbl_gov_title = QLabel("ALPHA 12 GOVERNANCE PARAMETERS (READ-ONLY)")
        lbl_gov_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")

        gov_info = (
            "• Minimum Challenger Score Advantage: +10.0 points\n"
            "• Conviction Buffer: +5.0 points\n"
            "• Maximum Replacements per Governance Cycle: 3 candidates\n"
            "• Projected Turnover Threshold: 20.0%\n"
            "• Replacement Cooling Period: 30 days\n"
            "• Incumbent Protection Policy: Strong incumbents are protected against rank-only turnover."
        )
        lbl_gov_body = QLabel(gov_info)
        lbl_gov_body.setStyleSheet("font-size: 13px; color: #334155; line-height: 1.5;")

        gov_layout.addWidget(lbl_gov_title)
        gov_layout.addWidget(lbl_gov_body)
        root_layout.addWidget(gov_card)

        # Section 4: Data & Persistence Status
        data_card = QFrame()
        data_card.setObjectName("metricCard")
        data_layout = QVBoxLayout(data_card)
        data_layout.setContentsMargins(16, 14, 16, 14)
        data_layout.setSpacing(8)

        lbl_data_title = QLabel("DATA PERSISTENCE & STORAGE DIRECTORIES")
        lbl_data_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")

        resource_dir = get_resource_path("data/universe")
        base_dir = get_base_data_dir()
        data_info = (
            f"• Bundled Application Resources: {resource_dir}\n"
            f"• User Writable Data Directory: {base_dir}\n"
            f"• Portfolio Intelligence Storage: {get_data_path('intelligence/portfolio_intelligence_history.json')}\n"
            f"• Alpha 12 Stability Storage: {get_data_path('rebalancing/alpha12_stability_history.json')}\n"
            "• Persistence Architecture: Centralized PyInstaller-Safe Resource & Writable Path Resolution"
        )
        lbl_data_body = QLabel(data_info)
        lbl_data_body.setStyleSheet("font-size: 13px; color: #334155; line-height: 1.5;")

        data_layout.addWidget(lbl_data_title)
        data_layout.addWidget(lbl_data_body)
        root_layout.addWidget(data_card)

        # Section 5: Operational Safety Notice
        safety_card = QFrame()
        safety_card.setObjectName("metricCard")
        safety_layout = QVBoxLayout(safety_card)
        safety_layout.setContentsMargins(16, 14, 16, 14)

        lbl_safety_title = QLabel("OPERATIONAL BOUNDARIES")
        lbl_safety_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")

        safety_body = (
            "AlphaForge operates strictly under human-review analytics guidelines. "
            "Broker API credentials, automated order routing, trade execution controls, "
            "and unreviewed portfolio mutations are excluded by architecture."
        )
        lbl_safety_text = QLabel(safety_body)
        lbl_safety_text.setStyleSheet("font-size: 12px; color: #475569; font-style: italic;")

        safety_layout.addWidget(lbl_safety_title)
        safety_layout.addWidget(lbl_safety_text)
        root_layout.addWidget(safety_card)

        root_layout.addStretch()
        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)
