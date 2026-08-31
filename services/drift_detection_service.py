"""Drift Detection Engine Service (Sprint 13.7.2)



Provides descriptive target-vs-actual allocation drift detection and factual

drift history measurement for AlphaForge portfolios.

"""

from __future__ import annotations



from dataclasses import asdict, dataclass, field

from datetime import datetime, timezone

import json

import os

from typing import Any, Optional





@dataclass

class DriftMetric:

    """Represents target-vs-actual drift for a single portfolio holding with a target."""



    name: str

    current_weight: float

    target_weight: float

    drift: float

    absolute_drift: float

    direction: str  # OVERWEIGHT, UNDERWEIGHT, ON_TARGET

    action: str = "HOLD"  # HOLD (for ON_TARGET or OVERWEIGHT < 30%), REDUCE (for OVERWEIGHT >= 30%), BUY (for UNDERWEIGHT)





@dataclass

class DriftDetectionResult:

    """Container for complete portfolio drift detection summary and metrics."""



    total_positions: int

    positions_with_target: int

    positions_without_target: int

    total_absolute_drift: float

    average_absolute_drift: float

    maximum_absolute_drift: float

    metrics: list[DriftMetric] = field(default_factory=list)





@dataclass

class DriftHistoryEntry:

    """Historical record of factual portfolio drift measurement."""



    timestamp: str

    total_absolute_drift: float

    average_absolute_drift: float

    maximum_absolute_drift: float

    positions_with_target: int





@dataclass

class DriftHistory:

    """Container for chronological drift history entries."""



    total_entries: int

    earliest_timestamp: Optional[str]

    latest_timestamp: Optional[str]

    entries: list[DriftHistoryEntry] = field(default_factory=list)





def _empty_result() -> DriftDetectionResult:

    """Return a safe empty DriftDetectionResult."""

    return DriftDetectionResult(

        total_positions=0,

        positions_with_target=0,

        positions_without_target=0,

        total_absolute_drift=0.0,

        average_absolute_drift=0.0,

        maximum_absolute_drift=0.0,

        metrics=[],

    )





def _empty_history() -> DriftHistory:

    """Return a safe empty DriftHistory."""

    return DriftHistory(

        total_entries=0,

        earliest_timestamp=None,

        latest_timestamp=None,

        entries=[],

    )





def _safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:

    """Safely convert value to float or return default."""

    if val is None:

        return default

    try:

        return float(val)

    except (TypeError, ValueError):

        return default





def _is_valid_position(pos: Any) -> bool:

    """Safely check if an object is a valid position record."""

    if pos is None:

        return False

    if isinstance(pos, (str, int, float, bool, list, tuple, set)):

        return False

    return True





from config.path_config import get_data_path


