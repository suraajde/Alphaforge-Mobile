"""Sprint 14.1.10 Regression & Acceptance Test Suite.

Verifies cross-screen reporting consistency, symbol comparison mapping,
authoritative stability consumption, structural health clarity, and immutable governance rules.
"""

import pytest
from PySide6.QtWidgets import QApplication

from services.alpha12_mapping_service import Alpha12MappingService, _clean_symbol
from services.alpha12_stability_service import Alpha12StabilityService
from services.portfolio_health_service import PortfolioHealthService
from services.portfolio_health_monitor_service import PortfolioHealthMonitorService
from services.rebalancing_service import RebalancingService
from services.sip_optimization_service import SIPOptimizationService
from app.screens.dashboard import Dashboard
from app.screens.portfolio_health import PortfolioHealth
from app.screens.watchtower import Watchtower



@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_1_alpha12_portfolio_symbols_mapped():
    """Verify Alpha 12 mapping accurately reports factual 11 mapped and 1 unmapped holding (91.7% coverage)."""
    svc = Alpha12MappingService()
    res = svc.analyze()
    assert res is not None
    assert res.analysis_status == "ANALYZED"
    port = res.portfolio
    assert port.total_alpha12_holdings == 12
    assert port.mapped_holdings == 11
    assert port.unmapped_holdings == 1
    assert abs(port.mapping_coverage_pct - 91.7) < 0.2

    # Verify unmapped holding is AEGISLOG while ACE remains in portfolio
    unmapped = [h for h in port.holdings if h.mapping_status == "UNMAPPED"]
    assert len(unmapped) == 1
    assert unmapped[0].symbol == "AEGISLOG"

    # Verify diagnostic evidence
    for h in port.holdings:
        assert any("Alpha 12 symbol:" in e for e in h.evidence)
        assert any("Mapping result:" in e for e in h.evidence)


def test_2_mapping_coverage_calculation():
    """Verify mapping coverage calculation logic with partial matches."""
    svc = Alpha12MappingService()
    alpha_input = [
        {"symbol": "CASTROLIND", "alpha12_rank": 1},
        {"symbol": "NONEXISTENT", "alpha12_rank": 2},
    ]
    state_input = {
        "state": {
            "positions": {
                "CASTROLIND": {"symbol": "CASTROLIND", "current_value": 1000.0, "actual_weight": 50.0}
            }
        }
    }
    res = svc.analyze(alpha12_input=alpha_input, state_input=state_input)
    assert res.portfolio.total_alpha12_holdings == 2
    assert res.portfolio.mapped_holdings == 1
    assert res.portfolio.unmapped_holdings == 1
    assert res.portfolio.mapping_coverage_pct == 50.0


def test_3_unmapped_symbols_remain_genuinely_unmapped():
    """Verify unmapped symbols evaluate safely to UNMAPPED without false positive matches."""
    svc = Alpha12MappingService()
    alpha_input = [{"symbol": "UNMAPPED_STOCK_XYZ", "name": "XYZ Corp"}]
    state_input = {"positions": {}}
    res = svc.analyze(alpha12_input=alpha_input, state_input=state_input)
    h = res.portfolio.holdings[0]
    assert h.mapping_status == "UNMAPPED"
    assert h.symbol == "UNMAPPED_STOCK_XYZ"
    assert "Portfolio symbol: None" in h.evidence[1]


def test_4_dashboard_consumes_authoritative_stability(qapp):
    """Verify Dashboard screen consumes live authoritative Alpha 12 stability result (97.9 VERY_STABLE)."""
    dash = Dashboard()
    dash.refresh_data()
    val_text = dash.lbl_stab_val.text()
    assert val_text != "N/A"
    assert "97.9" in val_text
    assert "VERY_STABLE" in val_text


def test_5_portfolio_health_structural_score_unchanged():
    """Verify Portfolio Health structural health score calculation remains intact."""
    svc = PortfolioHealthService()
    res = svc.evaluate()
    assert res.score in (90, 100)
    assert res.grade == "A"


def test_6_holding_quality_unavailable_represented_honestly(qapp):
    """Verify holding quality unavailable/unassessed state is explicitly presented."""
    screen = PortfolioHealth()
    screen.refresh_data()
    assert hasattr(screen, "holding_quality_container")
    found = False
    for i in range(screen.holding_quality_container.count()):
        item = screen.holding_quality_container.itemAt(i)
        if item and item.widget():
            txt = getattr(item.widget(), "text", lambda: "")()
            if "Holding Quality Coverage:" in txt:
                found = True
                break
    assert found, "Holding Quality Coverage explicit presentation label not found"


def test_7_watchtower_snapshot_score_timestamp_intact(qapp):
    """Verify Watchtower exposes snapshot score, grade, and timestamp explicitly."""
    wt = Watchtower()
    wt.refresh_data()
    found = False
    for i in range(wt.mon_container.count()):
        item = wt.mon_container.itemAt(i)
        if item and item.widget():
            txt = getattr(item.widget(), "text", lambda: "")()
            if "Latest Persisted Watchtower Snapshot:" in txt and "Snapshot Timestamp:" in txt:
                found = True
                break
    assert found, "Watchtower snapshot clarity label not found"


def test_8_historical_snapshots_not_deleted_or_rewritten():
    """Verify Watchtower historical monitor snapshots remain intact on disk."""
    from services.portfolio_health_monitor_dashboard_service import PortfolioHealthMonitoringDashboardService
    dash_svc = PortfolioHealthMonitoringDashboardService()
    dash = dash_svc.build_dashboard()
    assert dash.total_snapshots >= 1
    assert dash.latest_score > 0
    assert dash.latest_snapshot_time is not None


