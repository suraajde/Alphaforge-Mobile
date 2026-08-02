from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
from typing import Optional

from services.portfolio_state_service import PortfolioStateService


class PortfolioAdministrationService:
    """Portfolio Administration Service providing summary metrics and backup functionality."""

    def __init__(self, state_service: Optional[PortfolioStateService] = None) -> None:
        self.state_service = state_service or PortfolioStateService()

    def get_administration_summary(self, path: Optional[str | Path] = None) -> dict:
        """Load portfolio state and return key administrative metrics."""
        load_res = self.state_service.load_state(path=path)
        if load_res.get("status") != "OK" or not load_res.get("state"):
            return {"status": "NOT_FOUND"}

        state = load_res["state"]
        positions = state.get("positions", {})
        holdings_count = len(positions) if isinstance(positions, dict) else 0
        transaction_count = state.get("transaction_count", 0)
        snapshots = state.get("snapshots", [])
        snapshot_count = len(snapshots) if isinstance(snapshots, list) else 0

        cash_balance = state.get("cash_balance", 0.0)
        invested_market_value = state.get("invested_market_value", 0.0)
        total_portfolio_value = state.get("total_portfolio_value", 0.0)
        last_updated = state.get("updated_at")

        return {
            "status": "OK",
            "holdings_count": holdings_count,
            "transaction_count": transaction_count,
            "snapshot_count": snapshot_count,
            "cash_balance": cash_balance,
            "invested_market_value": invested_market_value,
            "total_portfolio_value": total_portfolio_value,
            "last_updated": last_updated,
        }

    def create_backup(
        self,
        path: Optional[str | Path] = None,
        backup_dir: Optional[str | Path] = None,
    ) -> dict:
        """Create a timestamped backup copy of the portfolio state JSON file."""
        source_path = Path(path) if path is not None else self.state_service.DEFAULT_STATE_PATH
        if not source_path.exists():
            return {"status": "NOT_FOUND"}

        if backup_dir is not None:
            target_dir = Path(backup_dir)
        else:
            target_dir = source_path.parent.parent / "backups"

        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = target_dir / f"portfolio_backup_{timestamp}.json"

        shutil.copy2(source_path, backup_file)

        return {
            "status": "OK",
            "backup_path": str(backup_file),
        }

    def restore_backup(self, *args, **kwargs):
        """Restore portfolio state from backup (Sprint 13.2.1C)."""
        raise NotImplementedError(
            "Backup restore will be implemented in Sprint 13.2.1C"
        )

    def reset_portfolio_holdings(self, *args, **kwargs):
        """Reset portfolio holdings state (Sprint 13.2.1C)."""
        raise NotImplementedError(
            "Portfolio reset will be implemented in Sprint 13.2.1C"
        )
