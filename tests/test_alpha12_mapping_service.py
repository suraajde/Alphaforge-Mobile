"""Unit tests for Alpha 12 Portfolio Mapping Service (Sprint 13.9.0)."""
import json
from pathlib import Path
import pytest
from services.alpha12_mapping_service import (
    Alpha12HoldingMapping,
    Alpha12MappingResult,
    Alpha12MappingService,
    Alpha12PortfolioMapping,
)


def test_service_instantiation(tmp_path):
    """TEST 1: Verify service instantiation with default and custom storage paths."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)
    assert service is not None
    assert service._portfolio_service is None
    assert service._portfolio_intelligence_service is None
    assert service._rebalancing_service is None


def test_default_dataclass_values():
    """TEST 2: Verify default dataclass values and structures."""
    holding = Alpha12HoldingMapping(symbol="RELIANCE", name="Reliance Industries")
    assert holding.alpha12_rank is None
    assert holding.alpha12_weight is None
    assert holding.current_weight is None
    assert holding.mapping_status == "UNAVAILABLE"

    port = Alpha12PortfolioMapping()
    assert port.mapping_status == "UNAVAILABLE"
    assert port.total_alpha12_holdings == 0
    assert port.mapped_holdings == 0
    assert port.mapping_coverage_pct == 0.0

    result = Alpha12MappingResult()
    assert result.analysis_status == "UNAVAILABLE"
    assert result.portfolio.mapping_status == "UNAVAILABLE"


def test_missing_alpha12_source(tmp_path):
    """TEST 3: Verify missing Alpha 12 source safely returns UNAVAILABLE status."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)
    service._load_alpha12_source = lambda source_input=None: None
    result = service.get_mapping()
    assert result.analysis_status == "UNAVAILABLE"
    assert "Alpha 12 portfolio source is not available." in result.rationale


def test_empty_alpha12_source(tmp_path):
    """TEST 4: Verify empty Alpha 12 source safely returns NO_DATA status."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)
    result = service.get_mapping(alpha12_input=[])
    assert result.analysis_status == "NO_DATA"
    assert result.portfolio.mapping_status == "EMPTY"


def test_valid_alpha12_mapping_and_exact_symbol_matching(tmp_path):
    """TEST 5 & 6: Verify valid mapping and exact symbol matching."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [
        {"symbol": "HDFCBANK", "name": "HDFC Bank", "alpha12_rank": 1, "alpha12_weight": 15.0},
        {"symbol": "INFY", "name": "Infosys", "alpha12_rank": 2, "alpha12_weight": 10.0},
    ]
    portfolio_state = {
        "positions": {
            "HDFCBANK": {"company_name": "HDFC Bank Ltd", "actual_weight": 14.5, "current_value": 145000.0},
        }
    }

    result = service.get_mapping(alpha12_input=alpha12_source, state_input=portfolio_state)
    assert result.analysis_status == "ANALYZED"

    port = result.portfolio
    assert port.total_alpha12_holdings == 2
    assert port.mapped_holdings == 1
    assert port.unmapped_holdings == 1
    assert port.mapping_coverage_pct == 50.0

    hdfc = next(h for h in port.holdings if h.symbol == "HDFCBANK")
    assert hdfc.mapping_status == "MAPPED"
    assert hdfc.current_weight == 14.5
    assert hdfc.current_value == 145000.0

    infy = next(h for h in port.holdings if h.symbol == "INFY")
    assert infy.mapping_status == "UNMAPPED"
    assert infy.current_weight is None
    assert infy.current_value is None


def test_symbol_normalization(tmp_path):
    """TEST 7: Verify lower-case and whitespace symbols are normalized cleanly."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [{"symbol": " tcs ", "name": "Tata Consultancy Services"}]
    portfolio_state = {"positions": {"TCS": {"actual_weight": 8.0}}}

    result = service.get_mapping(alpha12_input=alpha12_source, state_input=portfolio_state)
    assert result.portfolio.mapped_holdings == 1
    assert result.portfolio.holdings[0].symbol == "TCS"
    assert result.portfolio.holdings[0].mapping_status == "MAPPED"


def test_name_mismatch_does_not_create_mapping(tmp_path):
    """TEST 8: Verify matching is strictly by symbol and not merely company name."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [{"symbol": "ALPHA", "name": "Shared Name"}]
    portfolio_state = {"positions": {"BETA": {"name": "Shared Name", "actual_weight": 5.0}}}

    result = service.get_mapping(alpha12_input=alpha12_source, state_input=portfolio_state)
    assert result.portfolio.mapped_holdings == 0
    assert result.portfolio.holdings[0].symbol == "ALPHA"
    assert result.portfolio.holdings[0].mapping_status == "UNMAPPED"


