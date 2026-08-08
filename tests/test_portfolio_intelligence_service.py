"""Unit tests for Portfolio Intelligence Service (Sprint 13.8.0)."""
import json
import os
import tempfile
import pytest

from services.portfolio_intelligence_service import (
    PortfolioIntelligenceSnapshot,
    PortfolioIntelligenceSummary,
    PortfolioIntelligenceResult,
    PortfolioIntelligenceService,
    _empty_summary,
    _empty_result,
    _safe_float,
    _safe_int,
)


class DummyPortfolioSummary:
    def __init__(self, total_value=150000.0, total_positions=5, account_count=2, status="HEALTHY"):
        self.total_value = total_value
        self.total_positions = total_positions
        self.account_count = account_count
        self.status = status


class DummyPortfolioService:
    def __init__(self, summary=None):
        self._summary = summary if summary is not None else DummyPortfolioSummary()

    def get_portfolio_summary(self):
        return self._summary


@pytest.fixture
def temp_history_file():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        path = tf.name
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_portfolio_intelligence_dataclasses():
    snap = PortfolioIntelligenceSnapshot(
        timestamp="2026-08-08T00:00:00Z",
        total_value=50000.0,
        total_holdings=3,
        account_count=1,
        intelligence_status="HEALTHY",
    )
    assert snap.total_value == 50000.0
    assert snap.total_holdings == 3

    summ = PortfolioIntelligenceSummary(
        intelligence_status="HEALTHY",
        total_value=50000.0,
        total_holdings=3,
        account_count=1,
        latest_timestamp="2026-08-08T00:00:00Z",
    )
    assert summ.latest_timestamp == "2026-08-08T00:00:00Z"

    res = PortfolioIntelligenceResult(summary=summ, snapshots=[snap])
    assert len(res.snapshots) == 1
    assert res.summary.total_value == 50000.0


def test_safe_helpers():
    assert _safe_float("123.45") == 123.45
    assert _safe_float(None, 10.0) == 10.0
    assert _safe_float("invalid", 5.0) == 5.0

    assert _safe_int("42") == 42
    assert _safe_int(None, 7) == 7
    assert _safe_int("invalid", 3) == 3


def test_empty_helpers():
    es = _empty_summary("EMPTY")
    assert es.intelligence_status == "EMPTY"
    assert es.total_value == 0.0
    assert es.total_holdings == 0

    er = _empty_result("UNAVAILABLE")
    assert er.summary.intelligence_status == "UNAVAILABLE"
    assert er.snapshots == []


def test_service_init_defaults(temp_history_file):
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    assert svc._history_path == temp_history_file
    assert svc._portfolio_service is None


def test_load_portfolio_dict_input(temp_history_file):
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    data = {
        "portfolio_value": 75000.0,
        "position_count": 4,
        "account_count": 2,
        "status": "HEALTHY",
    }
    snap = svc.load_portfolio(data)
    assert snap.total_value == 75000.0
    assert snap.total_holdings == 4
    assert snap.account_count == 2
    assert snap.intelligence_status == "HEALTHY"


def test_load_portfolio_object_input(temp_history_file):
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    dummy_obj = DummyPortfolioSummary(total_value=120000.0, total_positions=6, account_count=3, status="MONITOR")
    snap = svc.load_portfolio(dummy_obj)
    assert snap.total_value == 120000.0
    assert snap.total_holdings == 6
    assert snap.account_count == 3
    assert snap.intelligence_status == "MONITOR"


def test_load_portfolio_with_injected_service(temp_history_file):
    dummy_svc = DummyPortfolioService(DummyPortfolioSummary(total_value=200000.0, total_positions=10, account_count=4))
    svc = PortfolioIntelligenceService(portfolio_service=dummy_svc, history_path=temp_history_file)
    snap = svc.load_portfolio()
    assert snap.total_value == 200000.0
    assert snap.total_holdings == 10
    assert snap.account_count == 4


def test_load_portfolio_none_input(temp_history_file):
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    # Portfolio application service fallback might return empty if not found
    snap = svc.load_portfolio(None)
    assert isinstance(snap, PortfolioIntelligenceSnapshot)
    assert snap.total_value >= 0.0


def test_build_summary_valid(temp_history_file):
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    snap = PortfolioIntelligenceSnapshot(
        timestamp="2026-08-08T12:00:00Z",
        total_value=88000.0,
        total_holdings=5,
        account_count=2,
        intelligence_status="HEALTHY",
    )
    summ = svc.build_summary(snap)
    assert summ.intelligence_status == "HEALTHY"
    assert summ.total_value == 88000.0
    assert summ.latest_timestamp == "2026-08-08T12:00:00Z"


def test_build_summary_none(temp_history_file):
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    summ = svc.build_summary(None)
    assert summ.intelligence_status == "EMPTY"
    assert summ.total_value == 0.0


def test_history_save_and_load_roundtrip(temp_history_file):
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    snaps = [
        PortfolioIntelligenceSnapshot("2026-08-08T01:00:00Z", 1000.0, 1, 1, "HEALTHY"),
        PortfolioIntelligenceSnapshot("2026-08-08T02:00:00Z", 2000.0, 2, 1, "HEALTHY"),
    ]
    svc.save_history(snaps)
    loaded = svc.load_history()
    assert len(loaded) == 2
    assert loaded[0].timestamp == "2026-08-08T01:00:00Z"
    assert loaded[1].total_value == 2000.0


def test_record_snapshot_prevents_duplicates(temp_history_file):
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    snap = PortfolioIntelligenceSnapshot("2026-08-08T05:00:00Z", 5000.0, 2, 1, "HEALTHY")
    svc.record_snapshot(snap)
    svc.record_snapshot(snap)
    loaded = svc.get_history()
    assert len(loaded) == 1


def test_load_history_nonexistent_file():
    svc = PortfolioIntelligenceService(history_path="/nonexistent/path/history.json")
    loaded = svc.load_history()
    assert loaded == []


def test_load_history_corrupt_file(temp_history_file):
    with open(temp_history_file, "w", encoding="utf-8") as fh:
        fh.write("invalid json content {{{")
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    loaded = svc.load_history()
    assert loaded == []


def test_load_history_invalid_dict_structure(temp_history_file):
    with open(temp_history_file, "w", encoding="utf-8") as fh:
        json.dump(["not", "a", "dict"], fh)
    svc = PortfolioIntelligenceService(history_path=temp_history_file)
    loaded = svc.load_history()
    assert loaded == []


def test_get_intelligence_full_flow(temp_history_file):
    dummy_svc = DummyPortfolioService(DummyPortfolioSummary(total_value=300000.0, total_positions=12, account_count=5))
    svc = PortfolioIntelligenceService(portfolio_service=dummy_svc, history_path=temp_history_file)
    res = svc.get_intelligence()
    assert isinstance(res, PortfolioIntelligenceResult)
    assert res.summary.total_value == 300000.0
    assert res.summary.total_holdings == 12
    assert res.summary.account_count == 5
    assert len(res.snapshots) >= 1
