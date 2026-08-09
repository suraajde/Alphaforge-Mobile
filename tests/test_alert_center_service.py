import json
import shutil
import tempfile
from pathlib import Path
import pytest

from services.alert_center_service import (
    AlertCenterService,
    AlertCenterState,
    PortfolioAlert,
)


@pytest.fixture
def custom_tmp_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_service_instantiation():
    """Verify AlertCenterService instantiation."""
    service = AlertCenterService()
    assert service is not None


def test_load_empty_alerts(custom_tmp_dir):
    """Verify loading from empty alerts storage."""
    file_path = str(custom_tmp_dir / "portfolio_alerts.json")
    service = AlertCenterService(storage_path=file_path)

    alerts = service.load_alerts()
    assert alerts == []


def test_save_and_load_alerts(custom_tmp_dir):
    """Verify saving and reloading alerts."""
    file_path = str(custom_tmp_dir / "portfolio_alerts.json")
    service = AlertCenterService(storage_path=file_path)

    alert1 = PortfolioAlert(
        alert_id="a1",
        timestamp="2026-08-08",
        alert_type="CONCENTRATION",
        severity="HIGH",
        title="Portfolio concentration increased",
        description="High weight on Reliance",
        status="ACTIVE",
    )
    alert2 = PortfolioAlert(
        alert_id="a2",
        timestamp="2026-08-06",
        alert_type="CASH_ALLOCATION",
        severity="LOW",
        title="Cash allocation changed",
        description="Cash reduced to 5%",
        status="ACKNOWLEDGED",
    )

    service.save_alerts([alert1, alert2])

    loaded = service.load_alerts()
    assert len(loaded) == 2
    assert loaded[0].alert_id == "a1"
    assert loaded[0].severity == "HIGH"
    assert loaded[0].status == "ACTIVE"
    assert loaded[1].alert_id == "a2"
    assert loaded[1].status == "ACKNOWLEDGED"


def test_missing_file_safety(custom_tmp_dir):
    """Verify missing storage file handling safety."""
    file_path = str(custom_tmp_dir / "nonexistent" / "portfolio_alerts.json")
    service = AlertCenterService(storage_path=file_path)

    state = service.get_state()
    assert state.total_alerts == 0
    assert state.active_alerts == 0
    assert state.acknowledged_alerts == 0
    assert state.dismissed_alerts == 0
    assert state.alerts == []


def test_corrupt_json_safety(custom_tmp_dir):
    """Verify corrupt JSON handling safety."""
    corrupt_file = custom_tmp_dir / "corrupt.json"
    corrupt_file.write_text("INVALID_JSON{", encoding="utf-8")

    service = AlertCenterService(storage_path=str(corrupt_file))
    state = service.get_state()

    assert state.total_alerts == 0
    assert state.active_alerts == 0
    assert state.acknowledged_alerts == 0
    assert state.dismissed_alerts == 0
    assert state.alerts == []


def test_state_calculations(custom_tmp_dir):
    """Verify state counters calculations (total, active, acknowledged, dismissed)."""
    file_path = str(custom_tmp_dir / "portfolio_alerts.json")
    service = AlertCenterService(storage_path=file_path)

    alerts = [
        PortfolioAlert("1", "ts1", "T1", "HIGH", "Title 1", "Desc 1", "ACTIVE"),
        PortfolioAlert("2", "ts2", "T2", "MEDIUM", "Title 2", "Desc 2", "ACTIVE"),
        PortfolioAlert("3", "ts3", "T3", "LOW", "Title 3", "Desc 3", "ACKNOWLEDGED"),
        PortfolioAlert("4", "ts4", "T4", "INFO", "Title 4", "Desc 4", "DISMISSED"),
    ]
    service.save_alerts(alerts)

    state = service.get_state()
    assert state.total_alerts == 4
    assert state.active_alerts == 2
    assert state.acknowledged_alerts == 1
    assert state.dismissed_alerts == 1
    assert len(state.alerts) == 4


def test_active_alerts_retrieval(custom_tmp_dir):
    """Verify retrieval of active alerts only."""
    file_path = str(custom_tmp_dir / "portfolio_alerts.json")
    service = AlertCenterService(storage_path=file_path)

    alerts = [
        PortfolioAlert("1", "ts1", "T1", "HIGH", "Title 1", "Desc 1", "ACTIVE"),
        PortfolioAlert("2", "ts2", "T2", "LOW", "Title 2", "Desc 2", "DISMISSED"),
    ]
    service.save_alerts(alerts)

    active = service.get_active_alerts()
    assert len(active) == 1
    assert active[0].alert_id == "1"