def test_mapped_holding_fields_preserved(tmp_path):
    """TEST 9: Verify all source and portfolio fields are preserved on mapped holdings."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [{"symbol": "RELIANCE", "name": "Reliance", "alpha12_rank": 1, "alpha12_weight": 12.0, "category": "LARGE_CAP"}]
    portfolio_state = {"positions": {"RELIANCE": {"company_name": "Reliance Industries Ltd", "actual_weight": 15.0, "current_value": 150000.0}}}

    result = service.get_mapping(alpha12_input=alpha12_source, state_input=portfolio_state)
    h = result.portfolio.holdings[0]
    assert h.symbol == "RELIANCE"
    assert h.name == "Reliance Industries Ltd"
    assert h.alpha12_rank == 1
    assert h.alpha12_weight == 12.0
    assert h.current_weight == 15.0
    assert h.current_value == 150000.0
    assert h.asset_type == "LARGE_CAP"


def test_unmapped_alpha12_holdings_preserved_without_fabrication(tmp_path):
    """TEST 10 & 15: Verify unmapped Alpha 12 holdings are preserved as UNMAPPED without fabricated positions."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [{"symbol": "UNMAPPED_STOCK", "name": "Unmapped Co", "alpha12_rank": 5, "alpha12_weight": 8.33}]
    result = service.get_mapping(alpha12_input=alpha12_source, state_input={"positions": {}})

    h = result.portfolio.holdings[0]
    assert h.symbol == "UNMAPPED_STOCK"
    assert h.mapping_status == "UNMAPPED"
    assert h.current_weight is None
    assert h.current_value is None
    assert h.alpha12_weight == 8.33


def test_mapping_coverage_calculation(tmp_path):
    """TEST 11: Verify mapping coverage percentage calculation."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [{"symbol": f"SYM_{i}"} for i in range(10)]
    portfolio_state = {"positions": {"SYM_0": {"actual_weight": 10.0}, "SYM_1": {"actual_weight": 10.0}, "SYM_2": {"actual_weight": 10.0}}}

    result = service.get_mapping(alpha12_input=alpha12_source, state_input=portfolio_state)
    assert result.portfolio.total_alpha12_holdings == 10
    assert result.portfolio.mapped_holdings == 3
    assert result.portfolio.unmapped_holdings == 7
    assert result.portfolio.mapping_coverage_pct == 30.0


def test_alpha12_rank_and_weight_preservation(tmp_path):
    """TEST 12, 13, 14: Verify rank/weight preservation and absence of equal-weight fabrication."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [
        {"symbol": "STOCK_A", "alpha12_rank": 1, "alpha12_weight": 25.0},
        {"symbol": "STOCK_B", "alpha12_rank": 2, "alpha12_weight": 15.0},
    ]

    result = service.get_mapping(alpha12_input=alpha12_source, state_input={"positions": {}})
    h0 = result.portfolio.holdings[0]
    h1 = result.portfolio.holdings[1]

    assert h0.alpha12_rank == 1
    assert h0.alpha12_weight == 25.0
    assert h1.alpha12_rank == 2
    assert h1.alpha12_weight == 15.0


def test_malformed_alpha12_data(tmp_path):
    """TEST 16: Verify malformed items in Alpha 12 source input handle gracefully."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    malformed_source = [None, "", {}, 12345, {"symbol": ""}, {"symbol": "VALID"}]
    result = service.get_mapping(alpha12_input=malformed_source, state_input={"positions": {}})

    assert result.analysis_status == "ANALYZED"
    assert result.portfolio.total_alpha12_holdings == 1
    assert result.portfolio.holdings[0].symbol == "VALID"


def test_missing_portfolio_data(tmp_path):
    """TEST 17: Verify missing/None portfolio state handles safely without error."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [{"symbol": "STOCK"}]
    result = service.get_mapping(alpha12_input=alpha12_source, state_input=None)
    assert result.analysis_status == "ANALYZED"
    assert result.portfolio.mapped_holdings == 0
    assert result.portfolio.unmapped_holdings == 1


