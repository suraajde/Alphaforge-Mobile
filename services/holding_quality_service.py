"""Holding Quality Engine Service (Sprint 13.8.1)

Provides a structured, factual quality assessment layer for portfolio holdings (Mutual Funds and ETFs).
Calculates transparent and deterministic quality scores only when real, measurable evidence exists.

IMPORTANT SCOPE BOUNDARY:
This service ONLY performs factual holding quality assessment.
It does NOT perform SIP optimization, opportunity scoring, portfolio risk scoring, Alpha 12 selection,
challenger identification, replacement decisions, buy/sell/hold recommendations, trade execution,
or broker integration. A quality score does NOT automatically imply that a holding should be sold or replaced.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class HoldingQuality:
    """Factual identity and quality assessment information for a single holding."""

    symbol: str
    name: str
    asset_type: str
    quality_score: float = 0.0
    quality_grade: str = "N/A"
    assessment_status: str = "UNAVAILABLE"  # e.g., "ASSESSED", "UNAVAILABLE", "UNSUPPORTED"
    rationale: str = ""
    evidence: list[str] = field(default_factory=list)


@dataclass
class HoldingQualityResult:
    """Container for holding quality assessment results across a portfolio."""

    total_holdings: int = 0
    assessed_holdings: int = 0
    unassessed_holdings: int = 0
    average_quality_score: float = 0.0
    highest_quality_score: float = 0.0
    lowest_quality_score: float = 0.0
    holdings: list[HoldingQuality] = field(default_factory=list)


def _empty_result() -> HoldingQualityResult:
    """Return a safe empty HoldingQualityResult."""
    return HoldingQualityResult(
        total_holdings=0,
        assessed_holdings=0,
        unassessed_holdings=0,
        average_quality_score=0.0,
        highest_quality_score=0.0,
        lowest_quality_score=0.0,
        holdings=[],
    )


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


class HoldingQualityService:
    """Service layer for computing factual holding quality assessments."""

    FUND_TYPES = {"FUND", "MUTUAL_FUND", "MUTUAL FUND", "INDEX_FUND"}
    ETF_TYPES = {"ETF", "EXCHANGE_TRADED_FUND", "EXCHANGE TRADED FUND"}

    def __init__(
        self,
        portfolio_intelligence_service: Optional[Any] = None,
        portfolio_service: Optional[Any] = None,
        rebalancing_service: Optional[Any] = None,
    ) -> None:
        """Initialize HoldingQualityService with optional dependencies."""
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._portfolio_service = portfolio_service
        self._rebalancing_service = rebalancing_service

    def _get_rebalancing_service(self) -> Optional[Any]:
        """Safely retrieve or instantiate the RebalancingService."""
        if self._rebalancing_service is not None:
            return self._rebalancing_service
        try:
            from services.rebalancing_service import RebalancingService

            return RebalancingService()
        except Exception:
            return None

    def _get_portfolio_service(self) -> Optional[Any]:
        """Safely retrieve or instantiate the PortfolioApplicationService."""
        if self._portfolio_service is not None:
            return self._portfolio_service
        try:
            from services.portfolio_application_service import PortfolioApplicationService

            return PortfolioApplicationService()
        except Exception:
            return None

    def _extract_field(self, obj: Any, field_name: str, default: Any = None) -> Any:
        """Helper to extract a field from dict or object safely."""
        if isinstance(obj, dict):
            return obj.get(field_name, default)
        return getattr(obj, field_name, default)

    def assess_fund_holding(self, holding_data: Any) -> HoldingQuality:
        """Provide a fund-specific descriptive assessment path."""
        try:
            sym = str(self._extract_field(holding_data, "symbol", "") or self._extract_field(holding_data, "ticker", "") or "").strip()
            nm = str(self._extract_field(holding_data, "name", "") or sym).strip()
            atype = str(self._extract_field(holding_data, "asset_type", "") or self._extract_field(holding_data, "type", "MUTUAL_FUND")).strip().upper()

            # Extract potential metadata metrics if available
            expense_ratio = self._extract_field(holding_data, "expense_ratio", None)
            category = self._extract_field(holding_data, "category", None)
            performance = self._extract_field(holding_data, "performance", None)
            consistency = self._extract_field(holding_data, "consistency", None)
            rating = self._extract_field(holding_data, "rating", None)

            evidence: list[str] = []
            score_points = 0
            has_valid_metrics = False

            if expense_ratio is not None:
                er = _safe_float(expense_ratio, -1.0)
                if er >= 0.0:
                    has_valid_metrics = True
                    if er < 0.5:
                        score_points += 40
                        evidence.append(f"Low expense ratio ({er:.2f}%)")
                    elif er < 1.0:
                        score_points += 25
                        evidence.append(f"Moderate expense ratio ({er:.2f}%)")
                    else:
                        score_points += 10
                        evidence.append(f"High expense ratio ({er:.2f}%)")

            if category is not None and str(category).strip():
                has_valid_metrics = True
                score_points += 30
                evidence.append(f"Category identified ({category})")

            if performance is not None or consistency is not None or rating is not None:
                has_valid_metrics = True
                score_points += 30
                if performance is not None:
                    evidence.append(f"Performance data present ({performance})")
                if consistency is not None:
                    evidence.append(f"Consistency data present ({consistency})")

            if not has_valid_metrics:
                return HoldingQuality(
                    symbol=sym,
                    name=nm,
                    asset_type=atype,
                    quality_score=0.0,
                    quality_grade="N/A",
                    assessment_status="UNAVAILABLE",
                    rationale="Insufficient fund metadata available for quality assessment.",
                    evidence=[],
                )

            final_score = float(min(100, max(0, score_points)))
            if final_score >= 80:
                grade = "A"
            elif final_score >= 70:
                grade = "B"
            elif final_score >= 60:
                grade = "C"
            else:
                grade = "D"

            rationale_str = f"Assessed fund based on available metrics: {', '.join(evidence)}."

            return HoldingQuality(
                symbol=sym,
                name=nm,
                asset_type=atype,
                quality_score=final_score,
                quality_grade=grade,
                assessment_status="ASSESSED",
                rationale=rationale_str,
                evidence=evidence,
            )
        except Exception:
            return HoldingQuality(
                symbol="UNKNOWN",
                name="UNKNOWN",
                asset_type="MUTUAL_FUND",
                quality_score=0.0,
                quality_grade="N/A",
                assessment_status="UNAVAILABLE",
                rationale="Error occurred during fund quality assessment.",
                evidence=[],
            )

    def assess_etf_holding(self, holding_data: Any) -> HoldingQuality:
        """Provide an ETF-specific descriptive assessment path."""
        try:
            sym = str(self._extract_field(holding_data, "symbol", "") or self._extract_field(holding_data, "ticker", "") or "").strip()
            nm = str(self._extract_field(holding_data, "name", "") or sym).strip()
            atype = str(self._extract_field(holding_data, "asset_type", "") or self._extract_field(holding_data, "type", "ETF")).strip().upper()

            # Extract potential metadata metrics if available
            expense_ratio = self._extract_field(holding_data, "expense_ratio", None)
            category = self._extract_field(holding_data, "category", None)
            index_name = self._extract_field(holding_data, "index_name", None)
            tracking_error = self._extract_field(holding_data, "tracking_error", None)
            performance = self._extract_field(holding_data, "performance", None)

            evidence: list[str] = []
            score_points = 0
            has_valid_metrics = False

            if expense_ratio is not None:
                er = _safe_float(expense_ratio, -1.0)
                if er >= 0.0:
                    has_valid_metrics = True
                    if er < 0.2:
                        score_points += 40
                        evidence.append(f"Low ETF expense ratio ({er:.2f}%)")
                    elif er < 0.5:
                        score_points += 25
                        evidence.append(f"Moderate ETF expense ratio ({er:.2f}%)")
                    else:
                        score_points += 10
                        evidence.append(f"High ETF expense ratio ({er:.2f}%)")

            if (category is not None and str(category).strip()) or (index_name is not None and str(index_name).strip()):
                has_valid_metrics = True
                score_points += 30
                idx_str = index_name or category
                evidence.append(f"Index/Category tracking identified ({idx_str})")

            if tracking_error is not None or performance is not None:
                has_valid_metrics = True
                score_points += 30
                if tracking_error is not None:
                    evidence.append(f"Tracking error metric present ({tracking_error})")
                if performance is not None:
                    evidence.append(f"Performance metric present ({performance})")

            if not has_valid_metrics:
                return HoldingQuality(
                    symbol=sym,
                    name=nm,
                    asset_type=atype,
                    quality_score=0.0,
                    quality_grade="N/A",
                    assessment_status="UNAVAILABLE",
                    rationale="Insufficient ETF metadata available for quality assessment.",
                    evidence=[],
                )

            final_score = float(min(100, max(0, score_points)))
            if final_score >= 80:
                grade = "A"
            elif final_score >= 70:
                grade = "B"
            elif final_score >= 60:
                grade = "C"
            else:
                grade = "D"

            rationale_str = f"Assessed ETF based on available metrics: {', '.join(evidence)}."

            return HoldingQuality(
                symbol=sym,
                name=nm,
                asset_type=atype,
                quality_score=final_score,
                quality_grade=grade,
                assessment_status="ASSESSED",
                rationale=rationale_str,
                evidence=evidence,
            )
        except Exception:
            return HoldingQuality(
                symbol="UNKNOWN",
                name="UNKNOWN",
                asset_type="ETF",
                quality_score=0.0,
                quality_grade="N/A",
                assessment_status="UNAVAILABLE",
                rationale="Error occurred during ETF quality assessment.",
                evidence=[],
            )

    def assess_equity_holding(self, holding_data: Any) -> HoldingQuality:
        """Provide an equity-specific descriptive assessment path using factual fundamental metrics/scores."""
        try:
            sym = str(self._extract_field(holding_data, "symbol", "") or self._extract_field(holding_data, "ticker", "") or "").strip().upper()
            nm = str(self._extract_field(holding_data, "company_name", "") or self._extract_field(holding_data, "name", "") or sym).strip()
            raw_atype = str(self._extract_field(holding_data, "asset_type", "") or self._extract_field(holding_data, "category", "EQUITY")).strip().upper()
            atype = raw_atype if raw_atype and raw_atype not in ("UNKNOWN", "") else "EQUITY"

            evidence: list[str] = []
            score_points = 0.0
            has_valid_metrics = False

            # Priority 1: Check direct quality / fundamental score or conviction carried on holding_data
            for score_field in ("quality_score", "fundamental_score", "score", "alpha12_selection_score", "base_score", "conviction"):
                score_val = self._extract_field(holding_data, score_field, None)
                if score_val is not None:
                    s_float = _safe_float(score_val, -1.0)
                    if s_float >= 0.0:
                        has_valid_metrics = True
                        score_points = s_float
                        field_name_pretty = score_field.replace("_", " ").title()
                        evidence.append(f"{field_name_pretty}: {s_float:.1f}")
                        break

            # Priority 2: Use existing fundamental score service if explicit score was not present
            if not has_valid_metrics and isinstance(holding_data, dict):
                try:
                    from services.fundamental_score_service import calculate_fundamental_score
                    fs_res = calculate_fundamental_score(holding_data)
                    if isinstance(fs_res, dict) and fs_res.get("fundamental_score") is not None:
                        f_score = _safe_float(fs_res.get("fundamental_score"), -1.0)
                        if f_score >= 0.0:
                            has_valid_metrics = True
                            score_points = f_score
                            evidence.append(f"Fundamental Score: {f_score:.1f}")
                except Exception:
                    pass

            # Priority 3: Insufficient valid metrics -> Return UNAVAILABLE and N/A
            if not has_valid_metrics:
                return HoldingQuality(
                    symbol=sym,
                    name=nm,
                    asset_type=atype,
                    quality_score=0.0,
                    quality_grade="N/A",
                    assessment_status="UNAVAILABLE",
                    rationale="Insufficient fundamental metadata or Alpha 12 conviction score available for equity quality assessment.",
                    evidence=[],
                )

            final_score = float(min(100.0, max(0.0, score_points)))
            if final_score >= 80.0:
                grade = "A"
            elif final_score >= 70.0:
                grade = "B"
            elif final_score >= 60.0:
                grade = "C"
            else:
                grade = "D"

            rationale_str = f"Assessed equity holding based on available fundamental metrics: {', '.join(evidence)}."

            return HoldingQuality(
                symbol=sym,
                name=nm,
                asset_type=atype,
                quality_score=round(final_score, 1),
                quality_grade=grade,
                assessment_status="ASSESSED",
                rationale=rationale_str,
                evidence=evidence,
            )
        except Exception:
            return HoldingQuality(
                symbol="UNKNOWN",
                name="UNKNOWN",
                asset_type="EQUITY",
                quality_score=0.0,
                quality_grade="N/A",
                assessment_status="UNAVAILABLE",
                rationale="Error occurred during equity quality assessment.",
                evidence=[],
            )

    def assess_single_holding(self, holding_data: Any) -> HoldingQuality:
        """Assess a single holding record based on its asset type and available metadata."""
        if holding_data is None or isinstance(holding_data, (int, float, str, bool)):
            return HoldingQuality(
                symbol="N/A",
                name="Invalid Holding",
                asset_type="UNKNOWN",
                quality_score=0.0,
                quality_grade="N/A",
                assessment_status="UNAVAILABLE",
                rationale="Malformed or invalid holding input.",
            )

        try:
            sym = str(self._extract_field(holding_data, "symbol", "") or self._extract_field(holding_data, "ticker", "") or "").strip()
            nm = str(self._extract_field(holding_data, "name", "") or sym or "Unnamed Holding").strip()
            atype = str(self._extract_field(holding_data, "asset_type", "") or self._extract_field(holding_data, "type", "EQUITY")).strip().upper()

            if not sym and not nm:
                return HoldingQuality(
                    symbol="N/A",
                    name="Unnamed Holding",
                    asset_type=atype,
                    quality_score=0.0,
                    quality_grade="N/A",
                    assessment_status="UNAVAILABLE",
                    rationale="Missing symbol and name identification.",
                )

            if atype in self.FUND_TYPES or "FUND" in atype:
                return self.assess_fund_holding(holding_data)
            elif atype in self.ETF_TYPES or "ETF" in atype:
                return self.assess_etf_holding(holding_data)
            elif atype in ("EQUITY", "STOCK", "EQUITIES") or not atype:
                return self.assess_equity_holding(holding_data)
            else:
                return HoldingQuality(
                    symbol=sym,
                    name=nm,
                    asset_type=atype,
                    quality_score=0.0,
                    quality_grade="N/A",
                    assessment_status="UNSUPPORTED",
                    rationale=f"Unsupported asset type '{atype}' for quality assessment.",
                    evidence=[],
                )
        except Exception:
            return HoldingQuality(
                symbol="UNKNOWN",
                name="UNKNOWN",
                asset_type="UNKNOWN",
                quality_score=0.0,
                quality_grade="N/A",
                assessment_status="UNAVAILABLE",
                rationale="Error occurred while processing holding record.",
            )

    def build_summary(self, holdings: list[HoldingQuality]) -> HoldingQualityResult:
        """Compute summary metrics container from assessed holdings list."""
        try:
            if not isinstance(holdings, list) or not holdings:
                return _empty_result()

            total_count = len(holdings)
            assessed = [h for h in holdings if isinstance(h, HoldingQuality) and h.assessment_status == "ASSESSED"]
            assessed_count = len(assessed)
            unassessed_count = total_count - assessed_count

            if assessed_count > 0:
                scores = [h.quality_score for h in assessed]
                avg_score = round(sum(scores) / float(assessed_count), 2)
                max_score = round(max(scores), 2)
                min_score = round(min(scores), 2)
            else:
                avg_score = 0.0
                max_score = 0.0
                min_score = 0.0

            return HoldingQualityResult(
                total_holdings=total_count,
                assessed_holdings=assessed_count,
                unassessed_holdings=unassessed_count,
                average_quality_score=avg_score,
                highest_quality_score=max_score,
                lowest_quality_score=min_score,
                holdings=holdings,
            )
        except Exception:
            return _empty_result()

    def assess_holdings(self, holdings_input: Optional[Any] = None) -> HoldingQualityResult:
        """Assess all portfolio holdings safely and return HoldingQualityResult."""
        try:
            raw_positions: list[Any] = []

            if holdings_input is not None:
                if isinstance(holdings_input, list):
                    raw_positions = holdings_input
                elif isinstance(holdings_input, dict):
                    if "positions" in holdings_input and isinstance(holdings_input["positions"], list):
                        raw_positions = holdings_input["positions"]
                    elif "holdings" in holdings_input and isinstance(holdings_input["holdings"], list):
                        raw_positions = holdings_input["holdings"]
                    else:
                        raw_positions = list(holdings_input.values())
                elif hasattr(holdings_input, "positions") and isinstance(getattr(holdings_input, "positions"), list):
                    raw_positions = getattr(holdings_input, "positions")
                elif hasattr(holdings_input, "portfolio") and hasattr(getattr(holdings_input, "portfolio"), "positions"):
                    raw_positions = getattr(getattr(holdings_input, "portfolio"), "positions", [])

            if not raw_positions:
                # Fallback to RebalancingService if available
                r_svc = self._get_rebalancing_service()
                if r_svc is not None and hasattr(r_svc, "get_state"):
                    st = r_svc.get_state()
                    if st is not None and hasattr(st, "portfolio") and st.portfolio is not None:
                        raw_positions = getattr(st.portfolio, "positions", [])

            if not raw_positions:
                # Fallback to PortfolioApplicationService if available
                p_svc = self._get_portfolio_service()
                if p_svc is not None and hasattr(p_svc, "get_status"):
                    res = p_svc.get_status()
                    if isinstance(res, dict) and res.get("status") == "OK":
                        st = res.get("state")
                        if isinstance(st, dict) and "positions" in st:
                            pos_dict = st["positions"]
                            if isinstance(pos_dict, dict):
                                raw_positions = list(pos_dict.values())
                            elif isinstance(pos_dict, list):
                                raw_positions = pos_dict

            if not raw_positions or not isinstance(raw_positions, list):
                return _empty_result()

            assessed_holdings: list[HoldingQuality] = []
            for item in raw_positions:
                hq = self.assess_single_holding(item)
                assessed_holdings.append(hq)

            return self.build_summary(assessed_holdings)
        except Exception:
            return _empty_result()

    def get_quality(self, holdings_input: Optional[Any] = None) -> HoldingQualityResult:
        """Alias interface method for assess_holdings."""
        return self.assess_holdings(holdings_input)
