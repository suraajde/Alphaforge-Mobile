from services.fundamental_service import (
    get_fundamental_metrics,
)

from services.fundamental_score_service import (
    calculate_fundamental_score,
)

from services.data_quality_service import (
    calculate_data_quality,
)

from services.technical_service import (
    get_technical_metrics,
)

from services.technical_score_service import (
    calculate_technical_score,
)

from services.alpha_composite_service import (
    calculate_alpha_composite,
)


symbols = [
    "INFY",
    "CASTROLIND",
    "BSE",
]


for symbol in symbols:

    print()
    print("=" * 70)
    print(
        f"ALPHA COMPOSITE PROTOTYPE: {symbol}"
    )
    print("=" * 70)

    fundamental_data = (
        get_fundamental_metrics(
            symbol
        )
    )

    fundamental_scores = (
        calculate_fundamental_score(
            fundamental_data
        )
    )

    data_quality = (
        calculate_data_quality(
            fundamental_data
        )
    )

    technical_data = (
        get_technical_metrics(
            symbol
        )
    )

    technical_scores = (
        calculate_technical_score(
            technical_data
        )
    )

    result = (
        calculate_alpha_composite(
            fundamental_scores,
            technical_scores,
            data_quality,
        )
    )

    for key, value in result.items():

        print(
            f"{key:25} : {value}"
        )