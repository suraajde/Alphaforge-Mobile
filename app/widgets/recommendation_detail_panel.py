"""Recommendation Detail Panel

Read-only presentation widget showing the details of a single
Recommendation action item.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)


class RecommendationDetailPanel(QWidget):
    """Widget that displays details for a selected recommendation.

    Fields shown (read-only): Title, Priority, Confidence, Score,
    Suggested Action, and Reasons (bullet list).
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _make_row(self, label_text: str) -> QLabel:
        """Helper to create a labeled row. Returns the value QLabel."""
        row = QHBoxLayout()
        label = QLabel(f"{label_text}")
        label.setObjectName("metricTitle")
        value = QLabel("-")
        value.setObjectName("metricValue")
        value.setWordWrap(True)
        row.addWidget(label)
        row.addWidget(value)
        self._main_layout.addLayout(row)
        return value

    def _setup_ui(self) -> None:
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(8)

        header = QLabel("Recommendation Details")
        header.setObjectName("sectionTitle")
        self._main_layout.addWidget(header)

        # Field rows
        self.title_value = self._make_row("Title:")
        self.priority_value = self._make_row("Priority:")
        self.confidence_value = self._make_row("Confidence:")
        self.score_value = self._make_row("Score:")
        self.suggested_action_value = self._make_row("Suggested Action:")

        # Reasons
        reasons_label = QLabel("Reasons")
        reasons_label.setObjectName("metricTitle")
        self._main_layout.addWidget(reasons_label)

        self.reasons_value = QLabel("-")
        self.reasons_value.setWordWrap(True)
        self._main_layout.addWidget(self.reasons_value)

    def clear(self) -> None:
        """Reset all fields to the default placeholder."""
        self.title_value.setText("-")
        self.priority_value.setText("-")
        self.confidence_value.setText("-")
        self.score_value.setText("-")
        self.suggested_action_value.setText("-")
        self.reasons_value.setText("-")

    def load_recommendation(self, recommendation: Dict[str, object] | Any) -> None:
        """Load a recommendation dict or object into the panel.

        The method accepts a dictionary or an object (e.g. Recommendation dataclass)
        containing attributes/keys: title, target, priority, confidence, score,
        suggested_action, reasons. Missing fields are rendered as "-".
        Reasons must be a list of strings and are rendered as bullet points.
        """
        if recommendation is None:
            self.clear()
            return

        if isinstance(recommendation, dict):
            title = recommendation.get("title") or recommendation.get("target") or "-"
            priority = recommendation.get("priority") or "-"
            confidence = recommendation.get("confidence")
            score = recommendation.get("score")
            suggested = recommendation.get("suggested_action") or "-"
            reasons = recommendation.get("reasons")
        elif hasattr(recommendation, "__dict__") or hasattr(recommendation, "title") or hasattr(recommendation, "target"):
            title = getattr(recommendation, "title", None) or getattr(recommendation, "target", None) or "-"
            priority = getattr(recommendation, "priority", None) or "-"
            confidence = getattr(recommendation, "confidence", None)
            score = getattr(recommendation, "score", None)
            suggested = getattr(recommendation, "suggested_action", None) or "-"
            reasons = getattr(recommendation, "reasons", None)
        else:
            self.clear()
            return

        self.title_value.setText(str(title))
        self.priority_value.setText(str(priority))
        self.confidence_value.setText(str(confidence) if confidence is not None else "-")
        self.score_value.setText(str(score) if score is not None else "-")
        self.suggested_action_value.setText(str(suggested))

        if isinstance(reasons, list) and reasons:
            bullets = "\n".join([f"• {str(r)}" for r in reasons])
            self.reasons_value.setText(bullets)
        else:
            self.reasons_value.setText("-")
