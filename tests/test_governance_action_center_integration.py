import pytest
from PySide6.QtWidgets import QApplication

from app.screens.portfolio_action_center import PortfolioActionCenter
from models.governance_action import GovernanceAction
from models.governance_severity import GovernanceSeverity
from services.action_center_service import (
    ActionCenterService,
    ActionCenterViewModel,
)
from services.governance_pipeline_service import GovernancePipelineService
from services.rebalance_orchestrator_service import RebalancePlan


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_governance_pipeline_output_reaches_action_center_service():
    pipeline_service = GovernancePipelineService()
    action_center_service = ActionCenterService(governance_pipeline=pipeline_service)

    sample_obs = [
        {
            "type": "sector_concentration",
            "sector": "Technology",
            "allocation_percent": 38.2,
            "exposure_pct": 38.2,
            "threshold": 30.0,
            "limit_pct": 30.0,
            "severity": "WARNING",
        }
    ]

    vm = action_center_service.build_view_model(plan=None, observations=sample_obs, review_date="2026-08-02")

    # Verify GovernancePipelineService output reached ActionCenterService and is stored in ActionCenterViewModel
    assert len(vm.governance_pipeline_actions) == 1
    gov_action = vm.governance_pipeline_actions[0]
    assert isinstance(gov_action, GovernanceAction)
    assert gov_action.title == "Sector Concentration: Technology"
    assert gov_action.severity == GovernanceSeverity.WARNING
    assert "38.2%" in gov_action.description


def test_action_center_viewmodel_contains_governance_content():
    action_center_service = ActionCenterService()

    sample_obs = [
        {
            "type": "position_concentration",
            "symbol": "INFY",
            "exposure_pct": 28.5,
            "weight_pct": 28.5,
            "limit_pct": 25.0,
            "severity": "CRITICAL",
        }
    ]

    vm = action_center_service.build_view_model(plan=None, observations=sample_obs)

    # Verify summary count and deferred actions contain the governance warning
    assert vm.summary.deferred_action_count == 1
    assert len(vm.deferred_actions) == 1

    def_vm = vm.deferred_actions[0]
    assert def_vm.action == "CRITICAL"
    assert def_vm.current_holding == "Position Concentration: INFY"
    assert "28.5%" in def_vm.reason
    assert "Rebalance 'INFY'" in def_vm.reason

    # Verify rationale list includes the governance alert
    assert any("Governance Alert [CRITICAL]: Position Concentration: INFY" in r for r in vm.rationale)


def test_portfolio_action_center_renders_service_generated_content(qapp):
    screen = PortfolioActionCenter()

    sample_obs = [
        {
            "type": "sector_concentration",
            "sector": "Technology",
            "exposure_pct": 38.2,
            "limit_pct": 30.0,
            "severity": "WARNING",
        }
    ]

    screen.load_plan(plan=None, observations=sample_obs, review_date="2026-08-02")

    # Verify passive UI rendering of service-generated content
    assert screen.lbl_review_date_val.text() == "2026-08-02"
    assert screen.lbl_deferred_count_val.text() == "1"
    assert screen.deferred_table.rowCount() == 1
    assert screen.deferred_table.item(0, 0).text() == "WARNING"
    assert screen.deferred_table.item(0, 1).text() == "Sector Concentration: Technology"
    assert "38.2%" in screen.deferred_table.item(0, 3).text()
