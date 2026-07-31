"""Portfolio Action Center widget

Presentation-only widget that displays action buckets produced by
PortfolioActionService. No business logic or calculations are performed here.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
)


class PortfolioActionCenter(QWidget):
    """A reusable UI widget that shows actionable recommendations in buckets.

    Expected input for load_actions is a dict with keys: status, buy, reduce,
    hold, watch. Each bucket is a list of dicts (action items).
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create layout and widgets."""
        root = QVBoxLayout(self)
        header = QLabel("Portfolio Action Center")
        header.setObjectName("portfolioActionHeader")
        root.addWidget(header)

        # BUY
        buy_box = QGroupBox("BUY")
        buy_layout = QVBoxLayout(buy_box)
        self.buy_list = QListWidget()
        self.buy_list.setMaximumHeight(80)
        self.buy_list.setMinimumHeight(60)
        self.buy_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        buy_layout.addWidget(self.buy_list)
        root.addWidget(buy_box)

        # REDUCE
        reduce_box = QGroupBox("REDUCE")
        reduce_layout = QVBoxLayout(reduce_box)
        self.reduce_list = QListWidget()
        self.reduce_list.setMaximumHeight(80)
        self.reduce_list.setMinimumHeight(60)
        self.reduce_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        reduce_layout.addWidget(self.reduce_list)
        root.addWidget(reduce_box)

        # HOLD
        hold_box = QGroupBox("HOLD")
        hold_layout = QVBoxLayout(hold_box)
        self.hold_list = QListWidget()
        self.hold_list.setMaximumHeight(80)
        self.hold_list.setMinimumHeight(60)
        self.hold_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        hold_layout.addWidget(self.hold_list)
        root.addWidget(hold_box)

        # WATCH
        watch_box = QGroupBox("WATCH")
        watch_layout = QVBoxLayout(watch_box)
        self.watch_list = QListWidget()
        self.watch_list.setMaximumHeight(80)
        self.watch_list.setMinimumHeight(60)
        self.watch_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        watch_layout.addWidget(self.watch_list)
        root.addWidget(watch_box)

        self.clear()

    def clear(self) -> None:
        """Clear all list widgets."""
        self.buy_list.clear()
        self.reduce_list.clear()
        self.hold_list.clear()
        self.watch_list.clear()

    def load_actions(self, actions: Dict[str, Any]) -> None:
        """Load prepared actions into the widget.

        The method is defensive about missing keys and expected types.
        """
        self.clear()

        if not isinstance(actions, dict) or str(actions.get("status", "")).upper() != "OK":
            # Nothing to show if contract is not honored
            for lw in (self.buy_list, self.reduce_list, self.hold_list, self.watch_list):
                self._populate_bucket(lw, [])
            return

        self._populate_bucket(self.buy_list, self._safe_get_list(actions, "buy"))
        self._populate_bucket(self.reduce_list, self._safe_get_list(actions, "reduce"))
        self._populate_bucket(self.hold_list, self._safe_get_list(actions, "hold"))
        self._populate_bucket(self.watch_list, self._safe_get_list(actions, "watch"))

    def _safe_get_list(self, actions: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
        """Return a list for key or an empty list if missing/invalid."""
        val = actions.get(key, [])
        return val if isinstance(val, list) else []

    def _populate_bucket(self, list_widget: QListWidget, items: List[Dict[str, Any]]) -> None:
        """Populate a single QListWidget from items.

        Each row is formatted as: "[PRIORITY] TARGET | Score: 95 | Confidence: 92".
        If items is empty, show a placeholder.
        """
        list_widget.clear()

        if not items:
            list_widget.addItem(QListWidgetItem("Nothing to display"))
            return

        for it in items:
            if not isinstance(it, dict):
                # Skip malformed entries
                continue

            priority = str(it.get("priority", "")).upper()
            target = str(it.get("target", ""))
            score = str(it.get("score", ""))
            confidence = str(it.get("confidence", ""))

            text = f"[{priority}] {target} | Score: {score} | Confidence: {confidence}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, it)
            list_widget.addItem(item)
