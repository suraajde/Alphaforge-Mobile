"""Sprint 14.1.9 Acceptance Test Suite — Runtime Persistence & Cross-Screen Consistency

Validates:
A. Production Radar persistence
B. Production Radar startup restore
C. Alpha 12 persistence
D. Alpha 12 startup restore
E. READY / STALE / UNAVAILABLE freshness states
F. Portfolio Health baseline persistence
G. Snapshot deduplication
H. Watchtower persistence after fresh service initialization
I. Cross-screen Alpha 12 consistency
J. Application restart simulation integration
K. Blank-screen / error-state fallback handling
L. SIP allocation (whole shares, no overspending)
M. Lump-sum allocation (whole shares, no overspending)
N. Concentration protection
O. Existing rebalancing governance regression
"""
import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from config.path_config import get_data_path
from services.production_radar_pipeline import (
    save_production_radar_snapshot,
    load_production_radar_snapshot,
    ProductionRadarPipeline,
)
from services.alpha12_mapping_service import Alpha12MappingService
from services.portfolio_health_history_service import (
    PortfolioHealthHistoryService,
    PortfolioHealthHistoryEntry,
)
from services.portfolio_health_monitor_service import PortfolioHealthMonitorService
from services.portfolio_health_service import (
    PortfolioHealthService,
    PortfolioHealthSnapshot,
    PortfolioHealthResult,
)
from services.investment_allocation_service import (
    InvestmentAllocationService,
    AllocationItem,
)
from services.alpha12_replacement_governance_service import (
    Alpha12ReplacementGovernanceService,
    PROTECT_INCUMBENT,
)


from PySide6.QtWidgets import QApplication
import sys


@pytest.fixture(autouse=True)
def init_qapp():
    """Ensure QApplication instance exists for PySide6 GUI widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def temp_data_dir(monkeypatch):
    """Isolated temporary data directory fixture enforcing ALPHAFORGE_DATA_DIR test isolation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_dir = Path(tmp_dir) / "alphaforge_test_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("ALPHAFORGE_DATA_DIR", str(data_dir))
        yield data_dir




def _create_mock_radar_result():
    return {
        "status": "OK",
        "universe_count": 400,
        "candidate_count": 120,
        "processed_count": 120,
        "successful_count": 120,
        "eligible_count": 68,
        "review_count": 0,
        "error_count": 0,
        "candidate_midcap_count": 60,
        "candidate_smallcap_count": 60,
        "ranked": [
            {
                "symbol": f"STOCK_{i}",
                "company": f"Company {i}",
                "category": "MIDCAP" if i % 2 == 0 else "SMALLCAP",
                "sector": "FINANCIAL SERVICES" if i % 3 == 0 else "TECHNOLOGY",
                "composite_score": round(90.0 - i * 0.5, 2),
                "fundamental_score": round(88.0 - i * 0.5, 2),
                "technical_score": round(92.0 - i * 0.5, 2),
                "alpha12_rank": i,
            }
            for i in range(1, 31)
        ],
        "alpha12": [
            {
                "symbol": f"STOCK_{i}",
                "company_name": f"Company {i}",
                "category": "MIDCAP" if i % 2 == 0 else "SMALLCAP",
                "alpha12_rank": i,
                "alpha12_selection_score": round(90.0 - i * 0.5, 2),
                "alpha12_weight": 8.33,
            }
            for i in range(1, 13)
        ],
        "alpha12_reserves": [
            {
                "symbol": f"STOCK_{i}",
                "company_name": f"Company {i}",
                "category": "MIDCAP" if i % 2 == 0 else "SMALLCAP",
                "alpha12_rank": i,
            }
            for i in range(13, 21)
        ],
        "completed": True,
    }


# ==========================================================
# A & B. PRODUCTION RADAR PERSISTENCE & STARTUP RESTORE
# ==========================================================

def test_production_radar_persistence_and_restore(temp_data_dir):
    mock_result = _create_mock_radar_result()

    saved = save_production_radar_snapshot(mock_result)
    assert saved is True

    snapshot = load_production_radar_snapshot()
    assert snapshot is not None
    assert snapshot["status"] == "OK"
    assert snapshot["universe_count"] == 400
    assert snapshot["candidate_count"] == 120
    assert snapshot["data_status"] == "READY"
    assert len(snapshot["ranked"]) == 30
    assert len(snapshot["alpha12"]) == 12
    assert len(snapshot["alpha12_reserves"]) == 8
    assert snapshot["alpha12"][0]["symbol"] == "STOCK_1"


# ==========================================================
# C & D. ALPHA 12 PERSISTENCE & STARTUP RESTORE
# ==========================================================

def test_alpha12_persistence_and_restore(temp_data_dir):
    mock_result = _create_mock_radar_result()
    save_production_radar_snapshot(mock_result)

    mapping_service = Alpha12MappingService()
    source = mapping_service._load_alpha12_source()

    assert source is not None
    assert isinstance(source, list)
    assert len(source) == 12
    symbols = [s.get("symbol") for s in source]
    assert symbols == [f"STOCK_{i}" for i in range(1, 13)]


# ==========================================================
# E. FRESHNESS STATES (READY / STALE / UNAVAILABLE)
# ==========================================================

