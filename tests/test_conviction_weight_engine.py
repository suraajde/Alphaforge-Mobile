from services.conviction_weight_engine import (
    ConvictionWeightEngine,
    ConvictionInput,
    WeightStrategy,
)


def test_equal_weight():
    engine = ConvictionWeightEngine()

    result = engine.weight(
        ConvictionInput(score=95),
        WeightStrategy.EQUAL,
    )

    assert result == 1.0
    print("PASS - Equal Weight")


def test_linear_weight():
    engine = ConvictionWeightEngine()

    result = engine.weight(
        ConvictionInput(score=85),
        WeightStrategy.LINEAR,
    )

    assert result == 85.0
    print("PASS - Linear Weight")


def test_tiered_high():
    engine = ConvictionWeightEngine()

    result = engine.weight(
        ConvictionInput(score=92),
        WeightStrategy.TIERED,
    )

    assert result == 1.40
    print("PASS - Tiered High")


def test_tiered_medium():
    engine = ConvictionWeightEngine()

    result = engine.weight(
        ConvictionInput(score=82),
        WeightStrategy.TIERED,
    )

    assert result == 1.25
    print("PASS - Tiered Medium")


def test_tiered_low():
    engine = ConvictionWeightEngine()

    result = engine.weight(
        ConvictionInput(score=72),
        WeightStrategy.TIERED,
    )

    assert result == 1.10
    print("PASS - Tiered Low")


def test_tiered_base():
    engine = ConvictionWeightEngine()

    result = engine.weight(
        ConvictionInput(score=60),
        WeightStrategy.TIERED,
    )

    assert result == 1.00
    print("PASS - Tiered Base")


if __name__ == "__main__":
    test_equal_weight()
    test_linear_weight()
    test_tiered_high()
    test_tiered_medium()
    test_tiered_low()
    test_tiered_base()

    print()
    print("Sprint 12.2.0 - Conviction Weight Engine PASSED")