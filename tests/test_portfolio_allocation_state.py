from services.portfolio_state_service import (
    PortfolioStateService,
)


def run_tests():

    service = PortfolioStateService()

    cases = [
        (
            9.0,
            6.5,
            "UNDER_TARGET",
        ),
        (
            9.0,
            8.2,
            "NEAR_TARGET",
        ),
        (
            9.0,
            9.6,
            "NEAR_TARGET",
        ),
        (
            9.0,
            12.0,
            "ABOVE_TARGET",
        ),
    ]

    for (
        target,
        actual,
        expected,
    ) in cases:

        result = service._allocation_state(
            target,
            actual,
        )

        print(
            f"target={target:.1f}% "
            f"actual={actual:.1f}% "
            f"=> {result}"
        )

        assert result == expected

    # ------------------------------------------
    # LOW-CHURN STRONG-RUNNER DOCTRINE
    #
    # Weight drift alone is descriptive.
    # ABOVE_TARGET must not encode a trade action.
    # ------------------------------------------

    runner_state = (
        service._allocation_state(
            9.0,
            12.0,
        )
    )

    assert (
        runner_state
        == "ABOVE_TARGET"
    )

    forbidden_actions = (
        "SELL",
        "TRIM",
        "EXIT",
        "REBALANCE",
    )

    for action in forbidden_actions:

        assert (
            action
            not in runner_state
        )

    # ------------------------------------------
    # TOLERANCE BOUNDARY
    #
    # Exactly +/-1 percentage point remains
    # NEAR_TARGET. Only meaningful drift outside
    # the band changes allocation state.
    # ------------------------------------------

    assert (
        service._allocation_state(
            9.0,
            8.0,
        )
        == "NEAR_TARGET"
    )

    assert (
        service._allocation_state(
            9.0,
            10.0,
        )
        == "NEAR_TARGET"
    )

    assert (
        service._allocation_state(
            9.0,
            7.99,
        )
        == "UNDER_TARGET"
    )

    assert (
        service._allocation_state(
            9.0,
            10.01,
        )
        == "ABOVE_TARGET"
    )

    print()
    print(
        "Sprint 11.5B.1 allocation-state doctrine: PASS"
    )


if __name__ == "__main__":
    run_tests()
