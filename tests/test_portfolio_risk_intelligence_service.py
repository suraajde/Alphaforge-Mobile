"""Unit tests for Portfolio Risk Intelligence Service (Sprint 13.8.4)."""
import json
from pathlib import Path
import pytest
from services.portfolio_risk_intelligence_service import (
    PortfolioRiskIntelligenceService,
    PortfolioRiskResult,
    PortfolioRiskSummary,
    RiskAssessment,
    RiskHistoryEntry,
    RiskHistory,
)


def test_service_instantiation(tmp_path):
    """TEST 1: Verify service instantiation with default and custom storage paths."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)
    assert service is not None
    assert service._holding_quality_service is None
    assert service._rebalancing_service is None


def test_default_dataclass_values():
    """TEST 2: Verify default dataclass values and structures."""
    assessment = RiskAssessment(
        risk_id="R1",
        symbol="TEST",
        name="Test Symbol",
        asset_type="EQUITY",
        risk_type="CONCENTRATION",
    )
    assert assessment.risk_score == 0.0
    assert assessment.risk_level == "UNAVAILABLE"
    assert assessment.assessment_status == "UNAVAILABLE"

    summary = PortfolioRiskSummary()
    assert summary.total_assessments == 0
    assert summary.high_risk_count == 0

    result = PortfolioRiskResult()
    assert result.analysis_status == "UNAVAILABLE"
    assert result.assessments == []

    history = RiskHistory()
    assert history.total_entries == 0
    assert history.entries == []


def test_empty_result_for_none_input(tmp_path):
    """TEST 3 & 4: Verify None input returns UNAVAILABLE status safely."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)
    service._get_portfolio_state = lambda: None
    result = service.get_risk(state_input=False)
    assert isinstance(result, PortfolioRiskResult)
    assert result.analysis_status == "UNAVAILABLE"
    assert result.summary.total_assessments == 0


def test_unavailable_portfolio_handling(tmp_path):
    """TEST 5: Verify portfolio state with no positions returns NO_DATA status."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)
    result = service.get_risk(state_input={"positions": {}})
    assert result.analysis_status == "NO_DATA"
    assert result.summary.total_assessments == 0


def test_concentration_assessment_and_thresholds(tmp_path):
    """TEST 6 & 7: Verify concentration assessment and transparent risk level thresholds."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    # Position weights: HIGH (>=20%), MEDIUM (10-20%), LOW (<10%)
    state = {
        "positions": {
            "RELIANCE": {"company_name": "Reliance Industries", "actual_weight": 25.0, "target_weight": 10.0, "drift_pct": 15.0},
            "INFY": {"company_name": "Infosys Ltd", "actual_weight": 15.0, "target_weight": 10.0, "drift_pct": 5.0},
            "TCS": {"company_name": "Tata Consultancy Services", "actual_weight": 6.0, "target_weight": 5.0, "drift_pct": 1.0},
        }
    }
    result = service.get_risk(state_input=state)
    assert result.analysis_status == "ANALYZED"

    conc_assessments = [a for a in result.assessments if a.risk_type == "CONCENTRATION"]
    assert len(conc_assessments) == 3

    rel_conc = next(a for a in conc_assessments if a.symbol == "RELIANCE")
    infy_conc = next(a for a in conc_assessments if a.symbol == "INFY")
    tcs_conc = next(a for a in conc_assessments if a.symbol == "TCS")

    assert rel_conc.risk_level == "HIGH"
    assert rel_conc.risk_score >= 70.0

    assert infy_conc.risk_level == "MEDIUM"
    assert 40.0 <= infy_conc.risk_score < 70.0

    assert tcs_conc.risk_level == "LOW"
    assert tcs_conc.risk_score < 40.0


