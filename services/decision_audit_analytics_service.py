"""Decision Audit Analytics Service (Sprint 16.0.5)

Provides analytics and summary aggregations derived exclusively from the
existing Decision Audit Trail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class DecisionAuditAnalyticsSummary:
    """Summary metrics computed from decision audit entries."""

    total_entries: int
    unique_decisions: int
    classified_entries: int
    unclassified_entries: int
    high_priority_entries: int
    medium_priority_entries: int
    low_priority_entries: int
    info_priority_entries: int
    critical_priority_entries: int


@dataclass
class DecisionAuditAnalytics:
    """Complete analytics result containing summary metrics and distribution dictionaries."""

    summary: DecisionAuditAnalyticsSummary
    category_counts: dict[str, int]
    priority_counts: dict[str, int]
    classification_counts: dict[str, int]
    source_counts: dict[str, int]


def _empty_summary() -> DecisionAuditAnalyticsSummary:
    """Return a safe empty analytics summary."""
    return DecisionAuditAnalyticsSummary(
        total_entries=0,
        unique_decisions=0,
        classified_entries=0,
        unclassified_entries=0,
        high_priority_entries=0,
        medium_priority_entries=0,
        low_priority_entries=0,
        info_priority_entries=0,
        critical_priority_entries=0,
    )


def _empty_analytics() -> DecisionAuditAnalytics:
    """Return a safe empty analytics object."""
    return DecisionAuditAnalytics(
        summary=_empty_summary(),
        category_counts={},
        priority_counts={},
        classification_counts={},
        source_counts={},
    )


def _is_valid_entry(entry: Any) -> bool:
    """Safely check if an object is a valid entry record."""
    if entry is None:
        return False
    if isinstance(entry, (str, int, float, bool, list, tuple, set)):
        return False
    return True


class DecisionAuditAnalyticsService:
    """Service for computing analytics and distributions from audit trail entries.

    Operates purely as an analytical engine on existing audit data.
    Never modifies persisted audit entries, decision rules, or classification states.
    """

    # Deterministic priority ordering required by specification
    PRIORITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    # Deterministic classification ordering required by specification
    CLASSIFICATION_ORDER = ["CLASSIFIED", "UNCLASSIFIED"]

    def __init__(self, audit_service: Optional[Any] = None) -> None:
        """Initialize DecisionAuditAnalyticsService with an optional audit service dependency."""
        self._audit_service = audit_service

    def _get_audit_service(self) -> Optional[Any]:
        """Safely retrieve or instantiate the DecisionAuditService."""
        if self._audit_service is not None:
            return self._audit_service
        try:
            from services.decision_audit_service import DecisionAuditService

            return DecisionAuditService()
        except Exception:
            return None

    def build_summary(
        self, entries: Optional[list] = None
    ) -> DecisionAuditAnalyticsSummary:
        """Build summary metrics from a list of decision audit entries."""
        try:
            if not entries or not isinstance(entries, list):
                return _empty_summary()

            total_entries = 0
            unique_decision_ids: set[str] = set()
            classified_count = 0
            unclassified_count = 0
            critical_count = 0
            high_count = 0
            medium_count = 0
            low_count = 0
            info_count = 0

            for entry in entries:
                if not _is_valid_entry(entry):
                    continue

                total_entries += 1

                # Unique decision ID tracking
                d_id = str(getattr(entry, "decision_id", ""))
                if d_id:
                    unique_decision_ids.add(d_id)

                # Classification status tracking
                cls_status = str(getattr(entry, "classification_status", "")).upper()
                if cls_status == "CLASSIFIED":
                    classified_count += 1
                else:
                    unclassified_count += 1

                # Priority tracking
                prio = str(getattr(entry, "priority", "")).upper()
                if prio == "CRITICAL":
                    critical_count += 1
                elif prio == "HIGH":
                    high_count += 1
                elif prio == "MEDIUM":
                    medium_count += 1
                elif prio == "LOW":
                    low_count += 1
                elif prio == "INFO":
                    info_count += 1

            return DecisionAuditAnalyticsSummary(
                total_entries=total_entries,
                unique_decisions=len(unique_decision_ids),
                classified_entries=classified_count,
                unclassified_entries=unclassified_count,
                high_priority_entries=high_count,
                medium_priority_entries=medium_count,
                low_priority_entries=low_count,
                info_priority_entries=info_count,
                critical_priority_entries=critical_count,
            )
        except Exception:
            return _empty_summary()

    def analyze(self, audit_trail: Optional[Any] = None) -> DecisionAuditAnalytics:
        """Analyze audit trail entries and return complete DecisionAuditAnalytics."""
        try:
            if audit_trail is None:
                svc = self._get_audit_service()
                if svc is not None and hasattr(svc, "get_audit_trail"):
                    audit_trail = svc.get_audit_trail()

            entries = (
                getattr(audit_trail, "entries", [])
                if audit_trail is not None
                else []
            )
            if not isinstance(entries, list) or not entries:
                return _empty_analytics()

            valid_entries = [e for e in entries if _is_valid_entry(e)]
            if not valid_entries:
                return _empty_analytics()

            summary = self.build_summary(valid_entries)

            category_raw: dict[str, int] = {}
            priority_raw: dict[str, int] = {}
            classification_raw: dict[str, int] = {}
            source_raw: dict[str, int] = {}

            for entry in valid_entries:
                # Category
                cat = str(getattr(entry, "category", "")).strip()
                if cat:
                    category_raw[cat] = category_raw.get(cat, 0) + 1

                # Priority
                prio = str(getattr(entry, "priority", "")).strip().upper()
                if prio:
                    priority_raw[prio] = priority_raw.get(prio, 0) + 1

                # Classification
                cls_status = (
                    str(getattr(entry, "classification_status", "")).strip().upper()
                )
                if cls_status:
                    classification_raw[cls_status] = (
                        classification_raw.get(cls_status, 0) + 1
                    )

                # Source
                src = str(getattr(entry, "source", "")).strip()
                if src:
                    source_raw[src] = source_raw.get(src, 0) + 1

            # Deterministic Ordering for Priority Counts: CRITICAL -> HIGH -> MEDIUM -> LOW -> INFO
            priority_counts: dict[str, int] = {}
            for p in self.PRIORITY_ORDER:
                if p in priority_raw:
                    priority_counts[p] = priority_raw[p]
            for p in sorted(priority_raw.keys()):
                if p not in priority_counts:
                    priority_counts[p] = priority_raw[p]

            # Deterministic Ordering for Classification Counts: CLASSIFIED -> UNCLASSIFIED
            classification_counts: dict[str, int] = {}
            for c in self.CLASSIFICATION_ORDER:
                if c in classification_raw:
                    classification_counts[c] = classification_raw[c]
            for c in sorted(classification_raw.keys()):
                if c not in classification_counts:
                    classification_counts[c] = classification_raw[c]

            # Deterministic Ordering for Category and Source Counts (Alphabetical order of present keys)
            category_counts = {k: category_raw[k] for k in sorted(category_raw.keys())}
            source_counts = {k: source_raw[k] for k in sorted(source_raw.keys())}

            return DecisionAuditAnalytics(
                summary=summary,
                category_counts=category_counts,
                priority_counts=priority_counts,
                classification_counts=classification_counts,
                source_counts=source_counts,
            )
        except Exception:
            return _empty_analytics()

    def get_analytics(self) -> DecisionAuditAnalytics:
        """Fetch audit trail and calculate analytics safely."""
        try:
            svc = self._get_audit_service()
            if svc is not None and hasattr(svc, "get_audit_trail"):
                trail = svc.get_audit_trail()
                return self.analyze(trail)
            return _empty_analytics()
        except Exception:
            return _empty_analytics()