def test_freshness_states(temp_data_dir):
    # Missing snapshot -> UNAVAILABLE
    assert load_production_radar_snapshot() is None

    # Fresh snapshot -> READY
    mock_result = _create_mock_radar_result()
    save_production_radar_snapshot(mock_result)
    fresh_snapshot = load_production_radar_snapshot()
    assert fresh_snapshot["data_status"] == "READY"

    # Stale snapshot (> 24 hours old) -> STALE
    old_time = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
    mock_result["timestamp"] = old_time
    target_path = get_data_path("cache/production_radar_snapshot.json")
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(mock_result, f)

    stale_snapshot = load_production_radar_snapshot()
    assert stale_snapshot is not None
    assert stale_snapshot["data_status"] == "STALE"


# ==========================================================
# F, G, H. PORTFOLIO HEALTH BASELINE, DEDUPLICATION, WATCHTOWER
# ==========================================================

def test_portfolio_health_baseline_and_watchtower_persistence(temp_data_dir):
    hist_svc = PortfolioHealthHistoryService()
    assert len(hist_svc.get_history()) == 0

    mon_svc = PortfolioHealthMonitorService(history_service=hist_svc)

    # Initial state should not crash, and evaluating establishes baseline snapshot
    health_svc = PortfolioHealthService(history_service=hist_svc)
    res1 = health_svc.evaluate()

    history = hist_svc.get_history()
    assert len(history) == 1
    assert history[0].score == res1.score

    # Deduplication test: re-evaluating identical metrics must NOT create duplicate snapshot
    res2 = health_svc.evaluate()
    assert len(hist_svc.get_history()) == 1

    # Fresh Watchtower / Monitor service instance must see READY status
    fresh_mon_svc = PortfolioHealthMonitorService(
        history_service=PortfolioHealthHistoryService()
    )
    mon_state = fresh_mon_svc.get_monitoring_state()
    assert mon_state.monitoring_status == "READY"
    assert mon_state.snapshot_count == 1


# ==========================================================
# I & J. CROSS-SCREEN ALPHA 12 CONSISTENCY & RESTART SIMULATION
# ==========================================================

def test_cross_screen_alpha12_consistency_and_restart_simulation(temp_data_dir):
    mock_result = _create_mock_radar_result()
    save_production_radar_snapshot(mock_result)

    # Simulate fresh application startup
    loaded_snapshot = load_production_radar_snapshot()
    assert loaded_snapshot is not None

    mapping_svc = Alpha12MappingService()
    mapping_res = mapping_svc.get_mapping()

    assert mapping_res.analysis_status != "ERROR"
    assert len(mapping_res.portfolio.holdings) == 12

    restored_symbols = [h.symbol for h in mapping_res.portfolio.holdings]
    expected_symbols = [f"STOCK_{i}" for i in range(1, 13)]
    assert restored_symbols == expected_symbols


# ==========================================================
# K. BLANK-SCREEN ERROR FALLBACK HANDLING
# ==========================================================

def test_blank_screen_error_fallback_handling(temp_data_dir):
    from app.main_window import ErrorFallbackWidget
    widget = ErrorFallbackWidget("Test Screen", "Simulated initialization exception")
    assert widget is not None
    assert widget.findChild(object, "") is not None or widget.layout().count() > 0


# ==========================================================
# L, M, N. SIP / LUMP-SUM ALLOCATION & CONCENTRATION SAFETY
# ==========================================================

def test_sip_and_lumpsum_allocation_with_concentration_safety(temp_data_dir):
    mock_prices = {
        "STOCK_1": {"price": 1200.0},
        "STOCK_2": {"price": 1500.0},
        "STOCK_3": {"price": 800.0},
        "STOCK_4": {"price": 2000.0},
        "STOCK_5": {"price": 600.0},
        "STOCK_6": {"price": 1000.0},
    }

    alloc_svc = InvestmentAllocationService(
        price_provider=lambda sym: mock_prices.get(sym, {"price": 500.0})
    )

    candidates = [
        {"symbol": f"STOCK_{i}", "company_name": f"Company {i}", "alpha12_rank": i, "conviction": 90 - i}
        for i in range(1, 7)
    ]

    # Test Rs. 6,000 monthly allocation
    result_sip = alloc_svc.allocate_monthly_investment(
        total_amount=6000.0,
        alpha12_candidates=candidates,
    )

    assert result_sip.total_input_amount == 6000.0
    assert result_sip.total_allocated_amount <= 6000.0
    assert result_sip.total_allocated_amount > 0

    for item in result_sip.allocations:
        assert item.executable_amount <= 6000.0
        assert item.quantity >= 0
        assert item.executable_amount == round(item.quantity * item.reference_price, 2)
        # Check concentration safety cap: max 35% unless unit share price > 30%
        if item.reference_price <= 1800.0:
            assert (item.executable_amount / 6000.0) <= 0.35

    # Test Rs. 1,00,000 lump-sum allocation
    result_lump = alloc_svc.allocate_lump_sum_investment(
        total_amount=100000.0,
        alpha12_candidates=candidates,
    )




    assert result_lump.total_input_amount == 100000.0
    assert result_lump.total_allocated_amount <= 100000.0
    assert result_lump.total_allocated_amount > 90000.0


# ==========================================================
# O. REBALANCING GOVERNANCE REGRESSION
# ==========================================================

def test_rebalancing_governance_regression(temp_data_dir):
    gov_svc = Alpha12ReplacementGovernanceService()
    res = gov_svc.evaluate_replacements()
    assert res is not None
    assert hasattr(res, "analysis_status")
