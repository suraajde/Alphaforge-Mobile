from pathlib import Path


def run_tests():

    project_root = (
        Path(__file__).resolve().parent.parent
    )

    service_path = (
        project_root
        / "services"
        / "research_radar_service.py"
    )

    source = service_path.read_text(
        encoding="utf-8"
    )

    # ------------------------------------------
    # GRANULAR FUNDAMENTAL CONTRACT
    #
    # These already-calculated dimensions must
    # survive the Research Radar output boundary
    # so downstream portfolio sizing can consume
    # direct investment factors rather than only
    # composites-of-composites.
    # ------------------------------------------

    required_fundamental_contract = {
        '"profitability_score":':
            'fundamental_scores.get(\n'
            '                        "profitability_score"',
        '"growth_score":':
            'fundamental_scores.get(\n'
            '                        "growth_score"',
        '"financial_strength_score":':
            'fundamental_scores.get(\n'
            '                        "financial_strength_score"',
        '"valuation_score":':
            'fundamental_scores.get(\n'
            '                        "valuation_score"',
    }

    for (
        output_field,
        source_expression,
    ) in required_fundamental_contract.items():

        assert output_field in source, (
            f"Missing output field: "
            f"{output_field}"
        )

        assert source_expression in source, (
            f"Incorrect source mapping for "
            f"{output_field}"
        )

        print(
            output_field,
            "=> fundamental score contract: PASS",
        )

    # ------------------------------------------
    # RISK CONTRACT
    #
    # Risk resilience comes directly from the
    # technical scoring engine. Higher risk_score
    # represents better technical risk resilience,
    # not greater raw risk.
    # ------------------------------------------

    assert '"risk_score":' in source

    assert (
        'technical_scores.get(\n'
        '                        "risk_score"'
        in source
    )

    print(
        '"risk_score":',
        "=> technical risk contract: PASS",
    )

    # ------------------------------------------
    # EXISTING AGGREGATE CONTRACT PRESERVED
    # ------------------------------------------

    required_existing_fields = (
        '"fundamental_score":',
        '"technical_score":',
        '"composite_score":',
        '"readiness_score":',
    )

    for field in required_existing_fields:

        assert field in source, (
            f"Existing score contract lost: "
            f"{field}"
        )

    print(
        "Existing aggregate score contract: PASS"
    )

    print()
    print(
        "Sprint 11.5B.2A Research Radar "
        "score-contract regression: PASS"
    )


if __name__ == "__main__":
    run_tests()