def test_allocation_assessment(tmp_path):
    """TEST 8: Verify ALLOCATION risk assessment for measurable target drift imbalance."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    state = {
        "positions": {
            "HDFCBANK": {"company_name": "HDFC Bank Ltd", "actual_weight": 15.0, "target_weight": 5.0, "drift_pct": 10.0}
        }
    }
    result = service.get_risk(state_input=state)
    alloc_assessments = [a for a in result.assessments if a.risk_type == "ALLOCATION"]
    assert len(alloc_assessments) == 1
    alloc = alloc_assessments[0]
    assert alloc.symbol == "HDFCBANK"
    assert any("Current weight is 15.00%" in e for e in alloc.evidence)
    assert any("10.00%" in e for e in alloc.evidence)


def test_diversification_assessment(tmp_path):
    """TEST 9: Verify DIVERSIFICATION risk assessment based on position count."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    # 3 positions -> concentrated diversification status
    state = {
        "positions": {
            "P1": {"actual_weight": 50.0},
            "P2": {"actual_weight": 30.0},
            "P3": {"actual_weight": 20.0},
        }
    }
    result = service.get_risk(state_input=state)
    div_assessments = [a for a in result.assessments if a.risk_type == "DIVERSIFICATION"]
    assert len(div_assessments) == 1
    div = div_assessments[0]
    assert div.symbol == "PORTFOLIO"
    assert div.risk_level == "HIGH"  # pos_count < 5 -> HIGH risk score
    assert result.summary.diversification_status == "CONCENTRATED"


def test_drift_assessment(tmp_path):
    """TEST 10: Verify DRIFT assessment integration with DriftDetection metrics."""
    storage_file = tmp_path / "risk_history.json"

    class MockDriftMetric:
        name = "TATAMOTORS"
        current_weight = 12.0
        target_weight = 5.0
        drift = 7.0
        absolute_drift = 7.0
        direction = "OVERWEIGHT"

    class MockDriftResult:
        metrics = [MockDriftMetric()]

    class MockDriftService:
        def detect_drift(self):
            return MockDriftResult()

    service = PortfolioRiskIntelligenceService(drift_detection_service=MockDriftService(), storage_path=storage_file)
    state = {
        "positions": {
            "TATAMOTORS": {"company_name": "Tata Motors", "actual_weight": 12.0, "target_weight": 5.0, "drift_pct": 7.0}
        }
    }
    result = service.analyze_risk(state_input=state)

    drift_assessments = [a for a in result.assessments if a.risk_type == "DRIFT"]
    assert len(drift_assessments) >= 1
    dr = drift_assessments[0]
    assert dr.name == "TATAMOTORS"
    assert any("7.00%" in e for e in dr.evidence)


def test_structure_assessment(tmp_path):
    """TEST 11: Verify STRUCTURE assessment for dominant category concentration."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    state = {
        "positions": {
            "STOCK1": {"category": "LARGE_CAP", "actual_weight": 25.0},
            "STOCK2": {"category": "LARGE_CAP", "actual_weight": 20.0},
        }
    }
    result = service.get_risk(state_input=state)
    struct_assessments = [a for a in result.assessments if a.risk_type == "STRUCTURE"]
    assert len(struct_assessments) == 1
    struct = struct_assessments[0]
    assert struct.symbol == "LARGE_CAP"
    assert any("45.00%" in e for e in struct.evidence)


def test_risk_score_deterministic_behavior(tmp_path):
    """TEST 12: Verify risk score is reproducible and deterministic for identical inputs."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    s1 = service._score_risk("CONCENTRATION", 25.0, 10.0, 15.0)
    s2 = service._score_risk("CONCENTRATION", 25.0, 10.0, 15.0)
    assert s1 == s2 == 77.5


def test_risk_score_boundary_clamping(tmp_path):
    """TEST 13: Verify risk scores are strictly clamped between 0.0 and 100.0."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    max_score = service._score_risk("CONCENTRATION", 100.0, 0.0, 100.0)
    assert max_score == 100.0

    min_score = service._score_risk("DIVERSIFICATION", 0.0, 0.0, 0.0, extra_val=50.0)
    assert min_score >= 0.0 and min_score <= 100.0


def test_risk_level_classification(tmp_path):
    """TEST 14: Verify risk level classification thresholds."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    assert service._classify_risk_level(80.0) == "HIGH"
    assert service._classify_risk_level(50.0) == "MEDIUM"
    assert service._classify_risk_level(20.0) == "LOW"
    assert service._classify_risk_level(50.0, status="UNAVAILABLE") == "UNAVAILABLE"


