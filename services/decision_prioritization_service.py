"""Decision Prioritization Service Framework (Sprint 16.0.2)

Establishes the foundational framework for prioritizing classified portfolio decisions.
This service is PRIORITIZATION ONLY.
It does NOT implement investment recommendations, buy/sell/hold decisions, rebalancing,
AI reasoning, portfolio optimization, decision scoring, trade execution, or broker integration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class DecisionPriority:
    """Dataclass representing a prioritized decision record."""
    decision_id: str
    category: str
    priority: str
    description: str


@dataclass
class DecisionPrioritizationResult:
    """Container holding prioritization metrics and prioritized items."""
    total_prioritized: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    priorities: list[DecisionPriority] = field(default_factory=list)


class DecisionPrioritizationService:
    """Service layer for Decision Prioritization foundation safely."""

    def __init__(
        self,
        decision_classification_service: Optional[Any] = None,
        decision_engine_service: Optional[Any] = None,
    ) -> None:
        self.decision_classification_service = decision_classification_service
        self.decision_engine_service = decision_engine_service

    def build_summary(
        self,
        priorities: Optional[list[DecisionPriority]] = None,
    ) -> DecisionPrioritizationResult:
        """Builds and returns a DecisionPrioritizationResult safely."""
        try:
            items = priorities or []
            total = len(items)
            critical = sum(1 for p in items if getattr(p, "priority", "") == "CRITICAL")
            high = sum(1 for p in items if getattr(p, "priority", "") == "HIGH")
            medium = sum(1 for p in items if getattr(p, "priority", "") == "MEDIUM")
            low = sum(1 for p in items if getattr(p, "priority", "") == "LOW")
            info = sum(1 for p in items if getattr(p, "priority", "") == "INFO")
            return DecisionPrioritizationResult(
                total_prioritized=total,
                critical_count=critical,
                high_count=high,
                medium_count=medium,
                low_count=low,
                info_count=info,
                priorities=items,
            )
        except Exception:
            return DecisionPrioritizationResult(
                total_prioritized=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                info_count=0,
                priorities=[],
            )

    def get_priorities(self) -> list[DecisionPriority]:
        """Returns the list of decision priorities (empty for foundation sprint) safely."""
        try:
            return []
        except Exception:
            return []

    def prioritize(
        self,
        classifications: Optional[list[Any]] = None,
    ) -> DecisionPrioritizationResult:
        """Prioritizes classification records safely.

        Deterministic priority mapping (only when classification_status == "CLASSIFIED"):
            HEALTH -> HIGH
            MONITORING -> MEDIUM
            ALERT -> HIGH
            PORTFOLIO -> MEDIUM
            GENERAL -> INFO
            UNCLASSIFIED -> LOW

        If classification_status == "UNCLASSIFIED", assign priority = "LOW".
        """
        fallback_result = DecisionPrioritizationResult(
            total_prioritized=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            info_count=0,
            priorities=[],
        )
        try:
            items_to_process = classifications
            if items_to_process is None:
                if (
                    self.decision_classification_service is not None
                    and hasattr(self.decision_classification_service, "get_classifications")
                ):
                    items_to_process = self.decision_classification_service.get_classifications()
                else:
                    items_to_process = []

            if not isinstance(items_to_process, list):
                items_to_process = []

            priority_map = {
                "HEALTH": "HIGH",
                "MONITORING": "MEDIUM",
                "ALERT": "HIGH",
                "PORTFOLIO": "MEDIUM",
                "GENERAL": "INFO",
                "UNCLASSIFIED": "LOW",
            }

            priorities = []
            for item in items_to_process:
                if item is None:
                    continue

                d_id = getattr(item, "decision_id", None)
                cat = getattr(item, "category", None)
                desc = getattr(item, "description", None)
                status = getattr(item, "classification_status", None)

                d_id_str = str(d_id) if d_id is not None else ""
                cat_str = str(cat) if cat is not None else ""
                desc_str = str(desc) if desc is not None else ""
                status_str = str(status) if status is not None else ""

                if status_str == "CLASSIFIED":
                    prio = priority_map.get(cat_str, "INFO")
                else:
                    prio = "LOW"

                priorities.append(
                    DecisionPriority(
                        decision_id=d_id_str,
                        category=cat_str,
                        priority=prio,
                        description=desc_str,
                    )
                )

            return self.build_summary(priorities)
        except Exception:
            return fallback_result