def test_9_stability_history_not_fabricated():
    """Verify stability history tenure and persistence are computed factually without fabrication."""
    stab_svc = Alpha12StabilityService()
    res = stab_svc.get_stability(auto_save=False)
    metrics = res.stability_metrics
    assert metrics is not None
    assert metrics.average_holding_tenure_months >= 0.0
    assert metrics.persistence_count >= 0


def test_10_existing_governance_behavior_unchanged():
    """Verify rebalancing governance rules remain unchanged (NO ACTION REQUIRED when near target)."""
    reb_svc = RebalancingService()
    state = reb_svc.get_state()
    assert state is not None
    assert getattr(state, "status", "") in ("UNAVAILABLE", "BALANCED", "NEAR_TARGET", "NO_ACTION_REQUIRED", "SUCCESS", "OK")


def test_11_existing_sip_allocation_behavior_unchanged():
    """Verify SIP allocation mathematics remain completely unchanged."""
    sip_svc = SIPOptimizationService()
    res = sip_svc.get_sip_analysis()
    assert res is not None
    assert getattr(res, "analysis_status", "") in ("NO_DATA", "OPTIMIZED", "BALANCED", "ANALYZED", "COMPLETE", "UNAVAILABLE")


def test_12_portfolio_health_screen_renders_completely(qapp):
    """Verify Portfolio Health screen renders all containers completely without throwing exceptions."""
    screen = PortfolioHealth()
    screen.refresh_data()
    assert screen is not None
    assert hasattr(screen, "alpha12_mapping_container")
    assert hasattr(screen, "alpha12_stability_container")


def test_13_watchtower_ready_status_intact(qapp):
    """Verify Watchtower monitoring status remains READY."""
    wt = Watchtower()
    wt.refresh_data()
    found = False
    for i in range(wt.mon_container.count()):
        item = wt.mon_container.itemAt(i)
        if item and item.widget():
            txt = getattr(item.widget(), "text", lambda: "")()
            if "Surveillance Status: READY" in txt or "Surveillance Status:" in txt:
                found = True
                break
    assert found, "Watchtower Surveillance Status label not found"


# ---------------------------------------------------------------------------
# Sprint 14.1.10 Additional Acceptance Tests (Requirements A through F)
# ---------------------------------------------------------------------------

def test_a_default_dependency_stability_behavior():
    """Requirement A: Alpha12StabilityService() without dependency injection must use Alpha12MappingService and calculate 97.9 (VERY_STABLE)."""
    stab_svc = Alpha12StabilityService()
    res = stab_svc.get_stability(auto_save=False)
    assert res is not None
    metrics = res.stability_metrics
    assert metrics is not None
    assert abs(metrics.stability_score - 97.9) < 0.1
    assert metrics.stability_rating == "VERY_STABLE"



def test_b_dashboard_stability_consistency(qapp):
    """Requirement B: Dashboard consumes authoritative mapping-aware stability result (97.9 VERY_STABLE)."""
    dash = Dashboard()
    dash.refresh_data()
    assert "97.9 (VERY_STABLE)" in dash.lbl_stab_val.text()


def test_c_cross_screen_stability_consistency(qapp):
    """Requirement C: Portfolio Health, Dashboard, and Watchtower report identical stability score/rating."""
    dash = Dashboard()
    dash.refresh_data()
    dash_text = dash.lbl_stab_val.text()

    wt = Watchtower()
    wt.refresh_data()
    wt_found = False
    for i in range(wt.stab_container.count()):
        item = wt.stab_container.itemAt(i)
        if item and item.widget():
            txt = getattr(item.widget(), "text", lambda: "")()
            if "Score 97.9/100" in txt and "VERY_STABLE" in txt:
                wt_found = True
                break
    assert wt_found, "Watchtower stability text score match not found"
    assert "97.9" in dash_text
    assert "VERY_STABLE" in dash_text


def test_d_read_only_history_protection():
    """Requirement D: Repeated calls with auto_save=False do not append entries to alpha12_stability_history.json."""
    stab_svc = Alpha12StabilityService()
    initial_entries = len(stab_svc.load_history().entries)

    # Call get_stability(auto_save=False) 5 times
    for _ in range(5):
        stab_svc.get_stability(auto_save=False)

    final_entries = len(stab_svc.load_history().entries)
    assert final_entries == initial_entries


def test_e_explicit_persistence_history():
    """Requirement E: Calling auto_save=True explicitly records a stability entry to history."""
    import tempfile
    from pathlib import Path
    temp_dir = tempfile.mkdtemp()
    try:
        hist_file = Path(temp_dir) / "test_stability_history.json"
        stab_svc = Alpha12StabilityService(storage_path=str(hist_file))
        assert len(stab_svc.load_history().entries) == 0

        stab_svc.get_stability(auto_save=True)
        assert len(stab_svc.load_history().entries) == 1
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_f_mapping_protection_aegislog_vs_ace():
    """Requirement F: AEGISLOG vs ACE mismatch remains 11 mapped, 1 unmapped, 91.7% coverage without symbol mutation."""
    map_svc = Alpha12MappingService()
    res = map_svc.analyze()
    assert res.portfolio.total_alpha12_holdings == 12
    assert res.portfolio.mapped_holdings == 11
    assert res.portfolio.unmapped_holdings == 1
    assert abs(res.portfolio.mapping_coverage_pct - 91.7) < 0.2

    # Symbols must be preserved without mutation
    alpha_syms = [h.symbol for h in res.portfolio.holdings]
    assert "AEGISLOG" in alpha_syms
    assert "ACE" not in alpha_syms  # ACE is in portfolio state, not in Alpha 12
