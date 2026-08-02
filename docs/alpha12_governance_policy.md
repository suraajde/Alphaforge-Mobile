# Alpha 12 Governance & Rebalance Policy

## 1. Investment Philosophy & Core Principles

Alpha 12 is engineered as a **long-term wealth-compounding investment portfolio**, not a high-frequency trading strategy. The core governance mandate is to **minimize unnecessary portfolio churn**, ensuring position replacements are rare, deliberate, and backed by strong empirical score and conviction advantage.

* **Core Principle**: Do not churn positions for minor, transient score fluctuations, but do not retain clearly inferior or thesis-broken holdings.

---

## 2. Monthly Review Cycle

* **Review Frequency**: **Monthly**
* **Rebalance Frequency**: **Conditional (Optional)**
* **Default Outcome**: **NO ACTION**

Rebalancing is **never mandatory** during a monthly review cycle. If all current holdings meet conviction standards and candidate stocks do not offer a substantial advantage clearing incumbent friction buffers, the default monthly outcome is **NO ACTION**.

---

## 3. Governance Limits & Parameters

| Parameter | Default Value | Description |
| :--- | :--- | :--- |
| **Max Replacements per Review** | `3` | Maximum approved position replacements per monthly review cycle. |
| **Max Turnover Limit** | `20.0%` | Maximum portfolio turnover budget per monthly review cycle. |
| **Minimum Score Advantage** | `10.0 pts` | Candidate score must exceed effective holding score by >= 10.0 points. |
| **Incumbent Protection Bonus** | `3.0 pts` | Friction protection added to incumbent holding score for trading costs/taxes. |
| **Conviction Buffer** | `5.0 pts` | Candidate conviction must exceed incumbent conviction by >= 5.0 points. |
| **Cooling Period** | `30 days` | Holding duration required before non-emergency replacement is permitted. |

---

## 4. Decision Categories

1. **`ADD`**: Capacity expansion action executed when the portfolio is below target size (`target_portfolio_size = 12`).
2. **`HOLD`**: Retains existing position because candidate advantage is below churn threshold. Does not consume turnover.
3. **`REVIEW`**: Flags position for manual human review due to active cooling period or guardrail warnings. Must never auto-execute.
4. **`REPLACE`**: Replaces an inferior holding with a top-ranked candidate stock after clearing score, conviction, cooling, and turnover thresholds.
5. **`NO_ACTION`**: Informational default outcome when portfolio is aligned and no rebalance is required.

---

## 5. Emergency Review & Override Process

In exceptional circumstances where an incumbent company's fundamental investment thesis is broken (e.g. severe accounting fraud, corporate governance failure, structural bankruptcy risk):

* **Emergency Review**: Enabled and active at all times.
* **Emergency Replacement**: Triggered via `CRITICAL` priority decision or explicit emergency override flag.
* **Override Authority**: Emergency replacements bypass standard monthly replacement limits (`max_replacements_per_cycle = 3`) and cooling period restrictions when `emergency_override_enabled = True`.
* **Audit Trail**: Every emergency replacement generates a high-priority audit record documenting the broken thesis rationale.
