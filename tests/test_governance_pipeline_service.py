import pytest

from models.governance_action import GovernanceAction
from models.governance_severity import GovernanceSeverity
from services.governance_pipeline_service import GovernancePipelineService


def test_empty_observation_handling():
    service = GovernancePipelineService()

    # None input
    actions_none = service.generate_actions(None)
    assert actions_none == []

    # Empty list input
    actions_empty = service.generate_actions([])
    assert actions_empty == []

    # Invalid list elements
    actions_invalid = service.generate_actions(["not_a_dict", 123])
    assert actions_invalid == []


def test_sector_concentration_action_creation():
    service = GovernancePipelineService()

    observations = [
        {
            "type": "sector_concentration",
            "sector": "Technology",
            "exposure_pct": 35.0,
            "limit_pct": 30.0,
            "severity": "WARNING",
        }
    ]

    actions = service.generate_actions(observations)

    assert len(actions) == 1
    action = actions[0]

    assert isinstance(action, GovernanceAction)
    assert action.title == "Sector Concentration: Technology"
    assert "Technology" in action.description
    assert "35.0%" in action.description
    assert action.severity == GovernanceSeverity.WARNING
    assert "Trim positions in Technology" in action.recommendation


def test_position_concentration_action_creation():
    service = GovernancePipelineService()

    observations = [
        {
            "type": "position_concentration",
            "symbol": "INFY",
            "weight_pct": 28.5,
            "limit_pct": 25.0,
            "severity": "CRITICAL",
        }
    ]

    actions = service.generate_actions(observations)

    assert len(actions) == 1
    action = actions[0]

    assert isinstance(action, GovernanceAction)
    assert action.title == "Position Concentration: INFY"
    assert "INFY" in action.description
    assert "28.5%" in action.description
    assert action.severity == GovernanceSeverity.CRITICAL
    assert "Rebalance 'INFY'" in action.recommendation


def test_custom_fields_observation():
    service = GovernancePipelineService()

    observations = [
        {
            "type": "custom_metric",
            "title": "Custom Alert",
            "description": "Custom Description Text",
            "recommendation": "Custom Action Recommended",
            "severity": "INFO",
        }
    ]

    actions = service.generate_actions(observations)

    assert len(actions) == 1
    action = actions[0]

    assert action.title == "Custom Alert"
    assert action.description == "Custom Description Text"
    assert action.severity == GovernanceSeverity.INFO
    assert action.recommendation == "Custom Action Recommended"