def test_deterministic_sorting(tmp_path):
    """TEST 15: Verify multi-key sorting: Level (HIGH>MEDIUM>LOW), Score desc, Symbol asc, Risk ID asc."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    assessments = [
        RiskAssessment(risk_id="R1", symbol="BBB", name="B", asset_type="EQ", risk_type="CONC", risk_score=30.0, risk_level="LOW"),
        RiskAssessment(risk_id="R2", symbol="AAA", name="A", asset_type="EQ", risk_type="CONC", risk_score=90.0, risk_level="HIGH"),
        RiskAssessment(risk_id="R3", symbol="CCC", name="C", asset_type="EQ", risk_type="CONC", risk_score=75.0, risk_level="HIGH"),
    ]
    sorted_items = service._sort_assessments(assessments)
    assert [a.symbol for a in sorted_items] == ["AAA", "CCC", "BBB"]


def test_summary_metrics_computation(tmp_path):
    """TEST 16: Verify summary metrics calculation."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    assessments = [
        RiskAssessment(risk_id="R1", symbol="A", name="A", asset_type="EQ", risk_type="CONC", risk_score=80.0, risk_level="HIGH", assessment_status="ASSESSED"),
        RiskAssessment(risk_id="R2", symbol="B", name="B", asset_type="EQ", risk_type="CONC", risk_score=40.0, risk_level="MEDIUM", assessment_status="ASSESSED"),
    ]
    summary = service.build_summary(assessments, position_count=2, largest_position_weight=50.0)
    assert summary.total_assessments == 2
    assert summary.high_risk_count == 1
    assert summary.medium_risk_count == 1
    assert summary.low_risk_count == 0
    assert summary.average_risk_score == 60.0
    assert summary.highest_risk_score == 80.0
    assert summary.largest_position_weight == 50.0
    assert summary.position_count == 2


def test_history_creation_save_load_round_trip(tmp_path):
    """TEST 17 & 18: Verify risk history creation, save, and load round trip."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    result = PortfolioRiskResult(
        analysis_status="ANALYZED",
        latest_timestamp="2026-08-08T10:00:00Z",
        summary=PortfolioRiskSummary(average_risk_score=50.0, highest_risk_score=80.0, high_risk_count=1, position_count=5, largest_position_weight=25.0)
    )

    success = service.record_history(result=result, timestamp="2026-08-08T10:00:00Z")
    assert success is True

    history = service.load_history()
    assert history.total_entries == 1
    assert history.entries[0].timestamp == "2026-08-08T10:00:00Z"
    assert history.entries[0].average_risk_score == 50.0


def test_chronological_history_ordering(tmp_path):
    """TEST 19: Verify risk history entries are always sorted chronologically (OLDEST -> NEWEST)."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    res1 = PortfolioRiskResult(summary=PortfolioRiskSummary(average_risk_score=40.0))
    res2 = PortfolioRiskResult(summary=PortfolioRiskSummary(average_risk_score=60.0))

    service.record_history(result=res2, timestamp="2026-08-08T12:00:00Z")
    service.record_history(result=res1, timestamp="2026-08-08T08:00:00Z")

    history = service.load_history()
    assert len(history.entries) == 2
    assert history.entries[0].timestamp == "2026-08-08T08:00:00Z"
    assert history.entries[1].timestamp == "2026-08-08T12:00:00Z"
    assert history.earliest_timestamp == "2026-08-08T08:00:00Z"
    assert history.latest_timestamp == "2026-08-08T12:00:00Z"


