"""Unit tests for Portfolio Opportunity Engine Service (Sprint 13.8.3)."""
import json
from pathlib import Path
import pytest
from services.portfolio_opportunity_service import (
    PortfolioOpportunityService,
    PortfolioOpportunityResult,
    PortfolioOpportunitySummary,
    OpportunityRecord,
    OpportunityTrackingRecord,
)


def test_service_init_defaults(tmp_path):
    """Verify service initializes cleanly with None/default arguments."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)
    assert service is not None
    assert service._holding_quality_service is None
    assert service._sip_optimization_service is None


def test_empty_result_for_none_input(tmp_path):
    """Verify empty/missing state returns UNAVAILABLE status safely."""
    storage_file = tmp_path / "opp_history.json"

    class EmptyStateService:
        def load_state(self):
            return None

    service = PortfolioOpportunityService(storage_path=storage_file)
    service._get_portfolio_state = lambda: None
    result = service.get_opportunities(state_input=False)
    assert isinstance(result, PortfolioOpportunityResult)
    assert result.analysis_status == "UNAVAILABLE"
    assert result.summary.total_opportunities == 0


def test_empty_state_handling(tmp_path):
    """Verify state with empty positions returns NO_DATA."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)
    result = service.get_opportunities(state_input={"positions": {}})
    assert result.analysis_status == "NO_DATA"
    assert result.summary.total_opportunities == 0


def test_no_available_data_handling(tmp_path):
    """Verify state with positions having 0 target weight and 0 drift produces empty opportunities safely."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)
    state = {
        "positions": {
            "FLAT": {
                "company_name": "Flat Stock",
                "target_weight": 0.0,
                "actual_weight": 0.0,
                "drift_pct": 0.0,
            }
        }
    }
    result = service.get_opportunities(state_input=state)
    assert result.analysis_status == "NO_DATA"
    assert len(result.opportunities) == 0


def test_allocation_gap_identification_and_evidence(tmp_path):
    """Verify ALLOCATION_GAP category identification and evidence formatting."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)
    state = {
        "positions": {
            "RELIANCE": {
                "company_name": "Reliance Industries",
                "category": "MIDCAP",
                "target_weight": 10.0,
                "actual_weight": 4.0,
                "drift_pct": -6.0,
            }
        }
    }
    opps = service.identify_opportunities(state=state)
    alloc_opps = [o for o in opps if o.opportunity_type == "ALLOCATION_GAP"]
    assert len(alloc_opps) == 1
    opp = alloc_opps[0]
    assert opp.symbol == "RELIANCE"
    assert opp.opportunity_status == "IDENTIFIED"
    assert any("Configured target weight: 10.00%" in e for e in opp.evidence)
    assert any("Current actual weight: 4.00%" in e for e in opp.evidence)
    assert any("-6.00%" in e for e in opp.evidence)


def test_quality_alignment_identification_and_evidence(tmp_path):
    """Verify QUALITY_ALIGNMENT category identification and evidence."""
    storage_file = tmp_path / "opp_history.json"

    class MockHQHolding:
        symbol = "INFY"
        name = "Infosys Ltd"
        asset_type = "MUTUAL_FUND"
        quality_score = 85.0
        quality_grade = "A"
        assessment_status = "ASSESSED"
        evidence = ["Strong historical consistency"]

    class MockHQResult:
        holdings = [MockHQHolding()]

    service = PortfolioOpportunityService(storage_path=storage_file)
    state = {
        "positions": {
            "INFY": {
                "company_name": "Infosys Ltd",
                "category": "MUTUAL_FUND",
                "target_weight": 10.0,
                "actual_weight": 8.0,
                "drift_pct": -2.0,
            }
        }
    }
    opps = service.identify_opportunities(state=state, hq_res=MockHQResult())
    qual_opps = [o for o in opps if o.opportunity_type == "QUALITY_ALIGNMENT"]
    assert len(qual_opps) == 1
    opp = qual_opps[0]
    assert opp.symbol == "INFY"
    assert opp.quality_score == 85.0
    assert any("85.0" in e for e in opp.evidence)
    assert any("Grade: A" in e for e in opp.evidence)


