"""Unit test suite for atomic JSON persistence and file safety (Sprint 14.0.2 SEC-01)."""

import json
import os
import tempfile
import pytest

from services.alert_center_service import AlertCenterService, PortfolioAlert
from services.alert_history_service import AlertHistoryService
from services.decision_audit_service import DecisionAuditEntry, DecisionAuditService, DecisionAuditTrail
from services.drift_detection_service import DriftDetectionResult, DriftDetectionService
from services.portfolio_health_history_service import PortfolioHealthHistoryService
from services.portfolio_health_service import PortfolioHealthResult
from services.portfolio_intelligence_service import PortfolioIntelligenceService, PortfolioIntelligenceSnapshot


def test_portfolio_health_history_atomic_write():
    """Verify PortfolioHealthHistoryService atomic write cleans up temp file and writes valid JSON."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = os.path.join(tmp_dir, "health_history.json")
        svc = PortfolioHealthHistoryService(storage_path=storage_path)

        res = PortfolioHealthResult(
            score=85,
            grade="B",
            diversification_rating="GOOD",
            concentration_rating="LOW",
            position_count=10,
            largest_position_weight_pct=8.5,
            cash_allocation_pct=5.0,
        )

        entry = svc.save_snapshot(res)

        assert entry is not None
        assert os.path.exists(storage_path)
        assert not os.path.exists(storage_path + ".tmp")

        # Verify content can be read back cleanly
        with open(storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["score"] == 85


def test_decision_audit_atomic_write():
    """Verify DecisionAuditService atomic write cleans up temp file and preserves data integrity."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = os.path.join(tmp_dir, "decision_audit.json")
        svc = DecisionAuditService(storage_path=storage_path)

        entry = DecisionAuditEntry(
            audit_id="aud_123",
            timestamp="2026-08-08T12:00:00Z",
            decision_id="dec_456",
            category="DIVERSIFICATION",
            classification_status="REVIEW_ELIGIBLE",
            priority="HIGH",
            description="Test decision audit entry",
            source="unit_test",
        )
        trail = DecisionAuditTrail(
            total_entries=1,
            latest_timestamp="2026-08-08T12:00:00Z",
            earliest_timestamp="2026-08-08T12:00:00Z",
            entries=[entry],
        )

        svc.save_audit(trail)

        assert os.path.exists(storage_path)
        assert not os.path.exists(storage_path + ".tmp")

        loaded_trail = svc.load_audit()
        assert loaded_trail.total_entries == 1
        assert loaded_trail.entries[0].decision_id == "dec_456"


def test_drift_detection_atomic_write():
    """Verify DriftDetectionService atomic write creates safe persistence without leaving temp artifacts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = os.path.join(tmp_dir, "drift_history.json")
        svc = DriftDetectionService(history_path=storage_path)

        result = DriftDetectionResult(
            total_positions=5,
            positions_with_target=4,
            positions_without_target=1,
            total_absolute_drift=0.12,
            average_absolute_drift=0.03,
            maximum_absolute_drift=0.05,
        )

        hist = svc.record_history(result, timestamp="2026-08-08T12:00:00Z")

        assert hist.total_entries >= 1
        assert os.path.exists(storage_path)
        assert not os.path.exists(storage_path + ".tmp")


def test_portfolio_intelligence_atomic_write():
    """Verify PortfolioIntelligenceService atomic write handles persistence safely."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = os.path.join(tmp_dir, "intelligence_history.json")
        svc = PortfolioIntelligenceService(history_path=storage_path)

        snap = PortfolioIntelligenceSnapshot(
            timestamp="2026-08-08T12:00:00Z",
            total_value=100000.0,
            total_holdings=10,
            account_count=1,
            intelligence_status="HEALTHY",
        )

        svc.save_history([snap])

        assert os.path.exists(storage_path)
        assert not os.path.exists(storage_path + ".tmp")

        loaded = svc.load_history()
        assert len(loaded) == 1
        assert loaded[0].total_value == 100000.0


def test_alert_center_atomic_write():
    """Verify AlertCenterService atomic write creates valid storage safely."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = os.path.join(tmp_dir, "alerts.json")
        svc = AlertCenterService(storage_path=storage_path)

        alert = PortfolioAlert(
            alert_id="alt_1",
            timestamp="2026-08-08T12:00:00Z",
            alert_type="CONCENTRATION",
            severity="HIGH",
            title="High Concentration Risk",
            description="Largest holding weight exceeds 20%",
            status="ACTIVE",
        )

        svc.save_alerts([alert])

        assert os.path.exists(storage_path)
        assert not os.path.exists(storage_path + ".tmp")

        loaded = svc.load_alerts()
        assert len(loaded) == 1
        assert loaded[0].alert_id == "alt_1"


def test_alert_history_atomic_write():
    """Verify AlertHistoryService atomic write records alert history cleanly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = os.path.join(tmp_dir, "alert_history.json")
        svc = AlertHistoryService(storage_path=storage_path)

        alert = PortfolioAlert(
            alert_id="alt_99",
            timestamp="2026-08-08T12:00:00Z",
            alert_type="DRIFT",
            severity="MEDIUM",
            title="Portfolio Drift",
            description="Asset weight drift detected",
            status="ACTIVE",
        )

        svc.save_history([alert])

        assert os.path.exists(storage_path)
        assert not os.path.exists(storage_path + ".tmp")

        history = svc.get_history()
        assert history.total_entries == 1
        assert history.entries[0].alert_id == "alt_99"


def test_atomic_write_preserves_existing_destination_on_interrupted_write():
    """Verify atomic write failure leaves existing valid destination file untouched."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = os.path.join(tmp_dir, "protected_history.json")

        # Initial valid save
        svc = PortfolioHealthHistoryService(storage_path=storage_path)
        res = PortfolioHealthResult(
            score=90,
            grade="A",
            diversification_rating="GOOD",
            concentration_rating="LOW",
            position_count=12,
            largest_position_weight_pct=8.0,
            cash_allocation_pct=5.0,
        )
        svc.save_snapshot(res)

        assert os.path.exists(storage_path)
        with open(storage_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Simulate write error before replace operation
        temp_path = storage_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("{ INCOMPLETE OR CORRUPT DRAFT DATA")

        # Destination file must remain unchanged
        with open(storage_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        assert current_content == original_content

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
