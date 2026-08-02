from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class Settings(QWidget):
    """Settings screen foundation for Portfolio Administration and application configuration."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e3a8a;")

        subtitle = QLabel("Portfolio Administration and application configuration")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
