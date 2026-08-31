from services.technical_service import (
    get_technical_metrics,
)


for symbol in [
    "INFY",
    "CASTROLIND",
    "BSE",
]:

    print()
    print("=" * 60)
    print(
        f"TECHNICAL TEST: {symbol}"
    )
    print("=" * 60)

    data = get_technical_metrics(
        symbol
    )

    for key, value in data.items():

        print(
            f"{key:25} : {value}"
        )