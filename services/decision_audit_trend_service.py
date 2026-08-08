"""Decision Audit Trend Service (Sprint 16.0.6)



Computes cumulative chronological trend points and overall audit volume direction

from existing Decision Audit Trail entries.

"""

from __future__ import annotations



from dataclasses import dataclass

from typing import Any, Optional





@dataclass

class DecisionAuditTrendPoint:

    """Cumulative trend snapshot at a specific audit timestamp."""



    timestamp: str

    total_entries: int

    classified_entries: int

    unclassified_entries: int

    high_priority_entries: int

    medium_priority_entries: int

    low_priority_entries: int

    info_priority_entries: int

    critical_priority_entries: int





@dataclass

class DecisionAuditTrend:

    """Complete decision audit trend summary with ordered points."""



    total_points: int

    earliest_timestamp: Optional[str]

    latest_timestamp: Optional[str]

    direction: str

    points: list[DecisionAuditTrendPoint]





def _empty_trend() -> DecisionAuditTrend:

    """Return a safe empty trend result."""

    return DecisionAuditTrend(

        total_points=0,

        earliest_timestamp=None,

        latest_timestamp=None,

        direction="STABLE",

        points=[],

    )





def _is_valid_entry(entry: Any) -> bool:

    """Safely check if an object is a valid entry record."""

    if entry is None:

        return False

    if isinstance(entry, (str, int, float, bool, list, tuple, set)):

        return False

    return True





class DecisionAuditTrendService:

    """Service for computing cumulative chronological trend points from audit entries.



    Operates purely as an analytical trend engine on existing audit records.

    Never modifies audit history or decision rules.

    """



    def __init__(self, audit_service: Optional[Any] = None) -> None:

        """Initialize DecisionAuditTrendService with an optional audit service dependency."""

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



    def build_trend(

        self, audit_trail: Optional[Any] = None

    ) -> DecisionAuditTrend:

        """Build cumulative chronological trend points from audit trail entries."""

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

                return _empty_trend()



            valid_entries = [e for e in entries if _is_valid_entry(e)]

            if not valid_entries:

                return _empty_trend()



            # Filter out items without timestamp and sort chronologically (OLDEST -> NEWEST)

            ts_entries = []

            for entry in valid_entries:

                ts = str(getattr(entry, "timestamp", "")).strip()

                if ts:

                    ts_entries.append((ts, entry))



            if not ts_entries:

                return _empty_trend()



            ts_entries.sort(key=lambda item: item[0])



            # Group entries by timestamp while preserving chronological order

            grouped_entries: dict[str, list[Any]] = {}

            for ts, entry in ts_entries:

                if ts not in grouped_entries:

                    grouped_entries[ts] = []

                grouped_entries[ts].append(entry)



            points: list[DecisionAuditTrendPoint] = []

            running_total = 0

            running_classified = 0

            running_unclassified = 0

            running_critical = 0

            running_high = 0

            running_medium = 0

            running_low = 0

            running_info = 0



            for ts, group in grouped_entries.items():

                for item in group:

                    running_total += 1



                    cls_status = (

                        str(getattr(item, "classification_status", "")).strip().upper()

                    )

                    if cls_status == "CLASSIFIED":

                        running_classified += 1

                    else:

                        running_unclassified += 1



                    prio = str(getattr(item, "priority", "")).strip().upper()

                    if prio == "CRITICAL":

                        running_critical += 1

                    elif prio == "HIGH":

                        running_high += 1

                    elif prio == "MEDIUM":

                        running_medium += 1

                    elif prio == "LOW":

                        running_low += 1

                    elif prio == "INFO":

                        running_info += 1



                point = DecisionAuditTrendPoint(

                    timestamp=ts,

                    total_entries=running_total,

                    classified_entries=running_classified,

                    unclassified_entries=running_unclassified,

                    high_priority_entries=running_high,

                    medium_priority_entries=running_medium,

                    low_priority_entries=running_low,

                    info_priority_entries=running_info,

                    critical_priority_entries=running_critical,

                )

                points.append(point)



            if not points:

                return _empty_trend()



            earliest_timestamp = points[0].timestamp

            latest_timestamp = points[-1].timestamp



            # Direction calculation based on first and latest cumulative total_entries

            if len(points) < 2:

                direction = "STABLE"

            else:

                first_total = points[0].total_entries

                latest_total = points[-1].total_entries

                if latest_total > first_total:

                    direction = "INCREASING"

                elif latest_total < first_total:

                    direction = "DECREASING"

                else:

                    direction = "STABLE"



            return DecisionAuditTrend(

                total_points=len(points),

                earliest_timestamp=earliest_timestamp,

                latest_timestamp=latest_timestamp,

                direction=direction,

                points=points,

            )

        except Exception:

            return _empty_trend()



    def get_trend(self) -> DecisionAuditTrend:

        """Fetch audit trail and build decision audit trend safely."""

        try:

            svc = self._get_audit_service()

            if svc is not None and hasattr(svc, "get_audit_trail"):

                trail = svc.get_audit_trail()

                return self.build_trend(trail)

            return _empty_trend()

        except Exception:

            return _empty_trend()
