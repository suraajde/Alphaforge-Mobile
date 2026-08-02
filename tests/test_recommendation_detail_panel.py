import os
import pytest
from PySide6.QtWidgets import QApplication

from app.widgets.recommendation_detail_panel import RecommendationDetailPanel
from services.recommendation_models import Recommendation


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_load_recommendation_from_dict(qapp):
    panel = RecommendationDetailPanel()
    data = {
        "title": "Deploy available cash",
        "priority": "HIGH",
        "confidence": 95,
        "score": 92,
        "suggested_action": "Deploy 50% cash gradually",
        "reasons": ["Reason 1", "Reason 2"],
    }
    panel.load_recommendation(data)

    assert panel.title_value.text() == "Deploy available cash"
    assert panel.priority_value.text() == "HIGH"
    assert panel.confidence_value.text() == "95"
    assert panel.score_value.text() == "92"
    assert panel.suggested_action_value.text() == "Deploy 50% cash gradually"
    assert "• Reason 1\n• Reason 2" in panel.reasons_value.text()


def test_load_recommendation_from_object(qapp):
    panel = RecommendationDetailPanel()
    rec = Recommendation(
        category="Risk",
        priority="CRITICAL",
        action="REDUCE",
        confidence=98,
        target="Portfolio",
        title="High Concentration Risk",
        reasons=["Top 3 weight > 50%"],
        suggested_action="Reduce top holdings",
        score=99,
    )
    panel.load_recommendation(rec)

    assert panel.title_value.text() == "High Concentration Risk"
    assert panel.priority_value.text() == "CRITICAL"
    assert panel.confidence_value.text() == "98"
    assert panel.score_value.text() == "99"
    assert panel.suggested_action_value.text() == "Reduce top holdings"
    assert "• Top 3 weight > 50%" in panel.reasons_value.text()


def test_load_recommendation_clear_on_invalid(qapp):
    panel = RecommendationDetailPanel()
    panel.load_recommendation(None)
    assert panel.title_value.text() == "-"
    assert panel.priority_value.text() == "-"
    assert panel.confidence_value.text() == "-"
    assert panel.score_value.text() == "-"
    assert panel.suggested_action_value.text() == "-"
    assert panel.reasons_value.text() == "-"
