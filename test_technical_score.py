from services.technical_service import (
    get_technical_metrics,
)

from services.technical_score_service import (
    calculate_technical_score,
)


for symbol in [
    "INFY",
    "CASTROLIND",
    "BSE",
]:

    print()
    print("=" * 60)

    print(
        f"TECHNICAL SCORE TEST: {symbol}"
    )

    print("=" * 60)

    data = get_technical_metrics(
        symbol
    )

    scores = calculate_technical_score(
        data
    )

    for key, value in scores.items():

        print(
            f"{key:25} : {value}"
        )