def test_sip_coverage_identification_and_evidence(tmp_path):
    """Verify SIP_COVERAGE category identification and evidence."""
    storage_file = tmp_path / "opp_history.json"

    class MockSIPHolding:
        symbol = "TCS"
        name = "Tata Consultancy Services"
        sip_transaction_count = 0
        sip_invested_amount = 0.0

    class MockSIPDist:
        sip_coverage_pct = 50.0

    class MockSIPResult:
        holdings = [MockSIPHolding()]
        distribution = MockSIPDist()

    service = PortfolioOpportunityService(storage_path=storage_file)
    state = {
        "positions": {
            "TCS": {
                "company_name": "Tata Consultancy Services",
                "category": "LARGE_CAP",
                "target_weight": 15.0,
                "actual_weight": 10.0,
                "drift_pct": -5.0,
            }
        }
    }
    opps = service.identify_opportunities(state=state, sip_res=MockSIPResult())
    sip_opps = [o for o in opps if o.opportunity_type == "SIP_COVERAGE"]
    assert len(sip_opps) == 1
    opp = sip_opps[0]
    assert opp.symbol == "TCS"
    assert any("zero recorded SIP transactions" in e for e in opp.evidence)


def test_portfolio_structure_identification_and_evidence(tmp_path):
    """Verify PORTFOLIO_STRUCTURE category identification for top position concentration."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)
    state = {
        "positions": {
            "HDFCBANK": {
                "company_name": "HDFC Bank Ltd",
                "category": "LARGE_CAP",
                "target_weight": 10.0,
                "actual_weight": 25.0,
                "drift_pct": 15.0,
            },
            "TCS": {
                "company_name": "Tata Consultancy Services",
                "category": "LARGE_CAP",
                "target_weight": 10.0,
                "actual_weight": 5.0,
                "drift_pct": -5.0,
            },
        }
    }
    opps = service.identify_opportunities(state=state)
    struct_opps = [o for o in opps if o.opportunity_type == "PORTFOLIO_STRUCTURE"]
    assert len(struct_opps) == 1
    opp = struct_opps[0]
    assert opp.symbol == "HDFCBANK"
    assert any("25.00%" in e for e in opp.evidence)


def test_deterministic_scoring_and_boundaries(tmp_path):
    """Verify score calculation is deterministic and strictly clamped within 0.0 - 100.0."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)

    score1, prio1 = service._score_opportunity("ALLOCATION_GAP", 2.0, 20.0, -18.0)
    score2, prio2 = service._score_opportunity("ALLOCATION_GAP", 2.0, 20.0, -18.0)
    assert score1 == score2 == 100.0  # Clamped at max 100
    assert prio1 == prio2 == "HIGH"

    min_score, min_prio = service._score_opportunity("UNKNOWN", 0.0, 0.0, 0.0)
    assert 0.0 <= min_score <= 100.0
    assert min_prio in ("HIGH", "MEDIUM", "LOW")


def test_priority_classification(tmp_path):
    """Verify priority thresholds: score >= 70 -> HIGH, 40-70 -> MEDIUM, < 40 -> LOW."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)

    s_high, p_high = service._score_opportunity("QUALITY_ALIGNMENT", 5.0, 15.0, -10.0, quality_score=90.0)
    assert s_high >= 70.0
    assert p_high == "HIGH"

    s_med, p_med = service._score_opportunity("QUALITY_ALIGNMENT", 5.0, 5.0, 0.0, quality_score=60.0)
    assert 40.0 <= s_med < 70.0
    assert p_med == "MEDIUM"


def test_deterministic_sorting(tmp_path):
    """Verify deterministic multi-key sorting: Priority desc, Score desc, Symbol asc, ID asc."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)

    opps = [
        OpportunityRecord(opportunity_id="OPP_B", symbol="BBB", name="B", asset_type="EQ", opportunity_type="ALLOCATION_GAP", opportunity_score=50.0, priority="LOW"),
        OpportunityRecord(opportunity_id="OPP_A", symbol="AAA", name="A", asset_type="EQ", opportunity_type="ALLOCATION_GAP", opportunity_score=90.0, priority="HIGH"),
        OpportunityRecord(opportunity_id="OPP_C", symbol="CCC", name="C", asset_type="EQ", opportunity_type="ALLOCATION_GAP", opportunity_score=80.0, priority="HIGH"),
    ]
    sorted_opps = service._sort_opportunities(opps)
    assert [o.symbol for o in sorted_opps] == ["AAA", "CCC", "BBB"]


