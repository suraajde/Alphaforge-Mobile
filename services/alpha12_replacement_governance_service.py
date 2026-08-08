"""Alpha 12 Replacement Governance Service (Sprint 13.9.3)

Determines whether an Alpha 12 challenger is eligible for replacement review.

This service enforces conservative, incumbent-protective governance rules.
A strong incumbent remains protected unless there is:
- meaningful incumbent deterioration
- materially superior challenger
- sufficient evidence

The service produces deterministic governance decisions for review, not replacement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib


@dataclass
class ReplacementGovernanceRecord:
    """Governance evaluation for a single challenger-incumbent pair."""

    replacement_id: str
    incumbent_symbol: str
    incumbent_name: Optional[str] = None
    challenger_symbol: str = ""
    challenger_name: Optional[str] = None

    governance_status: str = "UNAVAILABLE"

    incumbent_rank: Optional[int] = None
    challenger_rank: Optional[int] = None

    incumbent_score: Optional[float] = None
    challenger_score: Optional[float] = None
    score_difference: Optional[float] = None

    incumbent_quality_score: Optional[float] = None
    challenger_quality_score: Optional[float] = None
    quality_difference: Optional[float] = None

    incumbent_risk_score: Optional[float] = None
    challenger_risk_score: Optional[float] = None
    risk_advantage: Optional[float] = None

    material_superiority: bool = False
    meaningful_deterioration: bool = False

    governance_score: float = 0.0
    priority: str = "LOW"

    evidence: List[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class ReplacementGovernanceResult:
    """Aggregate governance evaluation result."""

    analysis_status: str = "OK"

    total_evaluations: int = 0
    review_eligible_count: int = 0
    protected_incumbent_count: int = 0
    insufficient_evidence_count: int = 0
    unavailable_count: int = 0

    average_governance_score: float = 0.0
    highest_governance_score: float = 0.0

    records: List[ReplacementGovernanceRecord] = field(default_factory=list)

    rationale: str = ""


# Governance status constants
PROTECT_INCUMBENT = "PROTECT_INCUMBENT"
REVIEW_ELIGIBLE = "REVIEW_ELIGIBLE"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
UNAVAILABLE = "UNAVAILABLE"

# Priority constants
PRIORITY_HIGH = "HIGH"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_LOW = "LOW"

# Material superiority thresholds (from Sprint 13.9.2)
SCORE_DIFF_THRESHOLD = 12.0
QUALITY_DIFF_THRESHOLD = 8.0
RISK_ADVANTAGE_THRESHOLD = 5.0


class Alpha12ReplacementGovernanceService:
    """Deterministic replacement governance engine for Alpha 12.

    Enforces conservative, incumbent-protective rules.
    Never executes replacements; only evaluates eligibility for review.
    """

    def __init__(
        self,
        alpha12_mapping_service: Optional[Any] = None,
        alpha12_challenger_service: Optional[Any] = None,
        alpha12_health_integration_service: Optional[Any] = None,
        portfolio_health_service: Optional[Any] = None,
    ) -> None:
        """Initialize service with optional dependencies."""
        self._alpha12_mapping_service = alpha12_mapping_service
        self._alpha12_challenger_service = alpha12_challenger_service
        self._alpha12_health_integration_service = alpha12_health_integration_service
        self._portfolio_health_service = portfolio_health_service

    @staticmethod
    def _safe_float(v: Any) -> Optional[float]:
        """Safely convert to float, returning None if not possible."""
        try:
            if v is None:
                return None
            return float(v)
        except Exception:
            return None

    @staticmethod
    def _safe_int(v: Any) -> Optional[int]:
        """Safely convert to int, returning None if not possible."""
        try:
            if v is None:
                return None
            return int(v)
        except Exception:
            return None

    @staticmethod
    def _clamp_score(v: float) -> float:
        """Clamp score to 0-100 range."""
        if v is None:
            return 0.0
        if v < 0:
            return 0.0
        if v > 100:
            return 100.0
        return float(round(v, 2))

    def _generate_replacement_id(
        self,
        incumbent_symbol: str,
        challenger_symbol: str,
    ) -> str:
        """Generate deterministic replacement ID using SHA-256."""
        try:
            combined = f"{incumbent_symbol}:{challenger_symbol}"
            hash_obj = hashlib.sha256(combined.encode())
            return hash_obj.hexdigest()[:16]
        except Exception:
            return f"{incumbent_symbol}_{challenger_symbol}"

    def _get_mapping_result(self) -> Optional[Dict[str, Any]]:
        """Get Alpha 12 mapping result from service."""
        try:
            if self._alpha12_mapping_service is None:
                return None
            if hasattr(self._alpha12_mapping_service, "get_mapping"):
                return self._alpha12_mapping_service.get_mapping()
            return None
        except Exception:
            return None

    def _get_challenger_result(self) -> Optional[Any]:
        """Get challenger evaluation result from service."""
        try:
            if self._alpha12_challenger_service is None:
                return None
            if hasattr(self._alpha12_challenger_service, "evaluate"):
                # Requires mapping, health, quality, risk inputs
                return self._alpha12_challenger_service.evaluate()
            return None
        except Exception:
            return None

    def _get_health_result(self) -> Optional[Any]:
        """Get portfolio health result from service."""
        try:
            if self._portfolio_health_service is None:
                return None
            if hasattr(self._portfolio_health_service, "evaluate"):
                return self._portfolio_health_service.evaluate()
            return None
        except Exception:
            return None

    def _evaluate_material_superiority(
        self,
        score_diff: Optional[float],
        quality_diff: Optional[float],
        risk_advantage: Optional[float],
    ) -> bool:
        """Evaluate if challenger demonstrates material superiority.

        Requires multiple dimensions to qualify (conservative rule).
        """
        s_diff = self._safe_float(score_diff)
        q_diff = self._safe_float(quality_diff)
        r_adv = self._safe_float(risk_advantage)

        # All three dimensions required for material superiority
        if s_diff is None or q_diff is None or r_adv is None:
            return False

        # Must exceed thresholds in all dimensions
        return (
            s_diff >= SCORE_DIFF_THRESHOLD
            and q_diff >= QUALITY_DIFF_THRESHOLD
            and r_adv >= RISK_ADVANTAGE_THRESHOLD
        )

    def _evaluate_incumbent_deterioration(
        self,
        incumbent_quality: Optional[float],
        incumbent_health_grade: Optional[str],
        challenger_evaluation: Optional[Dict[str, Any]],
    ) -> bool:
        """Evaluate if incumbent demonstrates meaningful deterioration.

        Conservative: only recognize clear deterioration signals.
        """
        evidence = []

        # Quality score <= 50 indicates weak holding
        inc_quality = self._safe_float(incumbent_quality)
        if inc_quality is not None and inc_quality <= 50.0:
            evidence.append("Incumbent quality weak (≤50)")

        # Health grade D, E, F, or POOR
        if isinstance(incumbent_health_grade, str):
            grade = str(incumbent_health_grade).upper()
            if grade in ("D", "E", "F", "POOR"):
                evidence.append(f"Incumbent health poor ({grade})")

        # Check challenger evaluation for explicit deterioration flag
        if isinstance(challenger_evaluation, dict):
            detected = challenger_evaluation.get("deterioration_detected")
            if detected is True:
                evidence.append("Deterioration detected in challenger evaluation")

        # Meaningful deterioration requires at least one strong signal
        return len(evidence) > 0

    def _calculate_governance_score(
        self,
        material_superiority: bool,
        meaningful_deterioration: bool,
        score_diff: Optional[float],
        quality_diff: Optional[float],
        risk_advantage: Optional[float],
        rank_diff: Optional[int],
    ) -> float:
        """Calculate transparent governance evidence strength score 0-100.

        This is NOT a probability or return forecast.
        It represents only the strength of governance evidence.
        """
        base_score = 0.0

        # Material superiority components (max 50 points)
        if material_superiority:
            base_score += 30.0
        else:
            # Partial credit for approaching thresholds
            s_diff = self._safe_float(score_diff) or 0.0
            q_diff = self._safe_float(quality_diff) or 0.0
            r_adv = self._safe_float(risk_advantage) or 0.0

            # Each dimension gets up to ~10 points for approaching threshold
            base_score += min(10.0, (s_diff / SCORE_DIFF_THRESHOLD) * 10.0)
            base_score += min(10.0, (q_diff / QUALITY_DIFF_THRESHOLD) * 10.0)
            base_score += min(10.0, (r_adv / RISK_ADVANTAGE_THRESHOLD) * 10.0)

        # Deterioration signals (max 30 points)
        if meaningful_deterioration:
            base_score += 30.0

        # Rank advantage (max 20 points, conservative)
        rank = self._safe_int(rank_diff)
        if rank is not None and rank > 0:
            base_score += min(20.0, rank * 2.0)

        return self._clamp_score(base_score)

    def _classify_governance_status(
        self,
        material_superiority: bool,
        meaningful_deterioration: bool,
        challenger_score: Optional[float],
        score_difference: Optional[float],
        evidence_completeness: float,
    ) -> str:
        """Classify governance status deterministically.

        Conservative default: PROTECT_INCUMBENT.
        Only REVIEW_ELIGIBLE when conditions are compelling.
        """
        # If data unavailable, cannot proceed
        if challenger_score is None:
            return UNAVAILABLE

        # Material superiority + meaningful deterioration -> review eligible
        if material_superiority and meaningful_deterioration:
            return REVIEW_ELIGIBLE

        # Material superiority alone is insufficient without deterioration
        if material_superiority and not meaningful_deterioration:
            return PROTECT_INCUMBENT

        # Weak evidence -> insufficient
        if evidence_completeness < 0.5:
            return INSUFFICIENT_EVIDENCE

        # Default: protect incumbent (conservative stance)
        return PROTECT_INCUMBENT

    def _build_evidence(
        self,
        material_superiority: bool,
        meaningful_deterioration: bool,
        score_diff: Optional[float],
        quality_diff: Optional[float],
        risk_advantage: Optional[float],
        incumbent_quality: Optional[float],
        incumbent_health: Optional[str],
        rank_diff: Optional[int],
    ) -> List[str]:
        """Build transparent evidence list."""
        evidence = []

        # Material superiority evidence
        if material_superiority:
            evidence.append(
                f"Material superiority confirmed: "
                f"score_diff={score_diff}, quality_diff={quality_diff}, risk_adv={risk_advantage}"
            )

        # Deterioration evidence
        if meaningful_deterioration:
            if (
                self._safe_float(incumbent_quality) is not None
                and self._safe_float(incumbent_quality) <= 50.0
            ):
                evidence.append(f"Incumbent quality weak: {incumbent_quality}")
            if isinstance(incumbent_health, str) and incumbent_health.upper() in (
                "D",
                "E",
                "F",
                "POOR",
            ):
                evidence.append(f"Incumbent health poor: {incumbent_health}")

        # Rank advantage
        if self._safe_int(rank_diff) is not None and rank_diff > 0:
            evidence.append(f"Challenger rank better by {rank_diff} positions")

        # Score advantage
        if self._safe_float(score_diff) is not None and score_diff > 0:
            evidence.append(f"Challenger score advantage: {score_diff} points")

        # Quality advantage
        if self._safe_float(quality_diff) is not None and quality_diff > 0:
            evidence.append(f"Challenger quality advantage: {quality_diff} points")

        # Risk advantage
        if self._safe_float(risk_advantage) is not None and risk_advantage > 0:
            evidence.append(
                f"Challenger risk advantage: {risk_advantage} points lower risk"
            )

        if not evidence:
            evidence.append("No material advantage detected")

        return evidence

    def _sort_records(
        self,
        records: List[ReplacementGovernanceRecord],
    ) -> List[ReplacementGovernanceRecord]:
        """Sort records deterministically.

        Priority: status, score desc, challenger symbol asc, incumbent symbol asc, id asc.
        """
        status_order = {
            REVIEW_ELIGIBLE: 0,
            INSUFFICIENT_EVIDENCE: 1,
            PROTECT_INCUMBENT: 2,
            UNAVAILABLE: 3,
        }

        def sort_key(r: ReplacementGovernanceRecord):
            status_priority = status_order.get(r.governance_status, 999)
            score_desc = -r.governance_score  # negative for descending
            return (status_priority, score_desc, r.challenger_symbol, r.incumbent_symbol, r.replacement_id)

        return sorted(records, key=sort_key)

    def evaluate_replacements(
        self,
        state_input: Optional[Dict[str, Any]] = None,
    ) -> ReplacementGovernanceResult:
        """Evaluate replacement governance for all challengers.

        Consumes challenger evaluation from Sprint 13.9.2.
        Produces deterministic governance decisions.
        """
        result = ReplacementGovernanceResult()

        try:
            # Get challenger evaluation (primary source)
            challenger_result = self._get_challenger_result()
            if challenger_result is None:
                result.analysis_status = "NO_CHALLENGER_DATA"
                result.rationale = "Challenger evaluation unavailable"
                return result

            # Extract challenger records
            challenger_records = []
            if hasattr(challenger_result, "challenger_records"):
                challenger_records = challenger_result.challenger_records or []
            elif isinstance(challenger_result, dict):
                challenger_records = challenger_result.get("challenger_records") or []

            if not isinstance(challenger_records, list):
                challenger_records = []

            if not challenger_records:
                result.analysis_status = "NO_CHALLENGERS"
                result.rationale = "No challenger records found"
                return result

            # Process each challenger
            records: List[ReplacementGovernanceRecord] = []

            for challenger in challenger_records:
                if not isinstance(challenger, dict):
                    continue

                try:
                    # Extract incumbent and challenger info
                    incumbent_symbol = str(
                        challenger.get("incumbent_symbol") or ""
                    ).strip().upper()
                    challenger_symbol = str(
                        challenger.get("symbol") or ""
                    ).strip().upper()

                    if not incumbent_symbol or not challenger_symbol:
                        continue

                    # Generate replacement ID
                    replacement_id = self._generate_replacement_id(
                        incumbent_symbol,
                        challenger_symbol,
                    )

                    # Extract scores and metrics
                    inc_rank = self._safe_int(challenger.get("incumbent_rank"))
                    ch_rank = self._safe_int(challenger.get("challenger_rank"))
                    rank_diff = (
                        (inc_rank - ch_rank)
                        if inc_rank is not None and ch_rank is not None
                        else None
                    )

                    inc_score = self._safe_float(challenger.get("incumbent_score"))
                    ch_score = self._safe_float(challenger.get("challenger_score"))
                    score_diff = self._safe_float(challenger.get("score_difference"))

                    inc_quality = self._safe_float(
                        challenger.get("incumbent_quality_score")
                    )
                    ch_quality = self._safe_float(
                        challenger.get("quality_score")
                    )
                    quality_diff = self._safe_float(
                        challenger.get("quality_difference")
                    )

                    inc_risk = self._safe_float(
                        challenger.get("incumbent_risk_score")
                    )
                    ch_risk = self._safe_float(challenger.get("risk_score"))
                    risk_advantage = self._safe_float(
                        challenger.get("risk_difference")
                    )

                    # Evaluate material superiority
                    material_superiority = self._evaluate_material_superiority(
                        score_diff,
                        quality_diff,
                        risk_advantage,
                    )

                    # Evaluate deterioration
                    meaningful_deterioration = (
                        self._evaluate_incumbent_deterioration(
                            inc_quality,
                            challenger.get("incumbent_health_status"),
                            challenger,
                        )
                    )

                    # Calculate governance score
                    gov_score = self._calculate_governance_score(
                        material_superiority,
                        meaningful_deterioration,
                        score_diff,
                        quality_diff,
                        risk_advantage,
                        rank_diff,
                    )

                    # Determine evidence completeness
                    evidence_completeness = 0.0
                    completeness_count = 0
                    if ch_score is not None:
                        completeness_count += 1
                    if inc_score is not None:
                        completeness_count += 1
                    if ch_quality is not None:
                        completeness_count += 1
                    if inc_quality is not None:
                        completeness_count += 1
                    if ch_risk is not None:
                        completeness_count += 1
                    if inc_risk is not None:
                        completeness_count += 1
                    if completeness_count >= 4:
                        evidence_completeness = 1.0
                    elif completeness_count >= 2:
                        evidence_completeness = 0.5
                    else:
                        evidence_completeness = 0.0

                    # Classify governance status
                    governance_status = self._classify_governance_status(
                        material_superiority,
                        meaningful_deterioration,
                        ch_score,
                        score_diff,
                        evidence_completeness,
                    )

                    # Determine priority
                    if governance_status == REVIEW_ELIGIBLE:
                        priority = PRIORITY_HIGH if gov_score >= 70 else PRIORITY_MEDIUM
                    elif governance_status == INSUFFICIENT_EVIDENCE:
                        priority = PRIORITY_MEDIUM
                    else:
                        priority = PRIORITY_LOW

                    # Build evidence
                    evidence = self._build_evidence(
                        material_superiority,
                        meaningful_deterioration,
                        score_diff,
                        quality_diff,
                        risk_advantage,
                        inc_quality,
                        challenger.get("incumbent_health_status"),
                        rank_diff,
                    )

                    # Build rationale
                    if governance_status == REVIEW_ELIGIBLE:
                        rationale = (
                            f"Challenger {challenger_symbol} may warrant review: "
                            f"material superiority confirmed and incumbent deterioration detected"
                        )
                    elif governance_status == PROTECT_INCUMBENT:
                        rationale = f"Incumbent {incumbent_symbol} protected: insufficient deterioration or marginal advantage"
                    elif governance_status == INSUFFICIENT_EVIDENCE:
                        rationale = f"Insufficient evidence for governance decision on {challenger_symbol} vs {incumbent_symbol}"
                    else:
                        rationale = f"Governance data unavailable for {challenger_symbol}"

                    # Create record
                    record = ReplacementGovernanceRecord(
                        replacement_id=replacement_id,
                        incumbent_symbol=incumbent_symbol,
                        incumbent_name=str(
                            challenger.get("incumbent_name") or ""
                        ).strip() or None,
                        challenger_symbol=challenger_symbol,
                        challenger_name=str(
                            challenger.get("name") or ""
                        ).strip() or None,
                        governance_status=governance_status,
                        incumbent_rank=inc_rank,
                        challenger_rank=ch_rank,
                        incumbent_score=inc_score,
                        challenger_score=ch_score,
                        score_difference=score_diff,
                        incumbent_quality_score=inc_quality,
                        challenger_quality_score=ch_quality,
                        quality_difference=quality_diff,
                        incumbent_risk_score=inc_risk,
                        challenger_risk_score=ch_risk,
                        risk_advantage=risk_advantage,
                        material_superiority=material_superiority,
                        meaningful_deterioration=meaningful_deterioration,
                        governance_score=gov_score,
                        priority=priority,
                        evidence=evidence,
                        rationale=rationale,
                    )

                    records.append(record)

                    # Update counters
                    result.total_evaluations += 1
                    if governance_status == REVIEW_ELIGIBLE:
                        result.review_eligible_count += 1
                    elif governance_status == PROTECT_INCUMBENT:
                        result.protected_incumbent_count += 1
                    elif governance_status == INSUFFICIENT_EVIDENCE:
                        result.insufficient_evidence_count += 1
                    else:
                        result.unavailable_count += 1

                except Exception:
                    # Skip malformed record
                    continue

            # Sort records
            result.records = self._sort_records(records)

            # Calculate aggregate metrics
            if result.total_evaluations > 0:
                total_score = sum(r.governance_score for r in result.records)
                result.average_governance_score = self._clamp_score(
                    total_score / result.total_evaluations
                )
                if result.records:
                    result.highest_governance_score = max(
                        r.governance_score for r in result.records
                    )

            result.analysis_status = "OK"
            result.rationale = (
                f"Evaluated {result.total_evaluations} replacements: "
                f"{result.review_eligible_count} eligible, "
                f"{result.protected_incumbent_count} protected, "
                f"{result.insufficient_evidence_count} insufficient evidence"
            )

            return result

        except Exception:
            result.analysis_status = "ERROR"
            result.rationale = "Unexpected service error"
            return result

    def get_governance(
        self,
        state_input: Optional[Dict[str, Any]] = None,
    ) -> ReplacementGovernanceResult:
        """Alias for evaluate_replacements (consistent interface)."""
        return self.evaluate_replacements(state_input)
