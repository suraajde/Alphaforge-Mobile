from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


@dataclass
class Alpha12Challenger:
    symbol: str
    name: Optional[str] = None
    asset_type: Optional[str] = None
    challenger_rank: Optional[int] = None
    challenger_score: Optional[float] = None
    incumbent_symbol: Optional[str] = None
    incumbent_name: Optional[str] = None
    incumbent_rank: Optional[int] = None
    incumbent_score: Optional[float] = None
    score_difference: Optional[float] = None
    quality_score: Optional[float] = None
    incumbent_quality_score: Optional[float] = None
    quality_difference: Optional[float] = None
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    sector: Optional[str] = None
    incumbent_sector: Optional[str] = None
    sector_overlap: Optional[bool] = None
    risk_score: Optional[float] = None
    incumbent_risk_score: Optional[float] = None
    risk_difference: Optional[float] = None
    portfolio_health_status: Optional[str] = None
    incumbent_health_status: Optional[str] = None
    deterioration_detected: Optional[bool] = None
    material_superiority: Optional[bool] = None
    evaluation_status: Optional[str] = None
    governance_status: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    rationale: Optional[str] = None


@dataclass
class Alpha12ChallengerResult:
    total_challengers_evaluated: int = 0
    incumbents_evaluated: int = 0
    strong_candidates: int = 0
    review_candidates: int = 0
    protected_incumbents: int = 0
    insufficient_data: int = 0
    average_challenger_score: float = 0.0
    average_score_advantage: float = 0.0
    latest_evaluation_timestamp: str = ""
    challenger_records: List[Alpha12Challenger] = field(default_factory=list)