def test_summary_metrics(tmp_path):
    """Verify summary metrics calculation for identified opportunities."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)

    opps = [
        OpportunityRecord(opportunity_id="1", symbol="A", name="A", asset_type="EQ", opportunity_type="ALLOC", opportunity_score=80.0, priority="HIGH", opportunity_status="IDENTIFIED"),
        OpportunityRecord(opportunity_id="2", symbol="B", name="B", asset_type="EQ", opportunity_type="ALLOC", opportunity_score=40.0, priority="MEDIUM", opportunity_status="IDENTIFIED"),
    ]
    summary = service.build_summary(opps)
    assert summary.total_opportunities == 2
    assert summary.high_priority_count == 1
    assert summary.medium_priority_count == 1
    assert summary.low_priority_count == 0
    assert summary.assessed_count == 2
    assert summary.average_opportunity_score == 60.0
    assert summary.highest_opportunity_score == 80.0


def test_tracking_persistence_and_duplicate_prevention(tmp_path):
    """Verify history persistence and duplicate record prevention."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)

    result = PortfolioOpportunityResult(
        analysis_status="ANALYZED",
        latest_timestamp="2026-08-08T12:00:00Z",
        opportunities=[
            OpportunityRecord(opportunity_id="OPP_TEST", symbol="TEST", name="Test", asset_type="EQ", opportunity_type="ALLOCATION_GAP", opportunity_score=75.0, priority="HIGH", opportunity_status="IDENTIFIED")
        ]
    )

    success1 = service.record_tracking(result)
    assert success1 is True
    history1 = service.load_tracking_history()
    assert len(history1) == 1
    assert history1[0]["opportunity_id"] == "OPP_TEST"

    # Attempt to record identical snapshot again -> duplicate prevented
    success2 = service.record_tracking(result)
    assert success2 is True
    history2 = service.load_tracking_history()
    assert len(history2) == 1  # Still 1 record, no duplicate added


def test_missing_tracking_file(tmp_path):
    """Verify loading from non-existent history file returns empty list safely."""
    missing_file = tmp_path / "non_existent_history.json"
    service = PortfolioOpportunityService(storage_path=missing_file)
    history = service.load_tracking_history()
    assert history == []


def test_empty_tracking_file(tmp_path):
    """Verify empty history file handles safely."""
    empty_file = tmp_path / "empty_history.json"
    empty_file.write_text("", encoding="utf-8")
    service = PortfolioOpportunityService(storage_path=empty_file)
    history = service.load_tracking_history()
    assert history == []


def test_corrupt_json_tracking_file(tmp_path):
    """Verify corrupt JSON history file handles safely without crashing."""
    corrupt_file = tmp_path / "corrupt_history.json"
    corrupt_file.write_text("{invalid json content:", encoding="utf-8")
    service = PortfolioOpportunityService(storage_path=corrupt_file)
    history = service.load_tracking_history()
    assert history == []


def test_malformed_tracking_records(tmp_path):
    """Verify non-list / malformed JSON records handle safely."""
    malformed_file = tmp_path / "malformed_history.json"
    malformed_file.write_text(json.dumps({"not_a_list": 123}), encoding="utf-8")
    service = PortfolioOpportunityService(storage_path=malformed_file)
    history = service.load_tracking_history()
    assert history == []


def test_malformed_state_handling(tmp_path):
    """Verify malformed state structures handle safely without throwing exceptions."""
    storage_file = tmp_path / "opp_history.json"
    service = PortfolioOpportunityService(storage_path=storage_file)
    malformed_states = [
        "invalid state string",
        {"positions": "invalid positions format"},
        {"positions": {"TEST": "invalid position format"}},
    ]
    for st in malformed_states:
        result = service.get_opportunities(state_input=st)
        assert isinstance(result, PortfolioOpportunityResult)
        assert result.analysis_status in ("UNAVAILABLE", "NO_DATA", "ERROR")


def test_exception_resilience(tmp_path):
    """Verify internal exceptions return safe ERROR result without crashing."""
    storage_file = tmp_path / "opp_history.json"

    class BrokenStateService:
        def load_state(self):
            raise RuntimeError("Database error")

    service = PortfolioOpportunityService(storage_path=storage_file)
    service._get_portfolio_state = lambda: (_ for _ in ()).throw(RuntimeError("Simulated engine crash"))
    result = service.get_opportunities(state_input=None)
    assert isinstance(result, PortfolioOpportunityResult)
    assert result.analysis_status == "ERROR"
