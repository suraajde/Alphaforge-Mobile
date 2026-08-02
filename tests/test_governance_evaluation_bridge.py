import pytest
from PySide6.QtWidgets import QApplication

from app.screens.portfolio_action_center import PortfolioActionCenter
from models.governance_action import GovernanceAction
from models.governance_severity import GovernanceSeverity
from services.action_center_service import ActionCenterService
from services.governance_pipeline_service import GovernancePipelineService
from services.portfolio_governance_service import GovernanceEvaluation


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_governance_evaluation_conversion():
    pipeline_service = GovernancePipelineService()

    evaluations = [
        GovernanceEvaluation(
            current_symbol="INFY", candidate_symbol="TCS", decision="HOLD",
            current_score=70.0, candidate_score=75.0, score_delta=5.0,
            is_cooling_active=False, holding_days=40,
            reasons=["Score advantage below minimum threshold (10.0 pts)."],
            replacement_justification="Hold INFY: Candidate score does not offer sufficient advantage.",
        ),
        GovernanceEvaluation(
            current_symbol="HDFCBANK", candidate_symbol="ICICIBANK", decision="REVIEW",
            current_score=72.0, candidate_score=85.0, score_delta=13.0,
            is_cooling_active=True, holding_days=15, sector_guardrail_breached=True,
            reasons=["Cooling period active (15/30 days held)."],
            replacement_justification="Review HDFCBANK -> ICICIBANK: Active cooling period.",
        ),
        GovernanceEvaluation(
            current_symbol="WIPRO", candidate_symbol="LTIM", decision="REPLACE",
            current_score=60.0, candidate_score=90.0, score_delta=30.0,
            is_cooling_active=False, holding_days=45,
            reasons=["Score advantage satisfies threshold."],
            replacement_justification="Replace WIPRO with LTIM: Score improvement of +30.0 pts.",
        ),
    ]

    actions = pipeline_service.generate_actions_from_evaluations(evaluations)

    assert len(actions) == 3

    # Check HOLD -> INFO mapping
    act_hold = actions[0]
    assert isinstance(act_hold, GovernanceAction)
    assert act_hold.severity == GovernanceSeverity.INFO
    assert "Governance HOLD: INFY -> TCS" in act_hold.title

    # Check REVIEW -> WARNING mapping
    act_review = actions[1]
    assert act_review.severity == GovernanceSeverity.WARNING
    assert "Governance REVIEW: HDFCBANK -> ICICIBANK" in act_review.title
    assert "[Sector Guardrail Breached]" in act_review.description

    # Check REPLACE -> WATCH mapping
    act_replace = actions[2]
    assert act_replace.severity == GovernanceSeverity.WATCH
    assert "Governance REPLACE: WIPRO -> LTIM" in act_replace.title


def test_action_center_service_integration_with_evaluations():
    service = ActionCenterService()

    evaluations = [
        GovernanceEvaluation(
            current_symbol="RELIANCE", candidate_symbol="ONGC", decision="REVIEW",
            current_score=65.0, candidate_score=80.0, score_delta=15.0,
            is_cooling_active=True, holding_days=10,
            reasons=["Cooling period active (10/30 days held)."],
            replacement_justification="Review RELIANCE -> ONGC.",
        )
    ]

    vm = service.build_view_model(plan=None, evaluations=evaluations, review_date="2026-08-02")

    assert len(vm.governance_pipeline_actions) == 1
    gov_action = vm.governance_pipeline_actions[0]
    assert gov_action.severity == GovernanceSeverity.WARNING
    assert "RELIANCE" in gov_action.title

    assert vm.summary.deferred_action_count == 1
    assert len(vm.deferred_actions) == 1
    def_item = vm.deferred_actions[0]
    assert def_item.action == "WARNING"
    assert "RELIANCE" in def_item.current_holding


def test_ui_renders_evaluation_driven_content(qapp):
    screen = PortfolioActionCenter()

    evaluations = [
        GovernanceEvaluation(
            current_symbol="HDFCBANK", candidate_symbol="ICICIBANK", decision="REVIEW",
            current_score=72.0, candidate_score=85.0, score_delta=13.0,
            is_cooling_active=True, holding_days=15,
            reasons=["Cooling period active (15/30 days held)."],
            replacement_justification="Review HDFCBANK -> ICICIBANK.",
        )
    ]

    # Render via service
    vm = screen.service.build_view_model(plan=None, evaluations=evaluations, review_date="2026-08-02")
    screen.lbl_review_date_val.setText(vm.summary.review_date)
    screen.lbl_deferred_count_val.setText(str(vm.summary.deferred_action_count))

    assert screen.lbl_review_date_val.text() == "2026-08-02"
    assert screen.lbl_deferred_count_val.text() == "1"