def test_missing_fields(tmp_path):
    """TEST 18: Verify missing optional fields on holding items handle safely."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [{"symbol": "SPARSE"}]
    result = service.get_mapping(alpha12_input=alpha12_source, state_input={"positions": {"SPARSE": {}}})
    h = result.portfolio.holdings[0]
    assert h.symbol == "SPARSE"
    assert h.mapping_status == "MAPPED"
    assert h.alpha12_rank is None
    assert h.alpha12_weight is None
    assert h.current_weight is None


def test_corrupt_persistence_file(tmp_path):
    """TEST 19: Verify corrupt JSON history file handles safely."""
    corrupt_file = tmp_path / "corrupt_history.json"
    corrupt_file.write_text("{invalid json content", encoding="utf-8")
    service = Alpha12MappingService(storage_path=corrupt_file)

    history = service.load_history()
    assert history == []


def test_empty_persistence_file(tmp_path):
    """TEST 20: Verify empty history file handles safely."""
    empty_file = tmp_path / "empty_history.json"
    empty_file.write_text("", encoding="utf-8")
    service = Alpha12MappingService(storage_path=empty_file)

    history = service.load_history()
    assert history == []


def test_duplicate_timestamp_prevention(tmp_path):
    """TEST 21: Verify duplicate timestamp recording is prevented."""
    storage_file = tmp_path / "history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    res = Alpha12MappingResult(
        analysis_status="ANALYZED",
        portfolio=Alpha12PortfolioMapping(mapping_status="MAPPED", total_alpha12_holdings=1)
    )

    service.record_history(result=res, timestamp="2026-08-08T12:00:00Z")
    service.record_history(result=res, timestamp="2026-08-08T12:00:00Z")

    history = service.load_history()
    assert len(history) == 1


def test_defensive_dependency_exceptions(tmp_path):
    """TEST 22: Verify upstream dependency exceptions are caught defensively."""
    storage_file = tmp_path / "history.json"

    class BrokenPortfolioService:
        def load_state(self):
            raise RuntimeError("Database error")

    service = Alpha12MappingService(portfolio_service=BrokenPortfolioService(), storage_path=storage_file)
    alpha12_source = [{"symbol": "STOCK"}]
    result = service.get_mapping(alpha12_input=alpha12_source)
    assert result.analysis_status == "ANALYZED"


def test_none_input_handling(tmp_path):
    """TEST 23: Verify None inputs handle safely."""
    storage_file = tmp_path / "history.json"
    service = Alpha12MappingService(storage_path=storage_file)
    service._load_alpha12_source = lambda source_input=None: None

    result = service.analyze(alpha12_input=None, state_input=None)
    assert result.analysis_status == "UNAVAILABLE"


def test_public_method_exception_safety(tmp_path):
    """TEST 24: Verify public methods catch unhandled exceptions defensively."""
    storage_file = tmp_path / "history.json"
    service = Alpha12MappingService(storage_path=storage_file)
    service._map_holdings = lambda a, p: (_ for _ in ()).throw(RuntimeError("Mapping engine failed"))

    result = service.analyze(alpha12_input=[{"symbol": "STOCK"}])
    assert result.analysis_status == "ERROR"


def test_deterministic_mapping_ordering(tmp_path):
    """TEST 25: Verify deterministic mapping sorting by alpha12_rank asc, then symbol asc."""
    storage_file = tmp_path / "history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [
        {"symbol": "ZETA", "alpha12_rank": 3},
        {"symbol": "BETA", "alpha12_rank": 1},
        {"symbol": "ALPHA", "alpha12_rank": 1},
        {"symbol": "UNRANKED_B"},
        {"symbol": "UNRANKED_A"},
    ]

    result = service.get_mapping(alpha12_input=alpha12_source, state_input={"positions": {}})
    symbols = [h.symbol for h in result.portfolio.holdings]
    assert symbols == ["ALPHA", "BETA", "ZETA", "UNRANKED_A", "UNRANKED_B"]
