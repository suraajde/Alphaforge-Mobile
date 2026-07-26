from services.portfolio_breadth_decision_service import (
    PortfolioBreadthDecisionService,
    PortfolioBreadthInput,
)


def test_user_configured_size():
    service = PortfolioBreadthDecisionService()

    request = PortfolioBreadthInput(
        candidate_count=30,
        target_portfolio_size=15,
    )

    result = service.recommend(request)

    assert result.recommended_size == 15
    assert result.confidence == 1.0

    print("PASS - User configured portfolio size")


def test_automatic_size():
    service = PortfolioBreadthDecisionService()

    request = PortfolioBreadthInput(
        candidate_count=12,
    )

    result = service.recommend(request)

    assert result.recommended_size == 12

    print("PASS - Automatic portfolio size")


def test_minimum_size():
    service = PortfolioBreadthDecisionService()

    request = PortfolioBreadthInput(
        candidate_count=3,
    )

    result = service.recommend(request)

    assert result.recommended_size == 8

    print("PASS - Minimum portfolio size enforced")


def test_maximum_size():
    service = PortfolioBreadthDecisionService()

    request = PortfolioBreadthInput(
        candidate_count=45,
    )

    result = service.recommend(request)

    assert result.recommended_size == 20

    print("PASS - Maximum portfolio size enforced")


if __name__ == "__main__":
    test_user_configured_size()
    test_automatic_size()
    test_minimum_size()
    test_maximum_size()

    print("\nSprint 12.1.0 - Portfolio Breadth Decision Service PASSED")