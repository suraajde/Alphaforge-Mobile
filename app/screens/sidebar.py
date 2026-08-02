from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
)


class Sidebar(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedWidth(200)

        layout = QVBoxLayout(self)

        self.dashboard_btn = QPushButton("🏠 Dashboard")
        self.stock_btn = QPushButton("🔍 Stock Explorer")
        self.research_btn = QPushButton("🎯 Research Radar")
        self.portfolio_btn = QPushButton("💼 Portfolio")
        self.action_center_btn = QPushButton("⚡ Portfolio Action Center")
        self.watchtower_btn = QPushButton("👁 Watchtower")
        self.settings_btn = QPushButton("⚙ Settings")

        buttons = [
            self.dashboard_btn,
            self.stock_btn,
            self.research_btn,
            self.portfolio_btn,
            self.action_center_btn,
            self.watchtower_btn,
            self.settings_btn,
        ]

        for button in buttons:

            button.setMinimumHeight(55)

            button.setStyleSheet("""
                QPushButton{
                    text-align:left;
                    padding-left:15px;
                    font-size:16px;
                    background:#2b2b2b;
                    color:white;
                    border:none;
                }

                QPushButton:hover{
                    background:#3d3d3d;
                }
            """)

            layout.addWidget(button)

        layout.addStretch()