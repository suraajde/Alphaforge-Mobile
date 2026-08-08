"""Rebalancing Candidate Engine Service (Sprint 13.7.3)



Identifies, measures, and ranks potential rebalancing candidates based on

measurable allocation drift and impact value.

"""

from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Optional





@dataclass

class RebalancingCandidate:

    """Represents a measured candidate for potential rebalancing evaluation."""



    symbol: str

    name: str

    asset_type: str

    current_weight: float

    target_weight: float

    drift: float

    absolute_drift: float

    direction: str

    impact_value: float

    scenario_weight: float

    scenario_delta: float

    candidate_score: float

    rank: int





@dataclass

class RebalancingCandidateResult:

    """Container for complete candidate identification and evaluation summary."""



    total_candidates: int

    overweight_candidates: int

    underweight_candidates: int

    on_target_candidates: int

    total_impact_value: float

    candidates: list[RebalancingCandidate] = field(default_factory=list)





def _empty_result() -> RebalancingCandidateResult:

    """Return a safe empty RebalancingCandidateResult."""

    return RebalancingCandidateResult(

        total_candidates=0,

        overweight_candidates=0,

        underweight_candidates=0,

        on_target_candidates=0,

        total_impact_value=0.0,

        candidates=[],

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





class RebalancingCandidateService:

    """Service for identifying, scoring, and ranking rebalancing candidates.



    Operates purely as a descriptive candidate identification engine.

    Does NOT make investment recommendations, generate trade orders, or execute rebalances.

    """



    def __init__(

        self,

        rebalancing_service: Optional[Any] = None,

        allocation_analysis_service: Optional[Any] = None,

        drift_detection_service: Optional[Any] = None,

    ) -> None:

        """Initialize RebalancingCandidateService with optional dependent services."""

        self._rebalancing_service = rebalancing_service

        self._allocation_analysis_service = allocation_analysis_service

        self._drift_detection_service = drift_detection_service



    def _get_rebalancing_service(self) -> Optional[Any]:

        """Safely retrieve or instantiate the RebalancingService."""

        if self._rebalancing_service is not None:

            return self._rebalancing_service

        try:

            from services.rebalancing_service import RebalancingService



            return RebalancingService()

        except Exception:

            return None



    def identify_candidates(

        self,

        rebalancing_state: Optional[Any] = None,

        allocation_analysis: Optional[Any] = None,

        drift_detection: Optional[Any] = None,

    ) -> RebalancingCandidateResult:

        """Identify, score, and rank potential rebalancing candidates from portfolio data."""

        try:

            if rebalancing_state is None:

                svc = self._get_rebalancing_service()

                if svc is not None and hasattr(svc, "get_state"):

                    rebalancing_state = svc.get_state()



            if rebalancing_state is None:

                return _empty_result()



            portfolio = getattr(rebalancing_state, "portfolio", None)

            positions = getattr(portfolio, "positions", []) if portfolio is not None else []

            if not isinstance(positions, list) or not positions:

                return _empty_result()



            valid_positions = [p for p in positions if _is_valid_position(p)]

            if not valid_positions:

                return _empty_result()



            total_val = _safe_float(getattr(portfolio, "total_value", None) or getattr(rebalancing_state, "total_value", None), 0.0) or 0.0



            # Map drift metrics by position symbol or name if drift_detection is provided

            drift_map: dict[str, Any] = {}

            if drift_detection is not None and hasattr(drift_detection, "metrics"):

                raw_metrics = getattr(drift_detection, "metrics", []) or []

                if isinstance(raw_metrics, list):

                    for m in raw_metrics:

                        m_name = str(getattr(m, "name", "") or "").strip()

                        if m_name:

                            drift_map[m_name] = m



            unranked_candidates: list[RebalancingCandidate] = []



            for p in valid_positions:

                try:

                    t_wt = _safe_float(getattr(p, "target_weight", None), None)

                    if t_wt is None:

                        continue



                    sym = str(getattr(p, "symbol", "") or "").strip()

                    name = str(getattr(p, "name", "") or sym or "Candidate").strip()

                    asset_type = str(getattr(p, "asset_type", "") or "EQUITY").strip()

                    c_wt = _safe_float(getattr(p, "current_weight", None), 0.0) or 0.0



                    lookup_key = sym if sym in drift_map else name

                    drift_metric = drift_map.get(lookup_key)



                    if drift_metric is not None:

                        drift = _safe_float(getattr(drift_metric, "drift", None), c_wt - t_wt) or (c_wt - t_wt)

                        abs_drift = _safe_float(getattr(drift_metric, "absolute_drift", None), abs(drift)) or abs(drift)

                        direction = str(getattr(drift_metric, "direction", "") or "").strip()

                    else:

                        drift = c_wt - t_wt

                        abs_drift = abs(drift)

                        direction = ""



                    if not direction:

                        if abs(drift) < 1e-4:

                            direction = "ON_TARGET"

                        elif drift > 0:

                            direction = "OVERWEIGHT"

                        else:

                            direction = "UNDERWEIGHT"



                    impact_val = (abs_drift / 100.0) * total_val if total_val > 0 else 0.0

                    scenario_wt = t_wt

                    scenario_dl = t_wt - c_wt

                    candidate_sc = abs_drift



                    unranked_candidates.append(

                        RebalancingCandidate(

                            symbol=sym or name,

                            name=name,

                            asset_type=asset_type,

                            current_weight=round(c_wt, 2),

                            target_weight=round(t_wt, 2),

                            drift=round(drift, 2),

                            absolute_drift=round(abs_drift, 2),

                            direction=direction,

                            impact_value=round(impact_val, 2),

                            scenario_weight=round(scenario_wt, 2),

                            scenario_delta=round(scenario_dl, 2),

                            candidate_score=round(candidate_sc, 2),

                            rank=0,  # Will be assigned during sorting

                        )

                    )

                except Exception:

                    continue



            if not unranked_candidates:

                return _empty_result()



            # Rank candidates deterministically: candidate_score desc, absolute_drift desc, symbol asc

            unranked_candidates.sort(key=lambda c: (-c.candidate_score, -c.absolute_drift, c.symbol))



            ranked_candidates: list[RebalancingCandidate] = []

            overweight_count = 0

            underweight_count = 0

            on_target_count = 0



            for idx, cand in enumerate(unranked_candidates, start=1):

                cand.rank = idx

                ranked_candidates.append(cand)

                if cand.direction == "OVERWEIGHT":

                    overweight_count += 1

                elif cand.direction == "UNDERWEIGHT":

                    underweight_count += 1

                else:

                    on_target_count += 1



            total_impact = round(sum(c.impact_value for c in ranked_candidates), 2)



            return RebalancingCandidateResult(

                total_candidates=len(ranked_candidates),

                overweight_candidates=overweight_count,

                underweight_candidates=underweight_count,

                on_target_candidates=on_target_count,

                total_impact_value=total_impact,

                candidates=ranked_candidates,

            )

        except Exception:

            return _empty_result()



    def get_candidates(self) -> RebalancingCandidateResult:

        """Fetch portfolio state and compute rebalancing candidates safely."""

        try:

            svc = self._get_rebalancing_service()

            if svc is not None and hasattr(svc, "get_state"):

                state = svc.get_state()

                return self.identify_candidates(rebalancing_state=state)

            return _empty_result()

        except Exception:

            return _empty_result()
