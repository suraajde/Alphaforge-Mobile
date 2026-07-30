"""Manual UI test runner for PortfolioActionScreen.

Run this script locally to visually inspect the widget. Not a unit test.
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from app.screens.portfolio_action_screen import PortfolioActionScreen


def main() -> None:
    app = QApplication(sys.argv)
    screen = PortfolioActionScreen()
    screen.resize(1200, 800)
    screen.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
