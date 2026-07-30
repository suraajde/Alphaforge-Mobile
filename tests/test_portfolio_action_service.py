import pytest

from services.portfolio_action_service import PortfolioActionService
from services.recommendation_models import Recommendation, RecommendationReport


def make_rec(action: str, target: str, score: int, confidence: int, title: str = "t") -> Recommendation:
    return Recommendation(
        category="test",
        priority="medium",
        action=action,
        confidence=confidence,
        target=target,
        title=title,
        reasons=["r1", "r2"],
        suggested_action="do something",
        score=score,
    )


def test_mapping_and_sorting():
    svc = PortfolioActionService()

    # Create recommendations across actions with varying scores/confidence
    recs = [
        make_rec("BUY", "AAPL", 90, 80, title="Buy AAPL"),
        make_rec("INCREASE", "MSFT", 85, 90, title="Increase MSFT"),
        make_rec("REDUCE", "GOOG", 70, 60, title="Reduce GOOG"),
        make_rec("SELL", "TSLA", 95, 50, title="Sell TSLA"),
        make_rec("HOLD", "AMZN", 50, 40, title="Hold AMZN"),
        make_rec("WATCH", "NFLX", 30, 20, title="Watch NFLX"),
        make_rec("MONITOR", "FB", 20, 30, title="Monitor FB"),
    ]

    report = RecommendationReport()
    report.portfolio_recommendations = recs[:2]
    report.holding_recommendations = recs[2:4]
    report.risk_recommendations = recs[4:5]
    report.cash_recommendations = recs[5:6]
    report.monitoring_recommendations = recs[6:7]

    out = svc.build_actions(report)

    # Contract keys
    assert set(out.keys()) == {"status", "buy", "reduce", "hold", "watch"}
    assert out["status"] == "OK"

    # BUYS should contain AAPL and MSFT and be sorted by score desc then confidence
    buy_targets = [i["target"] for i in out["buy"]]
    assert buy_targets == ["AAPL", "MSFT"]

    # REDUCE should contain TSLA and GOOG sorted by score desc
    reduce_targets = [i["target"] for i in out["reduce"]]
    assert reduce_targets == ["TSLA", "GOOG"]

    # HOLD
    assert [i["target"] for i in out["hold"]] == ["AMZN"]

    # WATCH contains NFLX and FB
    assert set([i["target"] for i in out["watch"]]) == {"NFLX", "FB"}

    # Ensure structure of an item
    sample = out["buy"][0]
    assert set(sample.keys()) == {"target", "title", "priority", "confidence", "score", "reasons", "suggested_action"}


def test_unknown_action_goes_to_watch():
    svc = PortfolioActionService()
    rec = make_rec("UNKNOWN_ACTION", "XYZ", 10, 5)
    report = RecommendationReport()
    report.portfolio_recommendations = [rec]

    out = svc.build_actions(report)
    assert out["watch"][0]["target"] == "XYZ"


def test_invalid_report_type_raises():
    svc = PortfolioActionService()
    with pytest.raises(TypeError):
        svc.build_actions({})
