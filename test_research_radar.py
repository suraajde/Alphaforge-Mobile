from services.research_radar_service import (
    build_research_radar,
)


symbols = [
    "INFY",
    "CASTROLIND",
    "BSE",
    "TCS",
    "RELIANCE",
    "HDFCBANK",
    "BAJFINANCE",
]


result = build_research_radar(
    symbols,
    limit=30,
)


print()
print("=" * 110)
print(
    "ALPHAFORGE RESEARCH RADAR - ELIGIBLE POOL"
)
print("=" * 110)

print(
    f"Analyzed   : "
    f"{result['analyzed_count']}"
)

print(
    f"Successful : "
    f"{result['successful_count']}"
)

print(
    f"Eligible   : "
    f"{result['eligible_count']}"
)

print(
    f"Review     : "
    f"{result['review_count']}"
)

print()


for stock in result["ranked"]:

    print(
        f"#{stock['rank']:02d} "
        f"{stock['symbol']:12} | "
        f"{stock['scoring_profile']:18} | "
        f"Composite: "
        f"{stock['composite_score']:5.1f} | "
        f"Fund: "
        f"{stock['fundamental_score']:5.1f} | "
        f"Tech: "
        f"{stock['technical_score']:5.1f} | "
        f"Ready: "
        f"{stock['readiness_score']:5.1f} | "
        f"{stock['classification']}"
    )


print()
print("=" * 110)
print(
    "REVIEW / PROVISIONAL POOL"
)
print("=" * 110)


for stock in result["review"]:

    print(
        f"{stock['symbol']:12} | "
        f"{stock['scoring_profile']:18} | "
        f"{stock['profile_maturity']:12} | "
        f"Composite: "
        f"{stock['composite_score']:5.1f} | "
        f"{stock['classification']} | "
        f"{stock['ranking_notes']}"
    )


if result["errors"]:

    print()
    print("=" * 110)
    print("ERRORS")
    print("=" * 110)

    for item in result["errors"]:

        print(
            item.get("symbol"),
            ":",
            item.get("error"),
        )