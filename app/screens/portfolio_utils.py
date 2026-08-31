"""
Portfolio utility helpers.

These functions are intentionally stateless so they can be reused
by Portfolio, Analytics, Health and future screens.
"""


def safe_float(value):

    try:
        return float(value)

    except (TypeError, ValueError):
        return 0.0


def money(value):

    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0

    return f"Rs. {value:,.2f}"


def number(value):

    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0

    return f"{value:,.2f}"