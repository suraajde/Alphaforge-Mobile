import shutil
import tempfile
from pathlib import Path
import pytest

from services.alert_center_service import AlertCenterService, PortfolioAlert
from services.alert_management_service import (
    AlertManagementResult,
    AlertManagementService,
    AlertManagementSummary,
)


@pytest.fixture
def custom_tmp_dir():
    scratch_dir = Path("d:/ALPHAFORGE/scratch")
    scratch_dir.mkdir(exist_ok=True, parents=True)
    temp_dir = tempfile.mkdtemp(dir=scratch_dir)
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_alert_management_service_instantiation():
    service = AlertManagementService()
    assert service is not None


def test_get_management_result_empty(custom_tmp_dir):
    storage_file = str(custom_tmp_dir / "alerts.json")
    ac_svc = AlertCenterService(storage_path=storage_file)
    mgmt_svc = AlertManagementService(alert_center_service=ac_svc)

    result = mgmt_svc.get_management_result()
    assert isinstance(result, AlertManagementResult)
    assert result.summary.total_alerts == 0
    assert result.summary.active_alerts == 0
    assert result.summary.acknowledged_alerts == 0
    assert result.summary.dismissed_alerts == 0
    assert result.summary.last_updated is None
    assert result.alerts == []


def test_get_management_summary_and_alerts(custom_tmp_dir):
    storage_file = str(custom_tmp_dir / "alerts.json")
    ac_svc = AlertCenterService(storage_path=storage_file)
    alert1 = PortfolioAlert(
        alert_id="a1",
        timestamp="2026-08-07 10:00",
        alert_type="VOLATILITY",
        severity="HIGH",
        title="High Volatility",
        description="Volatility spiked",
        status="ACTIVE",
    )
    alert2 = PortfolioAlert(
        alert_id="a2",
        timestamp="2026-08-07 11:00",
        alert_type="DRAWDOWN",
        severity="MEDIUM",
        title="Drawdown Alert",
        description="Drawdown > 5%",
        status="ACKNOWLEDGED",
    )
    ac_svc.save_alerts([alert1, alert2])

    mgmt_svc = AlertManagementService(alert_center_service=ac_svc)
    summary = mgmt_svc.get_management_summary()
    assert summary.total_alerts == 2
    assert summary.active_alerts == 1
    assert summary.acknowledged_alerts == 1
    assert summary.dismissed_alerts == 0
    assert summary.last_updated is not None

    alerts = mgmt_svc.get_alerts()
    assert len(alerts) == 2
    assert alerts[0].alert_id == "a1"


def test_acknowledge_alert_state_transition(custom_tmp_dir):
    storage_file = str(custom_tmp_dir / "alerts.json")
    ac_svc = AlertCenterService(storage_path=storage_file)
    alert1 = PortfolioAlert(
        alert_id="a1",
        timestamp="2026-08-07 10:00",
        alert_type="VOLATILITY",
        severity="HIGH",
        title="High Volatility",
        description="Volatility spiked",
        status="ACTIVE",
    )
    ac_svc.save_alerts([alert1])

    mgmt_svc = AlertManagementService(alert_center_service=ac_svc)
    result = mgmt_svc.acknowledge_alert("a1")
    assert result.summary.active_alerts == 0
    assert result.summary.acknowledged_alerts == 1
    assert result.alerts[0].status == "ACKNOWLEDGED"

    # Re-acknowledging should not change state
    result2 = mgmt_svc.acknowledge_alert("a1")
    assert result2.summary.acknowledged_alerts == 1


def test_dismiss_alert_state_transition(custom_tmp_dir):
    storage_file = str(custom_tmp_dir / "alerts.json")
    ac_svc = AlertCenterService(storage_path=storage_file)
    alert1 = PortfolioAlert(
        alert_id="a1",
        timestamp="2026-08-07 10:00",
        alert_type="VOLATILITY",
        severity="HIGH",
        title="High Volatility",
        description="Volatility spiked",
        status="ACTIVE",
    )
    alert2 = PortfolioAlert(
        alert_id="a2",
        timestamp="2026-08-07 11:00",
        alert_type="DRAWDOWN",
        severity="MEDIUM",
        title="Drawdown Alert",
        description="Drawdown > 5%",
        status="ACKNOWLEDGED",
    )
    ac_svc.save_alerts([alert1, alert2])

    mgmt_svc = AlertManagementService(alert_center_service=ac_svc)
    
    # ACTIVE -> DISMISSED
    result = mgmt_svc.dismiss_alert("a1")
    assert result.summary.dismissed_alerts == 1
    assert result.summary.active_alerts == 0
    
    # ACKNOWLEDGED -> DISMISSED
    result2 = mgmt_svc.dismiss_alert("a2")
    assert result2.summary.dismissed_alerts == 2
    assert result2.summary.acknowledged_alerts == 0


def test_defensive_error_handling():
    class FaultyAlertCenterService:
        def load_alerts(self):
            raise RuntimeError("Database connection failed")

    faulty_svc = FaultyAlertCenterService()
    mgmt_svc = AlertManagementService(alert_center_service=faulty_svc)

    result = mgmt_svc.get_management_result()
    assert result.summary.total_alerts == 0
    assert result.alerts == []

    ack_result = mgmt_svc.acknowledge_alert("a1")
    assert ack_result.summary.total_alerts == 0

    dismiss_result = mgmt_svc.dismiss_alert("a1")
    assert dismiss_result.summary.total_alerts == 0
