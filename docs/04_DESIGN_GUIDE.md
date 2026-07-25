# AlphaForge Design Guide

---

# Design Philosophy

AlphaForge is a professional desktop investment platform.

The interface should be:

- Clean
- Fast
- Modern
- Consistent
- Information-rich
- Easy to scan

Users should understand portfolio health within seconds.

---

# Design Principles

- Consistency over decoration
- Colour indicates meaning
- Icons reinforce meaning
- Data before graphics
- Minimal visual clutter
- Desktop-first experience

---

# Unified Status Framework

| Status | Meaning | Usage |
|---------|---------|-------|
| 🔴 Critical | Immediate attention required | Action required |
| 🟠 High | Strong recommendation | Review soon |
| 🟡 Monitor | Observation required | Watch closely |
| 🟢 Healthy | Normal | No action |
| 🔵 Information | Informational | Awareness |
| ⚪ Neutral | No status | Default |

This status framework is shared across every module.

---

# Colour Rules

Colours must never be hard-coded.

All colours must originate from the Theme Framework.

Business logic must never reference colours directly.

---

# Typography

Primary Font

Segoe UI

Fallback

Arial

Future

Inter

---

# Desktop Layout

Header

Navigation

Content

Status Bar

---

# Dashboard

The dashboard should answer:

- How is my portfolio?
- What needs attention?
- What opportunities exist?
- What changed today?

---

# Research Radar

Cards should display

- Rank
- Score
- Quality
- Growth
- Valuation
- Status Badge

---

# Portfolio Screen

Each holding should display

- Allocation
- Gain/Loss
- Conviction
- Health
- Status
- Watchtower Alerts

---

# Watchtower

Every alert must include

- Priority
- Colour
- Icon
- Explanation
- Recommended Action

---

# Theme Framework

Future implementation

core/theme/

- colors.py
- status.py
- icons.py
- typography.py
- spacing.py
- palette.py

---

# Accessibility

Never depend on colour alone.

Every status must include

- Colour
- Icon
- Text

---

Last Updated

Sprint 12.0.0
