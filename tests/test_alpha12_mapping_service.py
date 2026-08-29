"""Unit tests for Alpha 12 Portfolio Mapping Service."""
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


def test_analyze_mapping_against_active_universe(tmp_path):
    """TEST 3: Verify analyze maps portfolio holdings against active universe symbols."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    alpha12_source = [{"symbol": "RELIANCE"}, {"symbol": "UNKNOWN_STOCK"}]
    portfolio_state = {"positions": {"RELIANCE": {"actual_weight": 50.0}}}

    result = service.analyze(alpha12_input=alpha12_source, state_input=portfolio_state)
    assert result.analysis_status == "ANALYZED"

    port = result.portfolio
    assert port.total_alpha12_holdings == 2
    assert port.mapped_holdings == 1
    assert port.unmapped_holdings == 1
    assert port.mapping_coverage_pct == 50.0


def test_symbol_normalization(tmp_path):
    """TEST 4: Verify symbol normalization handles suffix and casing cleanly."""
    service = Alpha12MappingService()
    assert service._normalize_symbol(" tcs.ns ") == "TCS"
    assert service._normalize_symbol("hdfcbank.bo") == "HDFCBANK"


def test_empty_portfolio(tmp_path):
    """TEST 5: Verify analyzing empty alpha12 source produces NO_DATA status safely."""
    storage_file = tmp_path / "alpha12_history.json"
    service = Alpha12MappingService(storage_path=storage_file)

    result = service.analyze(alpha12_input=[])
    assert result.analysis_status == "NO_DATA"
    assert result.portfolio.mapping_status == "EMPTY"


def test_load_all_universe_symbols():
    """TEST 6: Verify _load_all_universe_symbols returns universe constituent list."""
    service = Alpha12MappingService()
    symbols = service._load_all_universe_symbols()
    assert isinstance(symbols, list)
    assert len(symbols) > 0


def test_corrupt_persistence_file(tmp_path):
    """TEST 7: Verify corrupt JSON history file handles safely."""
    corrupt_file = tmp_path / "corrupt_history.json"
    corrupt_file.write_text("{invalid json content", encoding="utf-8")
    service = Alpha12MappingService(storage_path=corrupt_file)

    history = service.load_history()
    assert history == []


def test_empty_persistence_file(tmp_path):
    """TEST 8: Verify empty history file handles safely."""
    empty_file = tmp_path / "empty_history.json"
    empty_file.write_text("", encoding="utf-8")
    service = Alpha12MappingService(storage_path=empty_file)

    history = service.load_history()
    assert history == []


def test_duplicate_timestamp_prevention(tmp_path):
    """TEST 9: Verify duplicate timestamp recording is prevented."""
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
