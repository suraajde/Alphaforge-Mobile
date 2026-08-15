"""Unit test suite for Alpha 12 Long-Term Portfolio Stability Engine (Sprint 13.9.4)."""

import json
import os
import tempfile
import pytest

from services.alpha12_stability_service import (
    Alpha12PersistenceEntry,
    Alpha12PersistenceHistory,
    Alpha12StabilityMetrics,
    Alpha12StabilityResult,
    Alpha12StabilityService,
    _empty_history,
    _empty_metrics,
    _empty_result,
)


@pytest.fixture
def tmp_storage_path():
    """Provide temporary JSON filepath for persistence testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield os.path.join(tmp_dir, "test_alpha12_stability_history.json")


def test_service_initialization(tmp_storage_path):
    """Verify service initializes with default and custom arguments."""
    svc = Alpha12StabilityService(storage_path=tmp_storage_path)
    assert svc._storage_path == tmp_storage_path
    assert svc._alpha12_mapping_service is not None
    assert svc._alpha12_replacement_governance_service is None


def test_default_dataclass_values():
    """Verify dataclasses initialize with expected defaults."""
    metrics = _empty_metrics()
    assert isinstance(metrics, Alpha12StabilityMetrics)
    assert metrics.stability_score == 0.0
    assert metrics.turnover_efficiency == 1.0

    history = _empty_history()
    assert isinstance(history, Alpha12PersistenceHistory)
    assert history.total_entries == 0

    result = _empty_result()
    assert isinstance(result, Alpha12StabilityResult)
    assert result.analysis_status == "UNAVAILABLE"


def test_none_input(tmp_storage_path):
    """Verify service handles None inputs gracefully, using auto-initialized mapping service when provided mapping is None."""
    class EmptyMappingService:
        def get_mapping(self):
            return None

    svc = Alpha12StabilityService(alpha12_mapping_service=EmptyMappingService(), storage_path=tmp_storage_path)
    res = svc.analyze_stability(None, None, None)
    assert isinstance(res, Alpha12StabilityResult)
    assert res.analysis_status == "UNAVAILABLE"
    assert res.stability_metrics is not None
    assert res.stability_metrics.stability_score == 0.0



def test_empty_portfolio(tmp_storage_path):
    """Verify safe handling of empty portfolio mappings."""

    class EmptyMapping:
        portfolio = None

    svc = Alpha12StabilityService(storage_path=tmp_storage_path)
    res = svc.get_stability(alpha12_mapping=EmptyMapping())
    assert isinstance(res, Alpha12StabilityResult)
    assert res.analysis_status == "UNAVAILABLE"


def test_stability_score_calculation_and_bounds(tmp_storage_path):
    """Verify stability score calculation, 0-100 bounding, and rating classification."""

    class MockHolding:
        def __init__(self, sym, status="MAPPED"):
            self.symbol = sym
            self.mapping_status = status

    class MockMapping:
        class Portfolio:
            total_alpha12_holdings = 12
            mapped_holdings = 12
            unmapped_holdings = 0
            holdings = [MockHolding(f"SYM{i}") for i in range(12)]

        portfolio = Portfolio()

    class MockGovernanceSnapshot:
        projected_turnover_pct = 0.0
        decisions = []

    class MockGovernance:
        governance_snapshot = MockGovernanceSnapshot()

    svc = Alpha12StabilityService(storage_path=tmp_storage_path)
    res = svc.get_stability(
        alpha12_mapping=MockMapping(),
        governance_result=MockGovernance(),
    )

    assert res.analysis_status == "ANALYZED"
    assert res.stability_metrics is not None
    assert 0.0 <= res.stability_metrics.stability_score <= 100.0
    assert res.stability_metrics.stability_rating in ("VERY_STABLE", "STABLE", "MODERATE", "UNSTABLE")
    assert res.stability_metrics.turnover_rate == 0.0
    assert res.stability_metrics.churn_risk == "LOW"


def test_turnover_and_churn_risk_classification(tmp_storage_path):
    """Verify churn risk classification based on turnover thresholds."""

    class MockGovernanceSnapshot:
        def __init__(self, turnover):
            self.projected_turnover_pct = turnover
            self.decisions = []

    class MockGovernance:
        def __init__(self, turnover):
            self.governance_snapshot = MockGovernanceSnapshot(turnover)

    svc = Alpha12StabilityService(storage_path=tmp_storage_path)

    # Low risk turnover
    res_low = svc.analyze_stability(governance_result=MockGovernance(4.0))
    assert res_low.stability_metrics.churn_risk == "LOW"

    # Moderate risk turnover
    res_mod = svc.analyze_stability(governance_result=MockGovernance(12.0))
    assert res_mod.stability_metrics.churn_risk == "MODERATE"

    # High risk turnover
    res_high = svc.analyze_stability(governance_result=MockGovernance(25.0))
    assert res_high.stability_metrics.churn_risk == "HIGH"


def test_unnecessary_swap_prevention_calculation(tmp_storage_path):
    """Verify calculation of unnecessary swap prevention metrics."""

    class MockDecision:
        def __init__(self, status):
            self.decision_status = status

    class MockGovernanceSnapshot:
        projected_turnover_pct = 5.0
        decisions = [
            MockDecision("PROTECT_INCUMBENT"),
            MockDecision("REVIEW_ELIGIBLE"),
            MockDecision("HOLD"),
            MockDecision("REPLACE_RECOMMENDED"),
        ]

    class MockGovernance:
        governance_snapshot = MockGovernanceSnapshot()

    svc = Alpha12StabilityService(storage_path=tmp_storage_path)
    res = svc.analyze_stability(governance_result=MockGovernance())

    metrics = res.stability_metrics
    assert metrics.unnecessary_swap_prevention == 3
    assert metrics.churn_prevention_ratio == 75.0  # 3 of 4


def test_persistence_history_save_load_roundtrip(tmp_storage_path):
    """Verify history loading, saving, recording, and chronological ordering."""
    svc = Alpha12StabilityService(storage_path=tmp_storage_path)

    # Initial empty state
    hist0 = svc.load_history()
    assert hist0.total_entries == 0

    # Record entries
    res1 = _empty_result("ANALYZED", "Test 1")
    res1.stability_metrics = _empty_metrics("STABLE", "Metrics 1")
    res1.stability_metrics.stability_score = 90.0
    res1.stability_metrics.persistence_count = 12

    svc.record_history(res1, timestamp="2026-08-01T10:00:00Z")

    res2 = _empty_result("ANALYZED", "Test 2")
    res2.stability_metrics = _empty_metrics("STABLE", "Metrics 2")
    res2.stability_metrics.stability_score = 92.0
    res2.stability_metrics.persistence_count = 12

    svc.record_history(res2, timestamp="2026-08-02T10:00:00Z")

    # Load and verify
    hist = svc.load_history()
    assert hist.total_entries == 2
    assert hist.earliest_timestamp == "2026-08-01T10:00:00Z"
    assert hist.latest_timestamp == "2026-08-02T10:00:00Z"
    assert hist.entries[0].stability_score == 90.0
    assert hist.entries[1].stability_score == 92.0


def test_duplicate_timestamp_prevention(tmp_storage_path):
    """Verify duplicate timestamp entries are ignored."""
    svc = Alpha12StabilityService(storage_path=tmp_storage_path)

    res = _empty_result("ANALYZED", "Test")
    res.stability_metrics = _empty_metrics("STABLE", "Metrics")
    res.stability_metrics.stability_score = 88.0

    svc.record_history(res, timestamp="2026-08-08T12:00:00Z")
    svc.record_history(res, timestamp="2026-08-08T12:00:00Z")

    hist = svc.load_history()
    assert hist.total_entries == 1


def test_corrupt_and_missing_history_handling(tmp_storage_path):
    """Verify corrupt or missing history JSON files produce safe empty history."""
    svc = Alpha12StabilityService(storage_path=tmp_storage_path)

    # Missing file
    assert not os.path.exists(tmp_storage_path)
    hist = svc.load_history()
    assert hist.total_entries == 0

    # Write corrupt JSON
    os.makedirs(os.path.dirname(tmp_storage_path), exist_ok=True)
    with open(tmp_storage_path, "w", encoding="utf-8") as f:
        f.write("{corrupt_json: invalid")

    hist_corrupt = svc.load_history()
    assert hist_corrupt.total_entries == 0


def test_defensive_exception_handling(tmp_storage_path):
    """Verify faulty dependencies never raise uncaught exceptions."""

    class FaultyService:
        def get_mapping(self):
            raise RuntimeError("Database breakdown")

    svc = Alpha12StabilityService(
        alpha12_mapping_service=FaultyService(),
        storage_path=tmp_storage_path,
    )
    res = svc.get_stability()
    assert isinstance(res, Alpha12StabilityResult)
    assert res.analysis_status == "UNAVAILABLE"


def test_deterministic_repeated_execution(tmp_storage_path):
    """Verify repeated calls with identical inputs yield identical metrics."""
    svc = Alpha12StabilityService(storage_path=tmp_storage_path)
    res1 = svc.analyze_stability(now_timestamp="2026-08-08T12:00:00Z")
    res2 = svc.analyze_stability(now_timestamp="2026-08-08T12:00:00Z")

    assert res1.analysis_status == res2.analysis_status
    assert res1.stability_metrics.stability_score == res2.stability_metrics.stability_score
    assert res1.stability_metrics.churn_risk == res2.stability_metrics.churn_risk
