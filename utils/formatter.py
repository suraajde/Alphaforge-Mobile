def format_price(price):
    """
    Format stock price.
    Example:
    1328.5 -> Rs.  1,328.50
    """

    if isinstance(price, (int, float)):
        return f"Rs.  {price:,.2f}"

    return "N/A"


def format_percentage(value, multiply=False):
    """
    Format percentage values.

    multiply=True is used for ratios like ROE returned as 0.135
    """

    if not isinstance(value, (int, float)):
        return "N/A"

    if multiply:
        value *= 100

    return f"{value:.2f} %"


def format_number(value):

    if isinstance(value, (int, float)):
        return f"{value:,.2f}"

    return "N/A"


def format_market_cap(value):
    """
    Convert market cap into Indian units.

    Example:
    4130000000000
    ->
    Rs.  4.13 Lakh Cr
    """

    if not isinstance(value, (int, float)):
        return "N/A"

    lakh_crore = value / 1e12

    if lakh_crore >= 1:
        return f"Rs.  {lakh_crore:.2f} Lakh Cr"

    crore = value / 1e7

    if crore >= 1:
        return f"Rs.  {crore:,.2f} Cr"

    return f"Rs.  {value:,.0f}"