def test_duplicate_timestamp_prevention(tmp_path):
    """TEST 20: Verify duplicate timestamp entries are prevented in history."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    res = PortfolioRiskResult(summary=PortfolioRiskSummary(average_risk_score=50.0))
    service.record_history(result=res, timestamp="2026-08-08T10:00:00Z")
    service.record_history(result=res, timestamp="2026-08-08T10:00:00Z")

    history = service.load_history()
    assert history.total_entries == 1


def test_missing_history_file(tmp_path):
    """TEST 21: Verify loading from non-existent history file returns empty RiskHistory safely."""
    missing_file = tmp_path / "missing_risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=missing_file)
    history = service.load_history()
    assert isinstance(history, RiskHistory)
    assert history.total_entries == 0


def test_empty_history_file(tmp_path):
    """TEST 22: Verify empty history file handles safely."""
    empty_file = tmp_path / "empty_risk_history.json"
    empty_file.write_text("", encoding="utf-8")
    service = PortfolioRiskIntelligenceService(storage_path=empty_file)
    history = service.load_history()
    assert history.total_entries == 0


def test_corrupt_json_history_file(tmp_path):
    """TEST 23: Verify corrupt JSON history file handles safely without crashing."""
    corrupt_file = tmp_path / "corrupt_risk_history.json"
    corrupt_file.write_text("{corrupt json data", encoding="utf-8")
    service = PortfolioRiskIntelligenceService(storage_path=corrupt_file)
    history = service.load_history()
    assert history.total_entries == 0


def test_malformed_history_records(tmp_path):
    """TEST 24: Verify non-list / malformed history JSON data handles safely."""
    malformed_file = tmp_path / "malformed_risk_history.json"
    malformed_file.write_text(json.dumps({"invalid_root": True}), encoding="utf-8")
    service = PortfolioRiskIntelligenceService(storage_path=malformed_file)
    history = service.load_history()
    assert history.total_entries == 0


def test_malformed_portfolio_state(tmp_path):
    """TEST 25: Verify malformed portfolio state inputs handle safely."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    malformed_states = [
        "not a dict",
        {"positions": "not a positions dict"},
        {"positions": {"ABC": "not a position dict"}},
    ]
    for st in malformed_states:
        result = service.get_risk(state_input=st)
        assert isinstance(result, PortfolioRiskResult)
        assert result.analysis_status in ("UNAVAILABLE", "NO_DATA", "ERROR")


def test_missing_fields_resilience(tmp_path):
    """TEST 26: Verify position missing optional fields handles without exception."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)

    state = {
        "positions": {
            "SPARSE": {}  # Empty position dict with no target_weight/actual_weight keys
        }
    }
    result = service.get_risk(state_input=state)
    assert isinstance(result, PortfolioRiskResult)
    assert result.analysis_status in ("ANALYZED", "NO_DATA")


def test_dependency_exception_resilience(tmp_path):
    """TEST 27: Verify upstream service exceptions handle gracefully."""
    storage_file = tmp_path / "risk_history.json"

    class BrokenAllocationService:
        def analyze_allocation(self):
            raise RuntimeError("Allocation engine crashed")

    service = PortfolioRiskIntelligenceService(
        allocation_analysis_service=BrokenAllocationService(),
        storage_path=storage_file,
    )
    state = {
        "positions": {
            "STOCK": {"actual_weight": 10.0, "target_weight": 10.0}
        }
    }
    result = service.get_risk(state_input=state)
    assert isinstance(result, PortfolioRiskResult)
    assert result.analysis_status == "ANALYZED"


def test_public_method_exception_resilience(tmp_path):
    """TEST 28: Verify public methods catch unhandled exceptions defensively."""
    storage_file = tmp_path / "risk_history.json"
    service = PortfolioRiskIntelligenceService(storage_path=storage_file)
    service._assess_concentration = lambda p: (_ for _ in ()).throw(RuntimeError("Engine failure"))

    state = {"positions": {"TEST": {"actual_weight": 10.0}}}
    result = service.get_risk(state_input=state)
    assert isinstance(result, PortfolioRiskResult)
    assert result.analysis_status == "ERROR"
