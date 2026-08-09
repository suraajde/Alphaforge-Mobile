"""Centralized UI Status Color System for AlphaForge (Sprint 14.1.1)

Provides a single, authoritative color palette and status mapping utility across
all primary screens (Portfolio, Portfolio Health, Action Center, Watchtower, Research Radar, Settings).

Color Principles (Requirement 18):
- GREEN: Positive / healthy / approved / low risk / strong
- AMBER: Warning / watch / review / medium risk / moderate
- RED: Negative / critical risk / breach / poor / high risk
- BLUE: Informational / neutral metric
- GREY: N/A / unavailable / no data / disabled / inactive
"""
from __future__ import annotations

from typing import Optional


class UIColors:
    """Authoritative AlphaForge UI Color Tokens."""

    # Primary Palette
    GREEN = "#16a34a"       # Positive / healthy / approved / low risk
    GREEN_LIGHT = "#dcfce7" # Light green container background
    GREEN_TEXT = "#15803d"  # Darker green text

    AMBER = "#d97706"       # Warning / watch / review / medium risk
    AMBER_LIGHT = "#fef3c7" # Light amber container background
    AMBER_TEXT = "#b45309"  # Darker amber text

    ORANGE = "#ea580c"      # Secondary warning / elevated risk
    ORANGE_TEXT = "#c2410c"

    RED = "#dc2626"         # Negative / critical risk / breach / poor
    RED_LIGHT = "#fee2e2"   # Light red container background
    RED_TEXT = "#b91c1c"    # Darker red text

    BLUE = "#2563eb"        # Informational / neutral metric / primary accent
    BLUE_LIGHT = "#dbeafe"  # Light blue container background
    BLUE_TEXT = "#1d4ed8"   # Darker blue text

    SKY = "#0284c7"         # Secondary accent / header highlight
    SKY_LIGHT = "#e0f2fe"

    GREY = "#64748b"        # N/A / unavailable / no data / disabled
    GREY_LIGHT = "#f1f5f9"  # Light grey background
    MUTED_TEXT = "#94a3b8"  # Secondary label text

    DARK_BG = "#0f172a"     # Card dark background
    DARK_CARD = "#1e293b"   # Secondary dark container
    CARD_BORDER = "#334155" # Card border line


def get_status_color(status_text: Optional[str]) -> str:
    """Return appropriate hex color for a general status string."""
    if not status_text:
        return UIColors.GREY

    txt = str(status_text).strip().upper()
    if txt in ("APPROVED", "OK", "HEALTHY", "REBALANCE APPROVED", "STABLE", "ACTIVE", "STRONG", "LOW_RISK", "LOW"):
        return UIColors.GREEN
    if txt in ("REVIEW", "WATCH", "WARNING", "MODERATE", "MEDIUM", "CONDITIONAL", "ELEVATED"):
        return UIColors.AMBER
    if txt in ("CRITICAL", "HIGH", "BREACH", "POOR", "DETERIORATING", "HIGH_RISK", "REDUCE"):
        return UIColors.RED
    if txt in ("INFO", "INFORMATIONAL", "NEUTRAL", "HOLD"):
        return UIColors.BLUE
    if "NO ACTIVE PORTFOLIO" in txt or txt in ("N/A", "UNAVAILABLE", "NO_DATA", "DISABLED", "NONE"):
        return UIColors.GREY

    return UIColors.BLUE


def get_grade_color(grade: Optional[str]) -> str:
    """Return color for portfolio health investment grade (A, B, C, D, F, N/A)."""
    if not grade:
        return UIColors.GREY

    g = str(grade).strip().upper()
    if g == "A":
        return UIColors.GREEN
    if g == "B":
        return UIColors.BLUE
    if g == "C":
        return UIColors.AMBER
    if g in ("D", "F"):
        return UIColors.RED

    return UIColors.GREY


def get_risk_color(risk_level: Optional[str]) -> str:
    """Return color for risk ratings (LOW, MEDIUM, HIGH, CRITICAL, N/A)."""
    if not risk_level:
        return UIColors.GREY

    r = str(risk_level).strip().upper()
    if r == "LOW":
        return UIColors.GREEN
    if r in ("MEDIUM", "MODERATE"):
        return UIColors.AMBER
    if r in ("HIGH", "CRITICAL", "ELEVATED"):
        return UIColors.RED

    return UIColors.GREY


def get_recommendation_color(recommendation: Optional[str]) -> str:
    """Return color for Action Center recommendation types (BUY, ADD, REDUCE, HOLD, WATCH, REVIEW)."""
    if not recommendation:
        return UIColors.GREY

    rec = str(recommendation).strip().upper()
    if rec in ("BUY", "ADD", "REBALANCE APPROVED"):
        return UIColors.GREEN
    if rec in ("WATCH", "REVIEW"):
        return UIColors.AMBER
    if rec in ("REDUCE", "SELL"):
        return UIColors.RED
    if rec in ("HOLD", "MAINTAIN"):
        return UIColors.BLUE

    return UIColors.GREY
