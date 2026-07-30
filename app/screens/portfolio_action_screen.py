"""Portfolio Action Screen

A simple smoke-test screen that hosts PortfolioActionCenter and loads
sample action data for manual QA.
"""
from __future__ import annotations

from typing import Dict

from PySide6.QtWidgets import QWidget, QVBoxLayout

from app.widgets.portfolio_action_center import PortfolioActionCenter


class PortfolioActionScreen(QWidget):
    """Screen wrapper to display the PortfolioActionCenter with sample data."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        self.action_center = PortfolioActionCenter(self)
        root.addWidget(self.action_center)

        sample: Dict[str, list] = {
            "status": "OK",
            "buy": [
                {
                    "target": "LUPIN",
                    "title": "Increase exposure",
                    "priority": "HIGH",
                    "confidence": 92,
                    "score": 95,
                    "reasons": [],
                }
            ],
            "reduce": [
                {
                    "target": "ABC",
                    "title": "Reduce position",
                    "priority": "MEDIUM",
                    "confidence": 80,
                    "score": 70,
                    "reasons": [],
                }
            ],
            "hold": [
                {
                    "target": "XYZ",
                    "title": "Maintain position",
                    "priority": "LOW",
                    "confidence": 75,
                    "score": 65,
                    "reasons": [],
                }
            ],
            "watch": [
                {
                    "target": "CDSL",
                    "title": "Monitor opportunity",
                    "priority": "LOW",
                    "confidence": 60,
                    "score": 55,
                    "reasons": [],
                }
            ],
        }

        self.action_center.load_actions(sample)