# Governance statuses
PROTECT_INCUMBENT = "PROTECT_INCUMBENT"
MONITOR_CHALLENGER = "MONITOR_CHALLENGER"
REVIEW_CANDIDATE = "REVIEW_CANDIDATE"
STRONG_CANDIDATE = "STRONG_CANDIDATE"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class Alpha12ChallengerService:
    """Deterministic, explainable challenger evaluation engine for Alpha 12.

    This service reads existing Alpha12 mapping/ranking and produces a governance-oriented
    evaluation. It is defensive: failures never raise and missing inputs do not get fabricated.
    """

    def __init__(
        self,
        alpha12_mapping_service: Optional[Any] = None,
        alpha12_health_integration_service: Optional[Any] = None,
        holding_quality_service: Optional[Any] = None,
        portfolio_risk_intelligence_service: Optional[Any] = None,
    ) -> None:
        self._alpha12_mapping_service = alpha12_mapping_service
        self._alpha12_health_integration_service = alpha12_health_integration_service
        self._holding_quality_service = holding_quality_service
        self._portfolio_risk_intelligence_service = portfolio_risk_intelligence_service

    @staticmethod
    def _safe_float(v: Any) -> Optional[float]:
        try:
            if v is None:
                return None
            return float(v)
        except Exception:
            return None

    @staticmethod
    def _clamp_score(v: float) -> float:
        if v is None:
            return 0.0
        if v < 0:
            return 0.0
        if v > 100:
            return 100.0
        return float(round(v, 2))

    def _compute_candidate_score(self, alpha12_score: Optional[float], quality: Optional[float], risk: Optional[float]) -> Optional[float]:
        # Require at least one primary metric to compute a score; prefer all three.
        if alpha12_score is None and quality is None and risk is None:
            return None
        a = alpha12_score if alpha12_score is not None else 50.0
        q = quality if quality is not None else 50.0
        r = risk if risk is not None else 50.0
        # deterministic weighted combination (alpha12:40%, quality:30%, risk inverse:30%)
        score = (0.4 * a) + (0.3 * q) + (0.3 * (100.0 - r))
        return self._clamp_score(score)

    def evaluate(
        self,
        alpha12_mapping: Optional[Dict[str, Any]] = None,
        portfolio_health_result: Optional[Any] = None,
        holding_quality: Optional[Any] = None,
        portfolio_risk: Optional[Any] = None,
    ) -> Alpha12ChallengerResult:
        result = Alpha12ChallengerResult()

        try:
            challengers = []
            # Expect mapping to carry challengers list under 'challengers' or 'candidates'
            if isinstance(alpha12_mapping, dict):
                challengers = alpha12_mapping.get("challengers") or alpha12_mapping.get("candidates") or []
            if not isinstance(challengers, list):
                challengers = []

            records: List[Alpha12Challenger] = []
            total_score = 0.0
            total_adv = 0.0

            for item in challengers:
                if not isinstance(item, dict):
                    continue
                symbol = str(item.get("symbol") or item.get("ticker") or "").strip().upper()
                if not symbol:
                    continue
                # extract fields defensively
                ch_rank = item.get("rank")
                ch_alpha12_score = self._safe_float(item.get("alpha12_score") or item.get("score"))
                ch_quality = self._safe_float(item.get("quality_score") or item.get("quality"))
                ch_risk = self._safe_float(item.get("risk_score") or item.get("risk"))

                incumbent = item.get("incumbent") or {}
                inc_symbol = str(incumbent.get("symbol") or incumbent.get("ticker") or "").strip().upper() if isinstance(incumbent, dict) else None
                inc_alpha12_score = self._safe_float(incumbent.get("alpha12_score") or incumbent.get("score"))
                inc_quality = self._safe_float(incumbent.get("quality_score") or incumbent.get("quality"))
                inc_risk = self._safe_float(incumbent.get("risk_score") or incumbent.get("risk"))

                # compute deterministic scores
                ch_score = self._compute_candidate_score(ch_alpha12_score, ch_quality, ch_risk)
                inc_score = self._compute_candidate_score(inc_alpha12_score, inc_quality, inc_risk) if inc_alpha12_score is not None or inc_quality is not None or inc_risk is not None else None

                score_diff = None
                if ch_score is not None and inc_score is not None:
                    score_diff = round(ch_score - inc_score, 2)

                quality_diff = None
                if ch_quality is not None and inc_quality is not None:
                    quality_diff = round(ch_quality - inc_quality, 2)

                risk_diff = None
                if ch_risk is not None and inc_risk is not None:
                    risk_diff = round(inc_risk - ch_risk, 2)  # positive means challenger lower risk

                # deterioration detection: conservative rule — incumbent quality <=50 OR incumbent health D/E
                incumbent_health = None
                if isinstance(portfolio_health_result, dict):
                    incumbent_health = portfolio_health_result.get("health_status")
                else:
                    incumbent_health = getattr(portfolio_health_result, "grade", None) if portfolio_health_result is not None else None

                deterioration = False
                if inc_quality is not None and inc_quality <= 50.0:
                    deterioration = True
                if isinstance(incumbent_health, str) and incumbent_health in ("D", "F", "POOR"):
                    deterioration = True

                # material superiority rule: requires multiple dimensions
                material = False
                if score_diff is not None and quality_diff is not None and risk_diff is not None:
                    if score_diff >= 12.0 and quality_diff >= 8.0 and risk_diff >= 5.0:
                        material = True

                # classification
                if ch_score is None:
                    gov_status = INSUFFICIENT_DATA
                elif material and deterioration:
                    gov_status = STRONG_CANDIDATE
                elif material and not deterioration:
                    gov_status = REVIEW_CANDIDATE
                elif ch_score is not None and score_diff is not None and score_diff >= 5.0:
                    gov_status = MONITOR_CHALLENGER
                else:
                    gov_status = PROTECT_INCUMBENT

                rec = Alpha12Challenger(
                    symbol=symbol,
                    name=item.get("name"),
                    asset_type=item.get("asset_type"),
                    challenger_rank=ch_rank,
                    challenger_score=ch_score,
                    incumbent_symbol=inc_symbol,
                    incumbent_name=incumbent.get("name") if isinstance(incumbent, dict) else None,
                    incumbent_rank=incumbent.get("rank") if isinstance(incumbent, dict) else None,
                    incumbent_score=inc_score,
                    score_difference=score_diff,
                    quality_score=ch_quality,
                    incumbent_quality_score=inc_quality,
                    quality_difference=quality_diff,
                    current_weight=item.get("current_weight"),
                    target_weight=item.get("target_weight"),
                    sector=item.get("sector"),
                    incumbent_sector=incumbent.get("sector") if isinstance(incumbent, dict) else None,
                    sector_overlap=(item.get("sector") == (incumbent.get("sector") if isinstance(incumbent, dict) else None)),
                    risk_score=ch_risk,
                    incumbent_risk_score=inc_risk,
                    risk_difference=risk_diff,
                    portfolio_health_status=getattr(portfolio_health_result, "grade", None) if portfolio_health_result is not None else None,
                    incumbent_health_status=None,
                    deterioration_detected=deterioration,
                    material_superiority=material,
                    evaluation_status=("OK" if ch_score is not None else "INSUFFICIENT_DATA"),
                    governance_status=gov_status,
                    evidence={
                        "alpha12_score": ch_alpha12_score,
                        "incumbent_alpha12_score": inc_alpha12_score,
                        "quality_score": ch_quality,
                        "incumbent_quality_score": inc_quality,
                        "risk_score": ch_risk,
                        "incumbent_risk_score": inc_risk,
                    },
                    rationale=None,
                )

                records.append(rec)
                if rec.challenger_score is not None:
                    total_score += rec.challenger_score
                if rec.score_difference is not None:
                    total_adv += rec.score_difference

                # counters
                result.total_challengers_evaluated += 1
                if rec.incumbent_symbol:
                    result.incumbents_evaluated += 1
                if rec.governance_status == STRONG_CANDIDATE:
                    result.strong_candidates += 1
                if rec.governance_status == REVIEW_CANDIDATE:
                    result.review_candidates += 1
                if rec.governance_status == PROTECT_INCUMBENT:
                    result.protected_incumbents += 1
                if rec.governance_status == INSUFFICIENT_DATA:
                    result.insufficient_data += 1

            # finalize
            result.challenger_records = records
            if result.total_challengers_evaluated > 0:
                result.average_challenger_score = round(total_score / max(1, (sum(1 for r in records if r.challenger_score is not None))), 2) if total_score > 0 else 0.0
                result.average_score_advantage = round(total_adv / result.total_challengers_evaluated, 2)
            result.latest_evaluation_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            return result
        except Exception:
            return result
