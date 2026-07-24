from services.production_radar_pipeline import (
    ProductionRadarPipeline,
)


def run_tests():

    # ======================================================
    # DEFAULT CONTRACT
    #
    # Existing production behavior must remain unchanged:
    #
    # Research Radar = 30
    # Alpha portfolio = 12
    # Reserves = 8
    # ======================================================

    default_pipeline = (
        ProductionRadarPipeline()
    )

    assert (
        default_pipeline.radar_limit
        == 30
    ), (
        "Default Research Radar breadth changed"
    )

    assert (
        default_pipeline.alpha_target_count
        == 12
    ), (
        "Default Alpha portfolio breadth changed"
    )

    assert (
        default_pipeline.alpha_reserve_count
        == 8
    ), (
        "Default Alpha reserve breadth changed"
    )

    print(
        "Default breadth contract:",
        "Radar 30 / Alpha 12 / Reserves 8 => PASS",
    )

    # ======================================================
    # 15-STOCK FLEXIBILITY
    # ======================================================

    alpha15_pipeline = (
        ProductionRadarPipeline(
            radar_limit=40,
            alpha_target_count=15,
            alpha_reserve_count=10,
        )
    )

    assert (
        alpha15_pipeline.radar_limit
        == 40
    )

    assert (
        alpha15_pipeline.alpha_target_count
        == 15
    )

    assert (
        alpha15_pipeline.alpha_reserve_count
        == 10
    )

    print(
        "Expanded breadth contract:",
        "Radar 40 / Alpha 15 / Reserves 10 => PASS",
    )

    # ======================================================
    # 17-STOCK FLEXIBILITY
    # ======================================================

    alpha17_pipeline = (
        ProductionRadarPipeline(
            radar_limit=50,
            alpha_target_count=17,
            alpha_reserve_count=12,
        )
    )

    assert (
        alpha17_pipeline.radar_limit
        == 50
    )

    assert (
        alpha17_pipeline.alpha_target_count
        == 17
    )

    assert (
        alpha17_pipeline.alpha_reserve_count
        == 12
    )

    print(
        "Expanded breadth contract:",
        "Radar 50 / Alpha 17 / Reserves 12 => PASS",
    )

    # ======================================================
    # LOWER-BOUND SAFETY
    # ======================================================

    bounded_pipeline = (
        ProductionRadarPipeline(
            radar_limit=0,
            alpha_target_count=0,
            alpha_reserve_count=-5,
        )
    )

    assert (
        bounded_pipeline.radar_limit
        == 1
    )

    assert (
        bounded_pipeline.alpha_target_count
        == 1
    )

    assert (
        bounded_pipeline.alpha_reserve_count
        == 0
    )

    print(
        "Breadth lower-bound safety:",
        "PASS",
    )

    print()
    print(
        "Sprint 11.5B.3A configurable "
        "portfolio breadth foundation: PASS"
    )


if __name__ == "__main__":
    run_tests()
