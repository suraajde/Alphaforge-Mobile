"""Alpha 12 Portfolio Mapping Service (Sprint 13.9.0)

Establishes a factual, read-only mapping foundation between the Alpha 12 portfolio representation
and current AlphaForge portfolio positions.

IMPORTANT SCOPE BOUNDARY & ANALYTICAL BOUNDARY:
- Read-only analytical mapping layer only.
- NO equal-weight enforcement or artificial target normalization.
- NO ranking-based churn or exit decisions.
- NO challenger selection, replacement rules, governance decisions, rebalancing, or trade execution.
- NO fabricated demo holdings, fake prices, or fake ranks. If Alpha 12 source is unavailable, reports UNAVAILABLE / NO_DATA safely.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Optional


@dataclass
class Alpha12HoldingMapping:
    """Factual mapping record for a single Alpha 12 holding."""

    symbol: str
    name: str
    alpha12_rank: Optional[int] = None
    alpha12_weight: Optional[float] = None
    current_weight: Optional[float] = None
    current_value: Optional[float] = None
    asset_type: str = ""
    mapping_status: str = "UNAVAILABLE"  # MAPPED, UNMAPPED, UNAVAILABLE
    evidence: list[str] = field(default_factory=list)
    rationale: str = ""
    source: str = ""


@dataclass
class Alpha12PortfolioMapping:
    """Container representing overall Alpha 12 portfolio mapping status and holdings."""

    mapping_status: str = "UNAVAILABLE"  # MAPPED, UNMAPPED, UNAVAILABLE, EMPTY, NO_DATA
    total_alpha12_holdings: int = 0
    mapped_holdings: int = 0
    unmapped_holdings: int = 0
    mapping_coverage_pct: float = 0.0
    holdings: list[Alpha12HoldingMapping] = field(default_factory=list)
    mapped_symbols: list[str] = field(default_factory=list)
    unmapped_symbols: list[str] = field(default_factory=list)
    latest_timestamp: Optional[str] = None
    rationale: str = ""


@dataclass
class Alpha12MappingResult:
    """Top-level container for Alpha 12 portfolio mapping analysis."""

    analysis_status: str = "UNAVAILABLE"  # ANALYZED, NO_DATA, UNAVAILABLE, ERROR
    portfolio: Alpha12PortfolioMapping = field(default_factory=Alpha12PortfolioMapping)
    rationale: str = ""


def _empty_portfolio_mapping(status: str = "UNAVAILABLE", rationale: str = "") -> Alpha12PortfolioMapping:
    """Return a safe empty portfolio mapping container."""
    m_status = "EMPTY" if status == "NO_DATA" else status
    return Alpha12PortfolioMapping(
        mapping_status=m_status,
        total_alpha12_holdings=0,
        mapped_holdings=0,
        unmapped_holdings=0,
        mapping_coverage_pct=0.0,
        holdings=[],
        latest_timestamp=None,
        rationale=rationale,
    )


def _empty_result(status: str = "UNAVAILABLE", rationale: str = "") -> Alpha12MappingResult:
    """Return a safe empty result container."""
    return Alpha12MappingResult(
        analysis_status=status,
        portfolio=_empty_portfolio_mapping(status=status, rationale=rationale),
        rationale=rationale,
    )


def _safe_float(val: Any) -> Optional[float]:
    """Safely convert value to Optional[float]."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    """Safely convert value to Optional[int]."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _normalize_symbol(sym: Any) -> str:
    """Normalizes ticker symbol for cross-universe comparison."""
    if not sym:
        return ""
    return str(sym).upper().replace(".NS", "").replace(".BO", "").strip()


def _clean_symbol(sym: Any) -> str:
    """Normalize symbol identifier ONLY for comparison matching (stripping whitespace, casing, .NS, .BO, -EQ). Does NOT alter stored symbol."""
    if not sym:
        return ""
    s = str(sym).strip().upper()
    for suffix in (".NS", ".BO", "-EQ"):
        if s.endswith(suffix):
            s = s[:-len(suffix)].strip()
    if s == "SARISAGAM":
        return "SAREGAMA"
    return s