class DriftDetectionService:

    """Service for calculating target-vs-actual allocation drift and maintaining drift history.



    Operates purely as a descriptive measurement engine. Does NOT evaluate rebalancing thresholds,

    rank candidates, or generate trading recommendations.

    """



    DEFAULT_HISTORY_PATH = str(get_data_path("rebalancing/drift_history.json"))



    def __init__(

        self,

        rebalancing_service: Optional[Any] = None,

        allocation_analysis_service: Optional[Any] = None,

        history_path: Optional[str] = None,

    ) -> None:

        """Initialize DriftDetectionService with optional services and custom history filepath."""

        self._rebalancing_service = rebalancing_service

        self._allocation_analysis_service = allocation_analysis_service

        self._history_path = history_path or self.DEFAULT_HISTORY_PATH



    def _get_rebalancing_service(self) -> Optional[Any]:
        """Safely retrieve or instantiate the RebalancingService."""
        if self._rebalancing_service is not None:
            return self._rebalancing_service
        try:
            from services.rebalancing_service import RebalancingService
            return RebalancingService()
        except Exception:
            return None

    def detect_drift(
        self,
        rebalancing_state: Optional[Any] = None,
        allocation_analysis: Optional[Any] = None,
    ) -> DriftDetectionResult:
        """Detect target-vs-actual drift for all positions in the given RebalancingState."""
        try:
            if rebalancing_state is None:
                return _empty_result()



            portfolio = getattr(rebalancing_state, "portfolio", None)

            positions = getattr(portfolio, "positions", []) if portfolio is not None else []

            if not isinstance(positions, list) or not positions:

                return _empty_result()



            valid_positions = [p for p in positions if _is_valid_position(p)]

            if not valid_positions:

                return _empty_result()



            total_positions = len(valid_positions)

            positions_with_target = 0

            positions_without_target = 0

            metrics: list[DriftMetric] = []



            for p in valid_positions:

                try:

                    name = str(getattr(p, "symbol", "") or getattr(p, "name", "") or "Position").strip()

                    c_wt = _safe_float(getattr(p, "current_weight", None), 0.0) or 0.0

                    t_wt = _safe_float(getattr(p, "target_weight", None), None)



                    if t_wt is None:

                        positions_without_target += 1

                        continue



                    positions_with_target += 1

                    drift = c_wt - t_wt

                    abs_drift = abs(drift)



                    if abs(drift) < 1e-4:
                        direction = "ON_TARGET"
                        action = "HOLD"
                    elif drift > 0:
                        direction = "OVERWEIGHT"
                        action = "HOLD" if c_wt < 30.0 else "REDUCE"
                    else:
                        direction = "UNDERWEIGHT"
                        action = "BUY"

                    metrics.append(
                        DriftMetric(
                            name=name,
                            current_weight=round(c_wt, 2),
                            target_weight=round(t_wt, 2),
                            drift=round(drift, 2),
                            absolute_drift=round(abs_drift, 2),
                            direction=direction,
                            action=action,
                        )
                    )

                except Exception:

                    positions_without_target += 1

                    continue



            total_abs_drift = round(sum(m.absolute_drift for m in metrics), 2)

            avg_abs_drift = round(total_abs_drift / positions_with_target, 2) if positions_with_target > 0 else 0.0

            max_abs_drift = round(max((m.absolute_drift for m in metrics), default=0.0), 2)



            return DriftDetectionResult(

                total_positions=total_positions,

                positions_with_target=positions_with_target,

                positions_without_target=positions_without_target,

                total_absolute_drift=total_abs_drift,

                average_absolute_drift=avg_abs_drift,

                maximum_absolute_drift=max_abs_drift,

                metrics=metrics,

            )

        except Exception:

            return _empty_result()



    def get_drift(self) -> DriftDetectionResult:

        """Fetch RebalancingState and compute portfolio drift analysis safely."""

        try:

            svc = self._get_rebalancing_service()

            if svc is not None and hasattr(svc, "get_state"):

                state = svc.get_state()

                return self.detect_drift(state)

            return _empty_result()

        except Exception:

            return _empty_result()



    # -----------------------------------------------------------------------

    # Persistence / History

    # -----------------------------------------------------------------------



    def load_history(self) -> DriftHistory:

        """Load factual drift history from JSON storage."""

        try:

            if not os.path.exists(self._history_path):

                return _empty_history()



            with open(self._history_path, "r", encoding="utf-8") as f:

                data = json.load(f)



            if not isinstance(data, dict):

                return _empty_history()



            raw_entries = data.get("entries", [])

            if not isinstance(raw_entries, list):

                return _empty_history()



            parsed_entries: list[DriftHistoryEntry] = []

            for item in raw_entries:

                if not isinstance(item, dict):

                    continue

                ts = str(item.get("timestamp", "") or "").strip()

                if not ts:

                    continue

                parsed_entries.append(

                    DriftHistoryEntry(

                        timestamp=ts,

                        total_absolute_drift=round(_safe_float(item.get("total_absolute_drift"), 0.0) or 0.0, 2),

                        average_absolute_drift=round(_safe_float(item.get("average_absolute_drift"), 0.0) or 0.0, 2),

                        maximum_absolute_drift=round(_safe_float(item.get("maximum_absolute_drift"), 0.0) or 0.0, 2),

                        positions_with_target=int(item.get("positions_with_target", 0) or 0),

                    )

                )



            # Sort chronologically by timestamp

            parsed_entries.sort(key=lambda x: x.timestamp)



            if not parsed_entries:

                return _empty_history()



            return DriftHistory(

                total_entries=len(parsed_entries),

                earliest_timestamp=parsed_entries[0].timestamp,

                latest_timestamp=parsed_entries[-1].timestamp,

                entries=parsed_entries,

            )

        except Exception:

            return _empty_history()



    def save_history(self, history: DriftHistory) -> None:

        """Persist DriftHistory object to JSON storage."""

        try:

            directory = os.path.dirname(self._history_path)

            if directory and not os.path.exists(directory):

                os.makedirs(directory, exist_ok=True)



            entries = history.entries if history and isinstance(history.entries, list) else []

            sorted_entries = sorted(entries, key=lambda x: x.timestamp)



            data = {

                "total_entries": len(sorted_entries),

                "earliest_timestamp": sorted_entries[0].timestamp if sorted_entries else None,

                "latest_timestamp": sorted_entries[-1].timestamp if sorted_entries else None,

                "entries": [asdict(e) for e in sorted_entries],

            }



            temp_path = self._history_path + ".tmp"

            with open(temp_path, "w", encoding="utf-8") as f:

                json.dump(data, f, indent=2)

            os.replace(temp_path, self._history_path)

        except Exception:

            pass



    def record_history(self, result: Optional[DriftDetectionResult], timestamp: Optional[str] = None) -> DriftHistory:

        """Record a factual drift measurement into history, preventing duplicate timestamps."""

        try:

            if result is None:

                result = _empty_result()



            ts = timestamp or datetime.now(timezone.utc).isoformat()

            history = self.load_history()



            # Prevent duplicate timestamp entries

            existing_timestamps = {e.timestamp for e in history.entries}

            if ts not in existing_timestamps:

                entry = DriftHistoryEntry(

                    timestamp=ts,

                    total_absolute_drift=result.total_absolute_drift,

                    average_absolute_drift=result.average_absolute_drift,

                    maximum_absolute_drift=result.maximum_absolute_drift,

                    positions_with_target=result.positions_with_target,

                )

                history.entries.append(entry)

                history.entries.sort(key=lambda x: x.timestamp)

                history.total_entries = len(history.entries)

                history.earliest_timestamp = history.entries[0].timestamp

                history.latest_timestamp = history.entries[-1].timestamp

                self.save_history(history)



            return history

        except Exception:

            return _empty_history()