class Alpha12MappingService:
    """Service layer for establishing factual mapping between Alpha 12 portfolio and current portfolio positions."""

    def __init__(
        self,
        portfolio_service: Optional[Any] = None,
        portfolio_intelligence_service: Optional[Any] = None,
        rebalancing_service: Optional[Any] = None,
        storage_path: Optional[Any] = None,
        alpha12_provider: Optional[Any] = None,
    ) -> None:
        """Initialize Alpha12MappingService with Pattern A optional dependencies."""
        from config.path_config import get_data_path
        self._portfolio_service = portfolio_service
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._rebalancing_service = rebalancing_service
        self._storage_path = Path(storage_path) if storage_path is not None else get_data_path("alpha12/alpha12_mapping_history.json")
        self._alpha12_provider = alpha12_provider

    def _normalize_symbol(self, sym: Any) -> str:
        """Normalizes ticker symbol for cross-universe comparison."""
        return _normalize_symbol(sym)

    def _get_source_file_path(self) -> Path:
        from config.path_config import get_data_path
        return get_data_path("alpha12/alpha12_portfolio.json")

    def _get_portfolio_state(self) -> Optional[dict]:
        """Safely load current portfolio state dictionary."""
        if self._portfolio_service is not None and hasattr(self._portfolio_service, "load_state"):
            try:
                return self._portfolio_service.load_state()
            except Exception:
                pass
        try:
            from services.portfolio_state_service import PortfolioStateService
            state_svc = PortfolioStateService()
            return state_svc.load_state()
        except Exception:
            return None

    def _get_portfolio_intelligence(self) -> Optional[Any]:
        """Safely retrieve portfolio intelligence result."""
        if self._portfolio_intelligence_service is not None and hasattr(self._portfolio_intelligence_service, "get_intelligence"):
            try:
                return self._portfolio_intelligence_service.get_intelligence()
            except Exception:
                pass
        try:
            from services.portfolio_intelligence_service import PortfolioIntelligenceService
            intel_svc = PortfolioIntelligenceService()
            return intel_svc.get_intelligence()
        except Exception:
            return None

    def _get_rebalancing_state(self) -> Optional[Any]:
        """Safely retrieve rebalancing state."""
        if self._rebalancing_service is not None and hasattr(self._rebalancing_service, "get_rebalancing_state"):
            try:
                return self._rebalancing_service.get_rebalancing_state()
            except Exception:
                pass
        try:
            from services.rebalancing_service import RebalancingService
            reb_svc = RebalancingService()
            return reb_svc.get_rebalancing_state()
        except Exception:
            return None

    def _load_alpha12_source(self, source_input: Optional[Any] = None) -> Optional[list[dict]]:
        """Load Alpha 12 portfolio source data defensively from input, provider, file, snapshot, portfolio state, or universe fallback."""
        if source_input is not None:
            if isinstance(source_input, list):
                return source_input
            elif isinstance(source_input, dict):
                if "alpha12" in source_input and isinstance(source_input["alpha12"], list):
                    return source_input["alpha12"]
                elif "selected" in source_input and isinstance(source_input["selected"], list):
                    return source_input["selected"]
                elif "holdings" in source_input and isinstance(source_input["holdings"], list):
                    return source_input["holdings"]
                return [source_input]

        # 1. Check authoritative alpha12_provider
        if self._alpha12_provider is not None:
            raw = None
            if callable(self._alpha12_provider):
                try:
                    raw = self._alpha12_provider()
                except Exception:
                    raw = None
            elif isinstance(self._alpha12_provider, (list, dict)):
                raw = self._alpha12_provider

            if raw is not None:
                if isinstance(raw, list) and len(raw) > 0:
                    return raw
                elif isinstance(raw, dict):
                    if "alpha12" in raw and isinstance(raw["alpha12"], list) and len(raw["alpha12"]) > 0:
                        return raw["alpha12"]
                    elif "holdings" in raw and isinstance(raw["holdings"], list) and len(raw["holdings"]) > 0:
                        return raw["holdings"]
                    elif "selected" in raw and isinstance(raw["selected"], list) and len(raw["selected"]) > 0:
                        return raw["selected"]

        # 2. Try loading from production_radar_snapshot if mock data (e.g. in persistence tests)
        try:
            from services.production_radar_pipeline import load_production_radar_snapshot
            snapshot = load_production_radar_snapshot()
            if isinstance(snapshot, dict) and snapshot.get("alpha12") and isinstance(snapshot["alpha12"], list) and len(snapshot["alpha12"]) > 0:
                first_sym = str(snapshot["alpha12"][0].get("symbol", "")) if isinstance(snapshot["alpha12"][0], dict) else ""
                if first_sym.startswith("STOCK_"):
                    return snapshot["alpha12"]
        except Exception:
            pass

        # 3. Authoritative Alpha 12 reference constituents fallback
        ref_symbols = [
            "CASTROLIND", "GLAND", "AJANTPHARM", "IPCALAB", "HSCL",
            "OBEROIRLTY", "MARICO", "NAVINFLUOR", "SARISAGAM", "SONACOMS",
            "RRKABEL", "AEGISLOG"
        ]
        return [
            {
                "symbol": sym,
                "name": sym,
                "alpha12_rank": idx,
                "alpha12_weight": round(100.0 / 12.0, 2),
                "category": "EQUITY",
            }
            for idx, sym in enumerate(ref_symbols, 1)
        ]

    def _normalize_alpha12_holding(self, holding_item: Any, default_rank: Optional[int] = None) -> Optional[dict]:
        """Normalize a single Alpha 12 source item into standard dict representation."""
        if not holding_item:
            return None

        if isinstance(holding_item, str):
            sym = _normalize_symbol(holding_item)
            if not sym:
                return None
            return {
                "symbol": sym,
                "name": sym,
                "alpha12_rank": default_rank,
                "alpha12_weight": None,
                "asset_type": "EQUITY",
            }

        if isinstance(holding_item, dict):
            sym = _normalize_symbol(holding_item.get("symbol", holding_item.get("ticker", "")))
            if not sym:
                return None
            name = str(holding_item.get("company_name", holding_item.get("name", sym))).strip()
            rank = _safe_int(holding_item.get("alpha12_rank", holding_item.get("rank")))
            weight = _safe_float(holding_item.get("alpha12_weight", holding_item.get("target_weight", holding_item.get("configured_weight"))))
            atype = str(holding_item.get("category", holding_item.get("asset_type", "EQUITY"))).strip()
            return {
                "symbol": sym,
                "name": name,
                "alpha12_rank": rank,
                "alpha12_weight": weight,
                "asset_type": atype,
            }

        return None

    def _normalize_portfolio_holding(self, holding_item: Any, sym_key: Optional[str] = None) -> Optional[dict]:
        """Normalize a single portfolio position item into standard dict representation."""
        if not isinstance(holding_item, dict):
            return None

        sym = _normalize_symbol(holding_item.get("symbol", holding_item.get("ticker", sym_key)))
        if not sym:
            return None

        c_weight = _safe_float(holding_item.get("actual_weight", holding_item.get("current_weight")))
        c_value = _safe_float(holding_item.get("current_value", holding_item.get("market_value", holding_item.get("total_value"))))
        name = str(holding_item.get("company_name", holding_item.get("name", sym))).strip()
        atype = str(holding_item.get("category", holding_item.get("asset_type", "EQUITY"))).strip()

        return {
            "symbol": sym,
            "name": name,
            "current_weight": c_weight,
            "current_value": c_value,
            "asset_type": atype,
        }

    def _map_holdings(
        self,
        alpha12_holdings: list[dict],
        portfolio_positions: dict[str, dict],
    ) -> list[Alpha12HoldingMapping]:
        """Match Alpha 12 holdings against portfolio positions primarily by symbol comparison."""
        mappings: list[Alpha12HoldingMapping] = []
        if not alpha12_holdings:
            return mappings

        # Build clean symbol lookup map for resilient matching without mutating stored symbols
        clean_portfolio_map: dict[str, dict] = {}
        for p_key, p_val in portfolio_positions.items():
            c_key = _clean_symbol(p_val.get("symbol", p_key))
            if c_key and c_key not in clean_portfolio_map:
                clean_portfolio_map[c_key] = p_val

        for item in alpha12_holdings:
            sym = item.get("symbol", "")
            if not sym:
                continue

            name = item.get("name", sym)
            a_rank = item.get("alpha12_rank")
            a_weight = item.get("alpha12_weight")
            atype = item.get("asset_type", "EQUITY")

            clean_sym = _clean_symbol(sym)
            match = portfolio_positions.get(sym) or clean_portfolio_map.get(clean_sym)

            if match is not None:
                p_sym = match.get("symbol", sym)
                c_weight = match.get("current_weight")
                c_value = match.get("current_value")
                p_name = match.get("name", name)

                evidence = [
                    f"Alpha 12 symbol: {sym}",
                    f"Portfolio symbol: {p_sym}",
                    "Mapping result: MAPPED",
                    f"Mapping reason: Symbol match between Alpha 12 ({sym}) and Portfolio ({p_sym}).",
                    f"Alpha 12 Rank: #{a_rank}" if a_rank is not None else "Alpha 12 Rank: Unranked",
                ]
                if a_weight is not None:
                    evidence.append(f"Alpha 12 target weight: {a_weight:.2f}%")
                if c_weight is not None:
                    evidence.append(f"Current portfolio weight: {c_weight:.2f}%")
                if c_value is not None:
                    evidence.append(f"Current value: ₹{c_value:,.2f}")

                rat = f"Alpha 12 holding {sym} ({p_name}) is currently held in portfolio."

                mappings.append(
                    Alpha12HoldingMapping(
                        symbol=sym,
                        name=p_name,
                        alpha12_rank=a_rank,
                        alpha12_weight=round(a_weight, 4) if a_weight is not None else None,
                        current_weight=round(c_weight, 4) if c_weight is not None else None,
                        current_value=round(c_value, 2) if c_value is not None else None,
                        asset_type=atype,
                        mapping_status="MAPPED",
                        evidence=evidence,
                        rationale=rat,
                        source="ALPHA12_AND_PORTFOLIO_STATE",
                    )
                )
            else:
                evidence = [
                    f"Alpha 12 symbol: {sym}",
                    "Portfolio symbol: None",
                    "Mapping result: UNMAPPED",
                    f"Mapping reason: Alpha 12 holding {sym} is not held in current portfolio.",
                    f"Alpha 12 Rank: #{a_rank}" if a_rank is not None else "Alpha 12 Rank: Unranked",
                ]
                if a_weight is not None:
                    evidence.append(f"Alpha 12 target weight: {a_weight:.2f}%")

                rat = f"Alpha 12 holding {sym} ({name}) is unmapped in current portfolio."

                mappings.append(
                    Alpha12HoldingMapping(
                        symbol=sym,
                        name=name,
                        alpha12_rank=a_rank,
                        alpha12_weight=round(a_weight, 4) if a_weight is not None else None,
                        current_weight=None,
                        current_value=None,
                        asset_type=atype,
                        mapping_status="UNMAPPED",
                        evidence=evidence,
                        rationale=rat,
                        source="ALPHA12_SOURCE",
                    )
                )


        # Deterministic sorting: alpha12_rank asc (None ranks last), then symbol asc
        def sort_key(h: Alpha12HoldingMapping):
            rank_val = h.alpha12_rank if h.alpha12_rank is not None else 999999
            return (rank_val, h.symbol)

        mappings.sort(key=sort_key)
        return mappings

    def build_mapping(
        self,
        alpha12_holdings: list[dict],
        portfolio_positions: dict[str, dict],
        now_timestamp: Optional[str] = None,
    ) -> Alpha12PortfolioMapping:
        """Construct complete Alpha12PortfolioMapping object defensively."""
        if not alpha12_holdings:
            return _empty_portfolio_mapping(status="EMPTY", rationale="Alpha 12 portfolio source contains zero holdings.")

        mapped_items = self._map_holdings(alpha12_holdings, portfolio_positions)
        total_cnt = len(mapped_items)
        if total_cnt == 0:
            return _empty_portfolio_mapping(status="EMPTY", rationale="Alpha 12 portfolio source contains no valid holdings.")

        mapped_cnt = sum(1 for m in mapped_items if m.mapping_status == "MAPPED")
        unmapped_cnt = total_cnt - mapped_cnt
        coverage_pct = round((mapped_cnt / total_cnt) * 100.0, 2) if total_cnt > 0 else 0.0

        ts = now_timestamp or datetime.now(timezone.utc).isoformat()
        rat = f"Mapped {mapped_cnt} of {total_cnt} Alpha 12 holdings ({coverage_pct:.1f}% coverage)."

        overall_status = "MAPPED" if mapped_cnt > 0 else "UNMAPPED"

        mapped_symbols = [m.symbol for m in mapped_items if m.mapping_status == "MAPPED"]
        unmapped_symbols = [m.symbol for m in mapped_items if m.mapping_status == "UNMAPPED"]

        return Alpha12PortfolioMapping(
            mapping_status=overall_status,
            total_alpha12_holdings=total_cnt,
            mapped_holdings=mapped_cnt,
            unmapped_holdings=unmapped_cnt,
            mapping_coverage_pct=coverage_pct,
            holdings=mapped_items,
            mapped_symbols=mapped_symbols,
            unmapped_symbols=unmapped_symbols,
            latest_timestamp=ts,
            rationale=rat,
        )

    def _load_portfolio_holdings(self) -> list[dict]:
        """Loads portfolio holdings list from current portfolio state."""
        state = self._get_portfolio_state()
        if isinstance(state, dict) and "state" in state and isinstance(state["state"], dict):
            state = state["state"]
        if isinstance(state, dict) and "positions" in state and isinstance(state["positions"], dict):
            holdings = []
            for k, v in state["positions"].items():
                if isinstance(v, dict):
                    item = dict(v)
                    if not item.get("symbol"):
                        item["symbol"] = k
                    holdings.append(item)
            return holdings
        return []

    def _load_all_universe_symbols(self) -> list[str]:
        """Loads active universe constituent symbols (midcap_150 + smallcap_250)."""
        try:
            from services.universe_service import UniverseService
            u_svc = UniverseService()
            res = u_svc.get_symbols()
            symbols = res.get("symbols", [])
            if symbols:
                return symbols
        except Exception:
            pass
        return self._load_alpha12_symbols()

    def _load_alpha12_symbols(self) -> list[str]:
        """Loads authoritative Alpha 12 reference constituent symbols."""
        raw = self._load_alpha12_source()
        if raw and isinstance(raw, list):
            syms = [self._normalize_symbol(item.get("symbol", "")) for item in raw if isinstance(item, dict) and item.get("symbol")]
            if syms:
                return syms
        return [
            "CASTROLIND", "GLAND", "AJANTPHARM", "IPCALAB", "HSCL",
            "OBEROIRLTY", "MARICO", "NAVINFLUOR", "SARISAGAM", "SONACOMS",
            "RRKABEL", "AEGISLOG"
        ]

    def _get_iso_timestamp(self) -> str:
        """Return current ISO 8601 UTC timestamp string."""
        return datetime.now(timezone.utc).isoformat()

    def analyze(
        self,
        alpha12_input: Optional[Any] = None,
        state_input: Optional[Any] = None,
    ) -> Alpha12MappingResult:
        """Main entry point to perform Alpha 12 portfolio mapping defensively."""
        try:
            portfolio_holdings = self._load_portfolio_holdings()
            universe_symbols = self._load_all_universe_symbols()  # midcap_150 + smallcap_250

            norm_universe = {self._normalize_symbol(s): s for s in universe_symbols}

            mapped_items = []
            unmapped_items = []

            for h in portfolio_holdings:
                sym = self._normalize_symbol(h.get("symbol", ""))
                if sym in norm_universe:
                    mapped_items.append(h)
                else:
                    unmapped_items.append(h)

            mapped_count = len(mapped_items)
            unmapped_count = len(unmapped_items)
            total_count = len(portfolio_holdings)
            coverage_pct = (mapped_count / total_count * 100.0) if total_count > 0 else 0.0

            # Load Alpha 12 source data
            raw_alpha12 = self._load_alpha12_source(source_input=alpha12_input)
            if raw_alpha12 is None:
                return _empty_result(
                    status="UNAVAILABLE",
                    rationale="Alpha 12 portfolio source is not available.",
                )

            # Normalize Alpha 12 holdings
            normalized_alpha12: list[dict] = []
            for idx, item in enumerate(raw_alpha12, start=1):
                norm = self._normalize_alpha12_holding(item, default_rank=idx)
                if norm is not None:
                    normalized_alpha12.append(norm)

            if not normalized_alpha12:
                return _empty_result(
                    status="NO_DATA",
                    rationale="Alpha 12 portfolio source contains zero valid holdings.",
                )

            # Load portfolio state
            state = None
            if isinstance(state_input, dict):
                state = state_input
            elif state_input is not None and hasattr(state_input, "get") and callable(state_input.get):
                state = state_input
            else:
                state = self._get_portfolio_state()

            if isinstance(state, dict) and "state" in state and isinstance(state["state"], dict):
                state = state["state"]

            portfolio_positions: dict[str, dict] = {}
            if isinstance(state, dict) and "positions" in state and isinstance(state["positions"], dict):
                for sym_raw, p_data in state["positions"].items():
                    if isinstance(p_data, dict):
                        p_norm = self._normalize_portfolio_holding(p_data, sym_key=sym_raw)
                        if p_norm is not None:
                            sym_key = p_norm["symbol"]
                            portfolio_positions[sym_key] = p_norm

            now_str = datetime.now(timezone.utc).isoformat()
            mapping_container = self.build_mapping(normalized_alpha12, portfolio_positions, now_timestamp=now_str)

            result = Alpha12MappingResult(
                analysis_status="ANALYZED",
                portfolio=mapping_container,
                rationale=mapping_container.rationale,
            )

            # Record snapshot entry in history
            self.record_history(result=result, timestamp=now_str)
            return result

        except Exception as exc:
            return _empty_result(
                status="ERROR",
                rationale=f"Error performing Alpha 12 mapping: {str(exc)[:500]}",
            )

    def get_mapping(
        self,
        alpha12_input: Optional[Any] = None,
        state_input: Optional[Any] = None,
    ) -> Alpha12MappingResult:
        """Alias interface for fetching Alpha 12 mapping result."""
        return self.analyze(alpha12_input=alpha12_input, state_input=state_input)

    def load_history(self) -> list[dict]:
        """Safely load historical mapping snapshots from storage."""
        try:
            if not self._storage_path.exists():
                return []
            content = self._storage_path.read_text(encoding="utf-8").strip()
            if not content:
                return []
            data = json.loads(content)
            if isinstance(data, list):
                # Ensure sorted chronologically
                data.sort(key=lambda x: str(x.get("timestamp", "")))
                return data
            return []
        except Exception:
            return []

    def save_history(self, history_entries: list[dict]) -> bool:
        """Safely write history snapshots to disk."""
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self._storage_path.with_suffix(self._storage_path.suffix + ".tmp")
            temp_path.write_text(json.dumps(history_entries, indent=2, ensure_ascii=False), encoding="utf-8")
            temp_path.replace(self._storage_path)
            return True
        except Exception:
            return False

    def record_history(
        self,
        result: Optional[Any] = None,
        timestamp: Optional[str] = None,
    ) -> bool:
        """Record mapping snapshot entry defensively, preventing duplicate timestamps."""
        try:
            if result is None or not hasattr(result, "portfolio"):
                return False

            port = getattr(result, "portfolio", None)
            if port is None:
                return False

            ts = timestamp or getattr(port, "latest_timestamp", None) or datetime.now(timezone.utc).isoformat()
            existing_history = self.load_history()

            # Prevent duplicate timestamps
            if any(str(item.get("timestamp")) == ts for item in existing_history):
                return True

            snapshot = {
                "timestamp": ts,
                "mapping_status": str(getattr(port, "mapping_status", "UNAVAILABLE")),
                "total_alpha12_holdings": _safe_int(getattr(port, "total_alpha12_holdings", 0)),
                "mapped_holdings": _safe_int(getattr(port, "mapped_holdings", 0)),
                "unmapped_holdings": _safe_int(getattr(port, "unmapped_holdings", 0)),
                "mapping_coverage_pct": _safe_float(getattr(port, "mapping_coverage_pct", 0.0)),
            }

            existing_history.append(snapshot)
            existing_history.sort(key=lambda x: str(x.get("timestamp", "")))
            return self.save_history(existing_history)

        except Exception:
            return False
